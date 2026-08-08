from extensions import db
from models import Payment


class PaymentService:

    @staticmethod
    def get_by_project(project_id):
        return Payment.query.filter_by(project_id=project_id).first()

    @staticmethod
    def get_by_id(payment_id):
        return Payment.query.get(payment_id)

    @staticmethod
    def update_status(payment, new_status):
        payment.status = new_status
        db.session.commit()
        return payment
