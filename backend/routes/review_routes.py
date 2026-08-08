from flask import Blueprint
from controllers.review_controller import ReviewController

review_bp = Blueprint("review", __name__, url_prefix="/api/reviews")

review_bp.route("", methods=["POST"])(ReviewController.create_review)
review_bp.route("/freelancer/<int:user_id>", methods=["GET"])(ReviewController.list_freelancer_reviews)
review_bp.route("/project/<int:project_id>", methods=["GET"])(ReviewController.get_project_review)
