from flask import Blueprint
from controllers.admin_controller import AdminController

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

admin_bp.route("/dashboard", methods=["GET"])(AdminController.dashboard)

admin_bp.route("/users", methods=["GET"])(AdminController.list_users)
admin_bp.route("/users/<int:user_id>/status", methods=["PATCH"])(AdminController.update_user_status)
admin_bp.route("/users/<int:user_id>", methods=["DELETE"])(AdminController.delete_user)

admin_bp.route("/projects", methods=["GET"])(AdminController.list_all_projects)
admin_bp.route("/projects/<int:project_id>", methods=["DELETE"])(AdminController.delete_project)

admin_bp.route("/bids", methods=["GET"])(AdminController.list_all_bids)
admin_bp.route("/bids/<int:bid_id>", methods=["DELETE"])(AdminController.delete_bid)
