from flask import request
from flask_jwt_extended import get_jwt_identity, get_jwt

from services.bid_service import BidService
from services.project_service import ProjectService
from models import BidStatusEnum, ProjectStatusEnum
from utils.responses import success_response, error_response
from utils.validators import (
    validate_required_fields,
    is_positive_number,
    is_positive_int,
)
from utils.decorators import role_required


class BidController:

    # ---------------------------------------------------------------
    # SUBMIT BID (freelancer only)
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("freelancer")
    def create_bid():
        freelancer_id = int(get_jwt_identity())
        data = request.get_json(silent=True) or {}

        missing = validate_required_fields(data, ["project_id", "price", "proposal", "estimated_days"])
        if missing:
            return error_response("Missing required fields", 422, errors={"missing_fields": missing})

        project = ProjectService.get_by_id(data["project_id"])
        if not project:
            return error_response("Project not found", 404)
        if project.status != ProjectStatusEnum.OPEN:
            return error_response("You can only bid on open projects", 409)

        if not is_positive_number(data["price"]):
            return error_response("price must be a positive number", 422)
        if not is_positive_int(data["estimated_days"]):
            return error_response("estimated_days must be a positive integer", 422)

        proposal = str(data["proposal"]).strip()
        if len(proposal) < 20:
            return error_response("Proposal must be at least 20 characters", 422)

        existing = BidService.get_existing_bid(project.id, freelancer_id)
        if existing:
            return error_response("You have already placed a bid on this project", 409)

        clean_data = {"price": data["price"], "proposal": proposal, "estimated_days": data["estimated_days"]}
        bid = BidService.create_bid(freelancer_id, project.id, clean_data)
        return success_response("Bid submitted", data={"bid": bid.to_dict()}, status_code=201)

    # ---------------------------------------------------------------
    # FREELANCER'S OWN BIDS
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("freelancer")
    def list_my_bids():
        freelancer_id = int(get_jwt_identity())
        args = request.args
        status = args.get("status")
        if status and status not in [s.value for s in BidStatusEnum]:
            return error_response("Invalid status filter", 422)

        try:
            page = max(int(args.get("page", 1)), 1)
            per_page = min(max(int(args.get("per_page", 20)), 1), 100)
        except ValueError:
            return error_response("page and per_page must be integers", 422)

        pagination = BidService.list_by_freelancer(freelancer_id, status=status, page=page, per_page=per_page)
        return success_response(
            "Your bids fetched",
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

    # ---------------------------------------------------------------
    # BIDS ON A GIVEN PROJECT (client owner or admin)
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("client", "admin")
    def list_project_bids(project_id):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        project = ProjectService.get_by_id(project_id)
        if not project:
            return error_response("Project not found", 404)
        if role != "admin" and project.client_id != user_id:
            return error_response("You do not have permission to view these bids", 403)

        bids = BidService.list_by_project(project_id)
        return success_response("Bids fetched", data={"bids": [b.to_dict() for b in bids]})

    # ---------------------------------------------------------------
    # EDIT BID (freelancer, own bid, only while pending & project open)
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("freelancer")
    def update_bid(bid_id):
        freelancer_id = int(get_jwt_identity())
        bid = BidService.get_by_id(bid_id)
        if not bid:
            return error_response("Bid not found", 404)
        if bid.freelancer_id != freelancer_id:
            return error_response("You do not have permission to edit this bid", 403)
        if bid.status != BidStatusEnum.PENDING:
            return error_response("Only pending bids can be edited", 409)
        if bid.project.status != ProjectStatusEnum.OPEN:
            return error_response("This project is no longer open for bidding", 409)

        data = request.get_json(silent=True) or {}
        if not data:
            return error_response("No fields provided to update", 422)

        if "price" in data and not is_positive_number(data["price"]):
            return error_response("price must be a positive number", 422)
        if "estimated_days" in data and not is_positive_int(data["estimated_days"]):
            return error_response("estimated_days must be a positive integer", 422)
        if "proposal" in data and len(str(data["proposal"]).strip()) < 20:
            return error_response("Proposal must be at least 20 characters", 422)

        bid = BidService.update_bid(bid, data)
        return success_response("Bid updated", data={"bid": bid.to_dict()})

    # ---------------------------------------------------------------
    # WITHDRAW BID (freelancer, own bid)
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("freelancer")
    def withdraw_bid(bid_id):
        freelancer_id = int(get_jwt_identity())
        bid = BidService.get_by_id(bid_id)
        if not bid:
            return error_response("Bid not found", 404)
        if bid.freelancer_id != freelancer_id:
            return error_response("You do not have permission to withdraw this bid", 403)
        if bid.status != BidStatusEnum.PENDING:
            return error_response("Only pending bids can be withdrawn", 409)

        bid = BidService.withdraw_bid(bid)
        return success_response("Bid withdrawn", data={"bid": bid.to_dict()})

    # ---------------------------------------------------------------
    # ACCEPT BID (client, owner of the project)
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("client")
    def accept_bid(bid_id):
        client_id = int(get_jwt_identity())
        bid = BidService.get_by_id(bid_id)
        if not bid:
            return error_response("Bid not found", 404)

        project = bid.project
        if project.client_id != client_id:
            return error_response("You do not have permission to accept this bid", 403)
        if project.status != ProjectStatusEnum.OPEN:
            return error_response("This project is no longer open", 409)
        if bid.status != BidStatusEnum.PENDING:
            return error_response("Only a pending bid can be accepted", 409)

        bid, project, payment = BidService.accept_bid(bid, project)
        return success_response(
            "Bid accepted — project is now in progress",
            data={"bid": bid.to_dict(), "project": project.to_dict(), "payment": payment.to_dict()},
        )

    # ---------------------------------------------------------------
    # REJECT BID (client, owner of the project)
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("client")
    def reject_bid(bid_id):
        client_id = int(get_jwt_identity())
        bid = BidService.get_by_id(bid_id)
        if not bid:
            return error_response("Bid not found", 404)

        if bid.project.client_id != client_id:
            return error_response("You do not have permission to reject this bid", 403)
        if bid.status != BidStatusEnum.PENDING:
            return error_response("Only a pending bid can be rejected", 409)

        bid = BidService.reject_bid(bid)
        return success_response("Bid rejected", data={"bid": bid.to_dict()})

    # ---------------------------------------------------------------
    # ACCEPTED PROJECTS (freelancer)
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("freelancer")
    def list_accepted_projects():
        freelancer_id = int(get_jwt_identity())
        args = request.args
        try:
            page = max(int(args.get("page", 1)), 1)
            per_page = min(max(int(args.get("per_page", 20)), 1), 100)
        except ValueError:
            return error_response("page and per_page must be integers", 422)

        pagination = BidService.get_accepted_projects_for_freelancer(freelancer_id, page=page, per_page=per_page)
        return success_response(
            "Accepted projects fetched",
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
