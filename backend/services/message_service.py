from extensions import db
from models import Message, Project


class MessageService:

    @staticmethod
    def get_participant_ids(project):
        """Returns (client_id, freelancer_id) for a project, or (client_id, None)
        if no freelancer has been accepted yet."""
        freelancer_id = project.accepted_bid.freelancer_id if project.accepted_bid else None
        return project.client_id, freelancer_id

    @staticmethod
    def is_participant(project, user_id):
        client_id, freelancer_id = MessageService.get_participant_ids(project)
        return user_id == client_id or (freelancer_id is not None and user_id == freelancer_id)

    @staticmethod
    def chat_unlocked(project):
        """Chat is only available once a freelancer has been accepted on the project."""
        return project.accepted_bid_id is not None

    @staticmethod
    def send_message(project, sender_id, content):
        client_id, freelancer_id = MessageService.get_participant_ids(project)
        receiver_id = freelancer_id if sender_id == client_id else client_id

        message = Message(
            project_id=project.id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content.strip(),
        )
        db.session.add(message)
        db.session.commit()
        return message

    @staticmethod
    def get_conversation(project_id, reader_id):
        messages = (
            Message.query.filter_by(project_id=project_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        unread = [m for m in messages if m.receiver_id == reader_id and not m.is_read]
        for m in unread:
            m.is_read = True
        if unread:
            db.session.commit()
        return messages

    @staticmethod
    def get_unread_count(user_id):
        return Message.query.filter_by(receiver_id=user_id, is_read=False).count()
