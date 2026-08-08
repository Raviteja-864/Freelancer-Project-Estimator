from flask import Blueprint
from controllers.project_controller import ProjectController

project_bp = Blueprint("project", __name__, url_prefix="/api/projects")

project_bp.route("", methods=["POST"])(ProjectController.create_project)
project_bp.route("", methods=["GET"])(ProjectController.list_projects)
project_bp.route("/mine", methods=["GET"])(ProjectController.list_my_projects)
project_bp.route("/<int:project_id>", methods=["GET"])(ProjectController.get_project)
project_bp.route("/<int:project_id>", methods=["PUT"])(ProjectController.update_project)
project_bp.route("/<int:project_id>", methods=["DELETE"])(ProjectController.delete_project)
project_bp.route("/<int:project_id>/status", methods=["PATCH"])(ProjectController.update_status)
