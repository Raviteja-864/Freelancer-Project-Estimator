from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from services.message_service import MessageService
from services.project_service import ProjectService
from utils.responses import success_response, error_response
from utils.validators import validate_required_fields


class MessageController:

    # ---------------------------------------------------------------
    # SEND MESSAGE
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def send_message():
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")
        if role not in ("client", "freelancer"):
            return error_response("Only clients and freelancers can send messages", 403)

        data = request.get_json(silent=True) or {}
        missing = validate_required_fields(data, ["project_id", "content"])
        if missing:
            return error_response("Missing required fields", 422, errors={"missing_fields": missing})

        project = ProjectService.get_by_id(data["project_id"])
        if not project:
            return error_response("Project not found", 404)

        if not MessageService.chat_unlocked(project):
            return error_response("Chat unlocks once a freelancer has been accepted for this project", 409)
        if not MessageService.is_participant(project, user_id):
            return error_response("You are not a participant in this project's chat", 403)

        content = str(data["content"]).strip()
        if not content:
            return error_response("Message content cannot be empty", 422)
        if len(content) > 5000:
            return error_response("Message is too long (max 5000 characters)", 422)

        message = MessageService.send_message(project, user_id, content)
        return success_response("Message sent", data={"message": message.to_dict()}, status_code=201)

    # ---------------------------------------------------------------
    # CONVERSATION HISTORY
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def get_conversation(project_id):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        project = ProjectService.get_by_id(project_id)
        if not project:
            return error_response("Project not found", 404)

        if role != "admin" and not MessageService.is_participant(project, user_id):
            return error_response("You are not a participant in this project's chat", 403)

        messages = MessageService.get_conversation(project_id, user_id)
        return success_response("Conversation fetched", data={"messages": [m.to_dict() for m in messages]})

    # ---------------------------------------------------------------
    # UNREAD COUNT
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def get_unread_count():
        user_id = int(get_jwt_identity())
        count = MessageService.get_unread_count(user_id)
        return success_response("Unread count fetched", data={"unread_count": count})
