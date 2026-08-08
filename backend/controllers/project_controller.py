from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from services.project_service import ProjectService
from models import ProjectStatusEnum
from utils.responses import success_response, error_response
from utils.validators import (
    validate_required_fields,
    is_non_negative_number,
    is_valid_date,
    is_valid_project_status,
)
from utils.decorators import role_required


class ProjectController:

    # ---------------------------------------------------------------
    # CREATE (client only)
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("client")
    def create_project():
        client_id = get_jwt_identity()
        data = request.get_json(silent=True) or {}

        missing = validate_required_fields(data, ["title", "description"])
        if missing:
            return error_response("Missing required fields", 422, errors={"missing_fields": missing})

        title = data["title"].strip()
        description = data["description"].strip()

        if len(title) < 5 or len(title) > 200:
            return error_response("Title must be between 5 and 200 characters", 422)
        if len(description) < 20:
            return error_response("Description must be at least 20 characters", 422)

        budget_min = data.get("budget_min")
        budget_max = data.get("budget_max")
        if budget_min is not None and not is_non_negative_number(budget_min):
            return error_response("budget_min must be a non-negative number", 422)
        if budget_max is not None and not is_non_negative_number(budget_max):
            return error_response("budget_max must be a non-negative number", 422)
        if budget_min is not None and budget_max is not None and float(budget_min) > float(budget_max):
            return error_response("budget_min cannot be greater than budget_max", 422)

        deadline = None
        if data.get("deadline"):
            deadline = is_valid_date(data["deadline"])
            if not deadline:
                return error_response("deadline must be in YYYY-MM-DD format", 422)

        clean_data = {
            "title": title,
            "description": description,
            "category": data.get("category"),
            "budget_min": budget_min,
            "budget_max": budget_max,
            "deadline": deadline,
        }

        project = ProjectService.create_project(client_id, clean_data)
        return success_response("Project created", data={"project": project.to_dict()}, status_code=201)

    # ---------------------------------------------------------------
    # LIST / SEARCH / FILTER
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def list_projects():
        role = get_jwt().get("role")
        args = request.args

        status = args.get("status")
        if status and not is_valid_project_status(status):
            return error_response("Invalid status filter", 422)

        try:
            page = max(int(args.get("page", 1)), 1)
            per_page = min(max(int(args.get("per_page", 20)), 1), 100)
        except ValueError:
            return error_response("page and per_page must be integers", 422)

        budget_min = args.get("budget_min")
        budget_max = args.get("budget_max")
        if budget_min is not None and budget_min != "" and not is_non_negative_number(budget_min):
            return error_response("budget_min filter must be a non-negative number", 422)
        if budget_max is not None and budget_max != "" and not is_non_negative_number(budget_max):
            return error_response("budget_max filter must be a non-negative number", 422)

        sort = args.get("sort", "newest")
        if sort not in ("newest", "budget_desc", "bids_asc"):
            return error_response("sort must be one of: newest, budget_desc, bids_asc", 422)

        filters = {
            "status": status,
            "category": args.get("category"),
            "keyword": args.get("keyword"),
            "budget_min": float(budget_min) if budget_min else None,
            "budget_max": float(budget_max) if budget_max else None,
            "sort": sort,
            # Freelancers browsing the marketplace default to open projects only
            "default_open_only": role == "freelancer" and not status,
        }

        pagination = ProjectService.list_projects(filters, page=page, per_page=per_page)
        return success_response(
            "Projects fetched",
            data={
                "projects": [p.to_dict() for p in pagination.items],
                "pagination": {
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "total_pages": pagination.pages,
                },
            },
        )

    # ---------------------------------------------------------------
    # CLIENT'S OWN PROJECTS
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("client")
    def list_my_projects():
        client_id = get_jwt_identity()
        args = request.args
        status = args.get("status")
        if status and not is_valid_project_status(status):
            return error_response("Invalid status filter", 422)

        try:
            page = max(int(args.get("page", 1)), 1)
            per_page = min(max(int(args.get("per_page", 20)), 1), 100)
        except ValueError:
            return error_response("page and per_page must be integers", 422)

        filters = {"client_id": client_id, "status": status}
        pagination = ProjectService.list_projects(filters, page=page, per_page=per_page)
        return success_response(
            "Your projects fetched",
            data={
                "projects": [p.to_dict() for p in pagination.items],
                "pagination": {
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "total_pages": pagination.pages,
                },
            },
        )

    # ---------------------------------------------------------------
    # DETAIL
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def get_project(project_id):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        project = ProjectService.get_by_id(project_id)
        if not project:
            return error_response("Project not found", 404)

        is_owner = project.client_id == user_id
        include_bids = is_owner or role == "admin"

        return success_response("Project fetched", data={"project": project.to_dict(include_bids=include_bids)})

    # ---------------------------------------------------------------
    # UPDATE (owner only)
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("client")
    def update_project(project_id):
        client_id = int(get_jwt_identity())
        project = ProjectService.get_by_id(project_id)
        if not project:
            return error_response("Project not found", 404)
        if project.client_id != client_id:
            return error_response("You do not have permission to edit this project", 403)
        if project.status != ProjectStatusEnum.OPEN:
            return error_response("Only open projects can be edited", 409)

        data = request.get_json(silent=True) or {}
        if not data:
            return error_response("No fields provided to update", 422)

        if "title" in data:
            title = str(data["title"]).strip()
            if len(title) < 5 or len(title) > 200:
                return error_response("Title must be between 5 and 200 characters", 422)
            data["title"] = title

        if "description" in data:
            description = str(data["description"]).strip()
            if len(description) < 20:
                return error_response("Description must be at least 20 characters", 422)
            data["description"] = description

        if "budget_min" in data and data["budget_min"] is not None and not is_non_negative_number(data["budget_min"]):
            return error_response("budget_min must be a non-negative number", 422)
        if "budget_max" in data and data["budget_max"] is not None and not is_non_negative_number(data["budget_max"]):
            return error_response("budget_max must be a non-negative number", 422)

        if "deadline" in data and data["deadline"]:
            parsed = is_valid_date(data["deadline"])
            if not parsed:
                return error_response("deadline must be in YYYY-MM-DD format", 422)
            data["deadline"] = parsed

        project = ProjectService.update_project(project, data)
        return success_response("Project updated", data={"project": project.to_dict()})

    # ---------------------------------------------------------------
    # DELETE (owner only)
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("client")
    def delete_project(project_id):
        client_id = int(get_jwt_identity())
        project = ProjectService.get_by_id(project_id)
        if not project:
            return error_response("Project not found", 404)
        if project.client_id != client_id:
            return error_response("You do not have permission to delete this project", 403)
        if project.status != ProjectStatusEnum.OPEN:
            return error_response("Only open projects with no accepted freelancer can be deleted", 409)
        if len(project.bids) > 0:
            return error_response(
                "Project has existing bids — cancel it instead of deleting", 409
            )

        ProjectService.delete_project(project)
        return success_response("Project deleted")

    # ---------------------------------------------------------------
    # STATUS TRANSITIONS (track status / mark completed / cancel)
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("client", "freelancer")
    def update_status(project_id):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")
        project = ProjectService.get_by_id(project_id)
        if not project:
            return error_response("Project not found", 404)

        if role == "client":
            if project.client_id != user_id:
                return error_response("You do not have permission to update this project", 403)
        else:
            # Freelancers may only cancel a project they were accepted on.
            accepted_freelancer_id = project.accepted_bid.freelancer_id if project.accepted_bid else None
            if accepted_freelancer_id != user_id:
                return error_response("You do not have permission to update this project", 403)

        data = request.get_json(silent=True) or {}
        missing = validate_required_fields(data, ["status"])
        if missing:
            return error_response("Missing required fields", 422, errors={"missing_fields": missing})

        new_status_raw = str(data["status"]).strip().lower()
        if not is_valid_project_status(new_status_raw):
            return error_response("Invalid status value", 422)

        new_status = ProjectStatusEnum(new_status_raw)

        if role == "freelancer" and new_status != ProjectStatusEnum.CANCELLED:
            return error_response("Freelancers may only cancel a project", 403)

        if new_status == ProjectStatusEnum.COMPLETED and not ProjectService.has_accepted_bid(project.id):
            return error_response("Cannot complete a project with no accepted freelancer", 409)

        if not ProjectService.can_transition(project.status, new_status):
            return error_response(
                f"Cannot change status from '{project.status.value}' to '{new_status.value}'", 409
            )

        project = ProjectService.update_status(project, new_status)
        return success_response("Project status updated", data={"project": project.to_dict()})
