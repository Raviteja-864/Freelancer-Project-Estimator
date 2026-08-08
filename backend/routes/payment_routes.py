from flask import Blueprint
from controllers.payment_controller import PaymentController

payment_bp = Blueprint("payment", __name__, url_prefix="/api/payments")

payment_bp.route("/project/<int:project_id>", methods=["GET"])(PaymentController.get_project_payment)
payment_bp.route("/<int:payment_id>/status", methods=["PATCH"])(PaymentController.update_payment_status)
