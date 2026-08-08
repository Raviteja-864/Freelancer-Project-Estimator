from flask import Blueprint
from controllers.auth_controller import AuthController

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

auth_bp.route("/register", methods=["POST"])(AuthController.register)
auth_bp.route("/login", methods=["POST"])(AuthController.login)
auth_bp.route("/logout", methods=["POST"])(AuthController.logout)
auth_bp.route("/refresh", methods=["POST"])(AuthController.refresh)
auth_bp.route("/me", methods=["GET"])(AuthController.get_current_user)
