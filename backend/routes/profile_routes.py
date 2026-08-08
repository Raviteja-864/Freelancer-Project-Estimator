from flask import Blueprint
from controllers.profile_controller import ProfileController

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")

profile_bp.route("/me", methods=["GET"])(ProfileController.get_my_profile)
profile_bp.route("/me", methods=["PUT"])(ProfileController.update_my_profile)
profile_bp.route("/skills", methods=["POST"])(ProfileController.add_skill)
profile_bp.route("/skills/<int:skill_id>", methods=["DELETE"])(ProfileController.remove_skill)
profile_bp.route("/portfolio", methods=["POST"])(ProfileController.add_portfolio_link)
profile_bp.route("/portfolio/<int:link_id>", methods=["DELETE"])(ProfileController.remove_portfolio_link)
profile_bp.route("/<int:user_id>", methods=["GET"])(ProfileController.get_public_profile)
