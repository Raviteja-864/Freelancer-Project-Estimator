from extensions import db
from models import Project, Bid, Payment, Message, ProjectStatusEnum, PaymentStatusEnum


class DashboardService:
    """
    Aggregates data for the client/freelancer dashboard screens.
    Built to match the FreelanceHub UI: stat cards, active-projects table,
    and a merged 'Recent Activity' feed (new bids, payments, messages).
    """

    ACTIVITY_LIMIT = 8
    ACTIVE_PROJECTS_LIMIT = 5

    # ------------------------------------------------------------------
    # CLIENT DASHBOARD
    # ------------------------------------------------------------------
    @staticmethod
    def get_client_dashboard(client_id):
        projects = Project.query.filter_by(client_id=client_id).all()
        project_ids = [p.id for p in projects]

        total_projects = len(projects)
        active = sum(
            1 for p in projects
            if p.status in (ProjectStatusEnum.OPEN, ProjectStatusEnum.IN_PROGRESS)
        )
        completed = sum(1 for p in projects if p.status == ProjectStatusEnum.COMPLETED)

        bids_received = (
            db.session.query(Bid)
            .filter(Bid.project_id.in_(project_ids))
            .count()
            if project_ids else 0
        )

        # Active projects table (most recently updated first)
        active_projects = sorted(
            [p for p in projects if p.status in (ProjectStatusEnum.OPEN, ProjectStatusEnum.IN_PROGRESS)],
            key=lambda p: p.updated_at or p.created_at,
            reverse=True,
        )[:DashboardService.ACTIVE_PROJECTS_LIMIT]

        active_projects_data = []
        for p in active_projects:
            accepted_bid = p.accepted_bid
            freelancer_name = accepted_bid.freelancer.name if accepted_bid and accepted_bid.freelancer else None
            active_projects_data.append({
                "id": p.id,
                "title": p.title,
                "status": p.status.value,
                "freelancer_name": freelancer_name,
                "bid_count": len(p.bids),
                "progress": DashboardService._progress_for(p),
            })

        activity = DashboardService._recent_activity_for_client(project_ids)

        return {
            "stats": {
                "total_projects": total_projects,
                "active": active,
                "completed": completed,
                "bids_received": bids_received,
            },
            "active_projects": active_projects_data,
            "recent_activity": activity,
        }

    # ------------------------------------------------------------------
    # FREELANCER DASHBOARD
    # ------------------------------------------------------------------
    @staticmethod
    def get_freelancer_dashboard(freelancer_id):
        bids = Bid.query.filter_by(freelancer_id=freelancer_id).all()
        accepted_project_ids = [b.project_id for b in bids if b.status.value == "accepted"]

        total_bids = len(bids)
        active_projects = Project.query.filter(
            Project.id.in_(accepted_project_ids),
            Project.status.in_([ProjectStatusEnum.OPEN, ProjectStatusEnum.IN_PROGRESS]),
        ).all() if accepted_project_ids else []
        completed_projects = Project.query.filter(
            Project.id.in_(accepted_project_ids),
            Project.status == ProjectStatusEnum.COMPLETED,
        ).count() if accepted_project_ids else 0

        pending_bids = sum(1 for b in bids if b.status.value == "pending")

        activity = DashboardService._recent_activity_for_freelancer(freelancer_id, accepted_project_ids)

        return {
            "stats": {
                "total_bids": total_bids,
                "active_projects": len(active_projects),
                "completed_projects": completed_projects,
                "pending_bids": pending_bids,
            },
            "active_projects": [
                {
                    "id": p.id,
                    "title": p.title,
                    "status": p.status.value,
                    "client_name": p.client.name if p.client else None,
                    "progress": DashboardService._progress_for(p),
                }
                for p in active_projects
            ],
            "recent_activity": activity,
        }

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    @staticmethod
    def _progress_for(project):
        """Rough progress heuristic for the UI progress bar (no separate milestones table)."""
        if project.status == ProjectStatusEnum.COMPLETED:
            return 100
        if project.status == ProjectStatusEnum.IN_PROGRESS:
            return 65
        if project.status == ProjectStatusEnum.OPEN and project.bids:
            return 15
        return 5

    @staticmethod
    def _recent_activity_for_client(project_ids):
        events = []
        if project_ids:
            recent_bids = (
                Bid.query.filter(Bid.project_id.in_(project_ids))
                .order_by(Bid.created_at.desc()).limit(DashboardService.ACTIVITY_LIMIT).all()
            )
            for b in recent_bids:
                events.append({
                    "type": "bid",
                    "title": f"New bid on {b.project.title if b.project else 'a project'}",
                    "subtitle": f"From: {b.freelancer.name if b.freelancer else 'Unknown'}",
                    "timestamp": b.created_at.isoformat() if b.created_at else None,
                })

            recent_payments = (
                Payment.query.filter(
                    Payment.project_id.in_(project_ids),
                    Payment.status == PaymentStatusEnum.PAID,
                )
                .order_by(Payment.updated_at.desc()).limit(DashboardService.ACTIVITY_LIMIT).all()
            )
            for pay in recent_payments:
                events.append({
                    "type": "payment",
                    "title": "Payment processed",
                    "subtitle": pay.project.title if pay.project else None,
                    "timestamp": pay.updated_at.isoformat() if pay.updated_at else None,
                })

            recent_messages = (
                Message.query.filter(Message.project_id.in_(project_ids))
                .order_by(Message.created_at.desc()).limit(DashboardService.ACTIVITY_LIMIT).all()
            )
            for m in recent_messages:
                events.append({
                    "type": "message",
                    "title": f"Message from {m.sender.name if m.sender else 'Unknown'}",
                    "subtitle": (m.content[:60] + "...") if len(m.content) > 60 else m.content,
                    "timestamp": m.created_at.isoformat() if m.created_at else None,
                })

        events.sort(key=lambda e: e["timestamp"] or "", reverse=True)
        return events[:DashboardService.ACTIVITY_LIMIT]

    @staticmethod
    def _recent_activity_for_freelancer(freelancer_id, project_ids):
        events = []

        recent_bid_updates = (
            Bid.query.filter_by(freelancer_id=freelancer_id)
            .order_by(Bid.updated_at.desc()).limit(DashboardService.ACTIVITY_LIMIT).all()
        )
        for b in recent_bid_updates:
            events.append({
                "type": "bid_status",
                "title": f"Bid {b.status.value} on {b.project.title if b.project else 'a project'}",
                "subtitle": f"${b.price}",
                "timestamp": b.updated_at.isoformat() if b.updated_at else None,
            })

        if project_ids:
            recent_messages = (
                Message.query.filter(
                    Message.project_id.in_(project_ids),
                    Message.receiver_id == freelancer_id,
                )
                .order_by(Message.created_at.desc()).limit(DashboardService.ACTIVITY_LIMIT).all()
            )
            for m in recent_messages:
                events.append({
                    "type": "message",
                    "title": f"Message from {m.sender.name if m.sender else 'Unknown'}",
                    "subtitle": (m.content[:60] + "...") if len(m.content) > 60 else m.content,
                    "timestamp": m.created_at.isoformat() if m.created_at else None,
                })

        events.sort(key=lambda e: e["timestamp"] or "", reverse=True)
        return events[:DashboardService.ACTIVITY_LIMIT]
