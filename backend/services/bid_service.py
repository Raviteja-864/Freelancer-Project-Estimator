from extensions import db
from models import Bid, BidStatusEnum, Project, ProjectStatusEnum, Payment, PaymentStatusEnum


class BidService:

    @staticmethod
    def get_by_id(bid_id):
        return Bid.query.get(bid_id)

    @staticmethod
    def get_existing_bid(project_id, freelancer_id):
        return Bid.query.filter_by(project_id=project_id, freelancer_id=freelancer_id).first()

    @staticmethod
    def create_bid(freelancer_id, project_id, data):
        bid = Bid(
            project_id=project_id,
            freelancer_id=freelancer_id,
            price=data["price"],
            proposal=data["proposal"].strip(),
            estimated_days=data["estimated_days"],
            status=BidStatusEnum.PENDING,
        )
        db.session.add(bid)
        db.session.commit()
        return bid

    @staticmethod
    def list_by_freelancer(freelancer_id, status=None, page=1, per_page=20):
        query = Bid.query.filter_by(freelancer_id=freelancer_id)
        if status:
            query = query.filter_by(status=BidStatusEnum(status))
        query = query.order_by(Bid.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def list_by_project(project_id):
        return Bid.query.filter_by(project_id=project_id).order_by(Bid.created_at.desc()).all()

    @staticmethod
    def update_bid(bid, data):
        editable_fields = ["price", "proposal", "estimated_days"]
        for field in editable_fields:
            if field in data:
                value = data[field]
                if field == "proposal" and isinstance(value, str):
                    value = value.strip()
                setattr(bid, field, value)
        db.session.commit()
        return bid

    @staticmethod
    def withdraw_bid(bid):
        bid.status = BidStatusEnum.WITHDRAWN
        db.session.commit()
        return bid

    @staticmethod
    def reject_bid(bid):
        bid.status = BidStatusEnum.REJECTED
        db.session.commit()
        return bid

    @staticmethod
    def accept_bid(bid, project):
        """Accepts one bid, rejects all other pending bids on the same project,
        moves the project to in_progress, and creates its payment record."""
        bid.status = BidStatusEnum.ACCEPTED
        project.status = ProjectStatusEnum.IN_PROGRESS
        project.accepted_bid_id = bid.id

        other_pending = Bid.query.filter(
            Bid.project_id == project.id,
            Bid.id != bid.id,
            Bid.status == BidStatusEnum.PENDING,
        ).all()
        for other in other_pending:
            other.status = BidStatusEnum.REJECTED

        payment = Payment(project_id=project.id, amount=bid.price, status=PaymentStatusEnum.PENDING)
        db.session.add(payment)

        db.session.commit()
        return bid, project, payment

    @staticmethod
    def get_accepted_projects_for_freelancer(freelancer_id, page=1, per_page=20):
        query = (
            Project.query.join(Bid, Project.accepted_bid_id == Bid.id)
            .filter(Bid.freelancer_id == freelancer_id)
            .order_by(Project.updated_at.desc())
        )
        return query.paginate(page=page, per_page=per_page, error_out=False)
