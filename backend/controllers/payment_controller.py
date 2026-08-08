from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from services.payment_service import PaymentService
from services.project_service import ProjectService
from models import PaymentStatusEnum
from utils.responses import success_response, error_response
from utils.validators import validate_required_fields, is_valid_payment_status


class PaymentController:

    # ---------------------------------------------------------------
    # VIEW PAYMENT FOR A PROJECT
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def get_project_payment(project_id):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        project = ProjectService.get_by_id(project_id)
        if not project:
            return error_response("Project not found", 404)

        is_client = project.client_id == user_id
        is_freelancer = project.accepted_bid and project.accepted_bid.freelancer_id == user_id
        if role != "admin" and not is_client and not is_freelancer:
            return error_response("You do not have permission to view this payment", 403)

        payment = PaymentService.get_by_project(project_id)
        if not payment:
            return error_response("No payment record exists yet for this project", 404)

        return success_response("Payment fetched", data={"payment": payment.to_dict()})

    # ---------------------------------------------------------------
    # UPDATE PAYMENT STATUS (client owner or admin)
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def update_payment_status(payment_id):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        payment = PaymentService.get_by_id(payment_id)
        if not payment:
            return error_response("Payment not found", 404)

        project = payment.project
        if role != "admin" and (role != "client" or project.client_id != user_id):
            return error_response("You do not have permission to update this payment", 403)

        data = request.get_json(silent=True) or {}
        missing = validate_required_fields(data, ["status"])
        if missing:
            return error_response("Missing required fields", 422, errors={"missing_fields": missing})

        new_status_raw = str(data["status"]).strip().lower()
        if not is_valid_payment_status(new_status_raw):
            return error_response("status must be one of: pending, paid, cancelled", 422)

        # Once marked paid, only an admin can change it further (prevents accidental reversal)
        if payment.status == PaymentStatusEnum.PAID and role != "admin":
            return error_response("A paid payment can only be modified by an admin", 409)

        payment = PaymentService.update_status(payment, PaymentStatusEnum(new_status_raw))
        return success_response("Payment status updated", data={"payment": payment.to_dict()})
