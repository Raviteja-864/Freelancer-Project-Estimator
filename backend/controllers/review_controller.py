from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from services.review_service import ReviewService
from services.project_service import ProjectService
from models import ProjectStatusEnum
from utils.responses import success_response, error_response
from utils.validators import validate_required_fields, is_valid_rating
from utils.decorators import role_required


class ReviewController:

    # ---------------------------------------------------------------
    # CREATE REVIEW (client only, project must be completed)
    # ---------------------------------------------------------------
    @staticmethod
    @role_required("client")
    def create_review():
        client_id = int(get_jwt_identity())
        data = request.get_json(silent=True) or {}

        missing = validate_required_fields(data, ["project_id", "rating"])
        if missing:
            return error_response("Missing required fields", 422, errors={"missing_fields": missing})

        project = ProjectService.get_by_id(data["project_id"])
        if not project:
            return error_response("Project not found", 404)
        if project.client_id != client_id:
            return error_response("You do not have permission to review this project", 403)
        if project.status != ProjectStatusEnum.COMPLETED:
            return error_response("You can only review a project once it is completed", 409)
        if not project.accepted_bid:
            return error_response("This project has no accepted freelancer to review", 409)
        if project.review:
            return error_response("This project has already been reviewed", 409)

        if not is_valid_rating(data["rating"]):
            return error_response("rating must be an integer between 1 and 5", 422)

        comment = str(data.get("comment")).strip() if data.get("comment") else None

        review = ReviewService.create_review(
            project, client_id, project.accepted_bid.freelancer_id, int(data["rating"]), comment
        )
        return success_response("Review submitted", data={"review": review.to_dict()}, status_code=201)

    # ---------------------------------------------------------------
    # REVIEWS FOR A FREELANCER (+ average rating)
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def list_freelancer_reviews(user_id):
        args = request.args
        try:
            page = max(int(args.get("page", 1)), 1)
            per_page = min(max(int(args.get("per_page", 20)), 1), 100)
        except ValueError:
            return error_response("page and per_page must be integers", 422)

        pagination = ReviewService.list_by_freelancer(user_id, page=page, per_page=per_page)
        avg_rating, total_reviews = ReviewService.get_average_rating(user_id)

        return success_response(
            "Reviews fetched",
            data={
                "reviews": [r.to_dict() for r in pagination.items],
                "average_rating": avg_rating,
                "total_reviews": total_reviews,
                "pagination": {
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "total_pages": pagination.pages,
                },
            },
        )

    # ---------------------------------------------------------------
    # REVIEW FOR A SPECIFIC PROJECT
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def get_project_review(project_id):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        project = ProjectService.get_by_id(project_id)
        if not project:
            return error_response("Project not found", 404)

        is_client = project.client_id == user_id
        is_freelancer = project.accepted_bid and project.accepted_bid.freelancer_id == user_id
        if role != "admin" and not is_client and not is_freelancer:
            return error_response("You do not have permission to view this review", 403)

        review = ReviewService.get_by_project(project_id)
        if not review:
            return error_response("No review found for this project", 404)

        return success_response("Review fetched", data={"review": review.to_dict()})
