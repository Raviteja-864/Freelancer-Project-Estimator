from flask import request
from flask_jwt_extended import get_jwt_identity

from services.admin_service import AdminService
from utils.responses import success_response, error_response
from utils.validators import (
    validate_required_fields,
    is_valid_role,
    is_valid_account_status,
    is_valid_project_status,
    is_valid_bid_status,
)
from utils.decorators import role_required


def _pagination_args(args):
    page = max(int(args.get("page", 1)), 1)
    per_page = min(max(int(args.get("per_page", 20)), 1), 100)
    return page, per_page


class AdminController:

    # ---------------------------------------------------------------
    # DASHBOARD
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("admin")
    def dashboard():
        stats = AdminService.get_dashboard_stats()
        return success_response("Dashboard stats fetched", data={"stats": stats})

    # ---------------------------------------------------------------
    # USERS
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("admin")
    def list_users():
        args = request.args
        if args.get("role") and not is_valid_role(args.get("role")):
            return error_response("Invalid role filter", 422)
        if args.get("account_status") and not is_valid_account_status(args.get("account_status")):
            return error_response("Invalid account_status filter", 422)

        try:
            page, per_page = _pagination_args(args)
        except ValueError:
            return error_response("page and per_page must be integers", 422)

        filters = {
            "role": args.get("role"),
            "account_status": args.get("account_status"),
            "keyword": args.get("keyword"),
        }
        pagination = AdminService.list_users(filters, page=page, per_page=per_page)
        return success_response(
            "Users fetched",
            data={
                "users": [u.to_dict(include_profile=True) for u in pagination.items],
                "pagination": {
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "total_pages": pagination.pages,
                },
            },
        )

    @staticmethod
    @role_required("admin")
    def update_user_status(user_id):
        from models import AccountStatusEnum

        user = AdminService.get_user(user_id)
        if not user:
            return error_response("User not found", 404)

        data = request.get_json(silent=True) or {}
        missing = validate_required_fields(data, ["account_status"])
        if missing:
            return error_response("Missing required fields", 422, errors={"missing_fields": missing})

        new_status = str(data["account_status"]).strip().lower()
        if not is_valid_account_status(new_status):
            return error_response("account_status must be one of: active, suspended, deleted", 422)

        user = AdminService.update_user_status(user, AccountStatusEnum(new_status))
        return success_response("User status updated", data={"user": user.to_dict()})

    @staticmethod
    @role_required("admin")
    def delete_user(user_id):
        admin_id = int(get_jwt_identity())
        if admin_id == user_id:
            return error_response("You cannot delete your own admin account", 409)

        user = AdminService.get_user(user_id)
        if not user:
            return error_response("User not found", 404)

        AdminService.delete_user(user)
        return success_response("User deleted")

    # ---------------------------------------------------------------
    # PROJECTS
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("admin")
    def list_all_projects():
        args = request.args
        if args.get("status") and not is_valid_project_status(args.get("status")):
            return error_response("Invalid status filter", 422)

        try:
            page, per_page = _pagination_args(args)
        except ValueError:
            return error_response("page and per_page must be integers", 422)

        filters = {"status": args.get("status"), "keyword": args.get("keyword")}
        pagination = AdminService.list_all_projects(filters, page=page, per_page=per_page)
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

    @staticmethod
    @role_required("admin")
    def delete_project(project_id):
        project = AdminService.get_project(project_id)
        if not project:
            return error_response("Project not found", 404)
        AdminService.delete_project(project)
        return success_response("Project deleted")

    # ---------------------------------------------------------------
    # BIDS
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("admin")
    def list_all_bids():
        args = request.args
        if args.get("status") and not is_valid_bid_status(args.get("status")):
            return error_response("Invalid status filter", 422)

        try:
            page, per_page = _pagination_args(args)
        except ValueError:
            return error_response("page and per_page must be integers", 422)

        filters = {"status": args.get("status"), "project_id": args.get("project_id")}
        pagination = AdminService.list_all_bids(filters, page=page, per_page=per_page)
        return success_response(
            "Bids fetched",
            data={
                "bids": [b.to_dict() for b in pagination.items],
                "pagination": {
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "total_pages": pagination.pages,
                },
            },
        )

    @staticmethod
    @role_required("admin")
    def delete_bid(bid_id):
        bid = AdminService.get_bid(bid_id)
        if not bid:
            return error_response("Bid not found", 404)
        AdminService.delete_bid(bid)
        return success_response("Bid deleted")
