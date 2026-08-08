from flask import Blueprint
from controllers.message_controller import MessageController

message_bp = Blueprint("message", __name__, url_prefix="/api/messages")

message_bp.route("", methods=["POST"])(MessageController.send_message)
message_bp.route("/unread-count", methods=["GET"])(MessageController.get_unread_count)
message_bp.route("/project/<int:project_id>", methods=["GET"])(MessageController.get_conversation)
