from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from services.dashboard_service import DashboardService
from utils.responses import success_response, error_response


class DashboardController:

    @staticmethod
    @jwt_required()
    def get_dashboard():
        """
        GET /api/dashboard
        Returns the correct dashboard payload based on the caller's role
        (client or freelancer). Admins get a 403 here — they use /api/admin/dashboard.
        """
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role == "client":
            data = DashboardService.get_client_dashboard(user_id)
        elif role == "freelancer":
            data = DashboardService.get_freelancer_dashboard(user_id)
        else:
            return error_response("Use /api/admin/dashboard for admin accounts", 403)

        return success_response("Dashboard fetched", data=data)
