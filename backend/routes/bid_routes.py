from flask import Blueprint
from controllers.bid_controller import BidController

bid_bp = Blueprint("bid", __name__, url_prefix="/api/bids")

bid_bp.route("", methods=["POST"])(BidController.create_bid)
bid_bp.route("/mine", methods=["GET"])(BidController.list_my_bids)
bid_bp.route("/accepted-projects", methods=["GET"])(BidController.list_accepted_projects)
bid_bp.route("/project/<int:project_id>", methods=["GET"])(BidController.list_project_bids)
bid_bp.route("/<int:bid_id>", methods=["PUT"])(BidController.update_bid)
bid_bp.route("/<int:bid_id>/withdraw", methods=["POST"])(BidController.withdraw_bid)
bid_bp.route("/<int:bid_id>/accept", methods=["POST"])(BidController.accept_bid)
bid_bp.route("/<int:bid_id>/reject", methods=["POST"])(BidController.reject_bid)
