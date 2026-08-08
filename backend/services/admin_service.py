from extensions import db
from sqlalchemy import func
from models import (
    User, RoleEnum, AccountStatusEnum,
    Project, ProjectStatusEnum,
    Bid, BidStatusEnum,
    Review, Payment, PaymentStatusEnum,
)


class AdminService:

    # ---------------------------------------------------------------
    # DASHBOARD
    # ---------------------------------------------------------------
    @staticmethod
    def get_dashboard_stats():
        users_by_role = dict(
            db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
        )
        users_by_role = {k.value: v for k, v in users_by_role.items()}

        projects_by_status = dict(
            db.session.query(Project.status, func.count(Project.id)).group_by(Project.status).all()
        )
        projects_by_status = {k.value: v for k, v in projects_by_status.items()}

        bids_by_status = dict(
            db.session.query(Bid.status, func.count(Bid.id)).group_by(Bid.status).all()
        )
        bids_by_status = {k.value: v for k, v in bids_by_status.items()}

        total_paid = (
            db.session.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.status == PaymentStatusEnum.PAID)
            .scalar()
        )

        avg_rating = db.session.query(func.avg(Review.rating)).scalar()

        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()

        return {
            "total_users": sum(users_by_role.values()),
            "users_by_role": users_by_role,
            "total_projects": sum(projects_by_status.values()),
            "projects_by_status": projects_by_status,
            "total_bids": sum(bids_by_status.values()),
            "bids_by_status": bids_by_status,
            "total_reviews": db.session.query(func.count(Review.id)).scalar(),
            "average_rating": round(float(avg_rating), 2) if avg_rating is not None else None,
            "total_paid_amount": float(total_paid) if total_paid is not None else 0,
            "recent_users": [u.to_dict() for u in recent_users],
            "recent_projects": [p.to_dict() for p in recent_projects],
        }

    # ---------------------------------------------------------------
    # USERS
    # ---------------------------------------------------------------
    @staticmethod
    def list_users(filters, page=1, per_page=20):
        query = User.query
        if filters.get("role"):
            query = query.filter(User.role == RoleEnum(filters["role"]))
        if filters.get("account_status"):
            query = query.filter(User.account_status == AccountStatusEnum(filters["account_status"]))
        if filters.get("keyword"):
            kw = f"%{filters['keyword']}%"
            query = query.filter(db.or_(User.name.ilike(kw), User.email.ilike(kw)))
        query = query.order_by(User.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_user(user_id):
        return User.query.get(user_id)

    @staticmethod
    def update_user_status(user, new_status):
        user.account_status = new_status
        db.session.commit()
        return user

    @staticmethod
    def delete_user(user):
        db.session.delete(user)
        db.session.commit()

    # ---------------------------------------------------------------
    # PROJECTS
    # ---------------------------------------------------------------
    @staticmethod
    def list_all_projects(filters, page=1, per_page=20):
        query = Project.query
        if filters.get("status"):
            query = query.filter(Project.status == ProjectStatusEnum(filters["status"]))
        if filters.get("keyword"):
            kw = f"%{filters['keyword']}%"
            query = query.filter(db.or_(Project.title.ilike(kw), Project.description.ilike(kw)))
        query = query.order_by(Project.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_project(project_id):
        return Project.query.get(project_id)

    @staticmethod
    def delete_project(project):
        db.session.delete(project)
        db.session.commit()

    # ---------------------------------------------------------------
    # BIDS
    # ---------------------------------------------------------------
    @staticmethod
    def list_all_bids(filters, page=1, per_page=20):
        query = Bid.query
        if filters.get("status"):
            query = query.filter(Bid.status == BidStatusEnum(filters["status"]))
        if filters.get("project_id"):
            query = query.filter(Bid.project_id == filters["project_id"])
        query = query.order_by(Bid.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_bid(bid_id):
        return Bid.query.get(bid_id)

    @staticmethod
    def delete_bid(bid):
        db.session.delete(bid)
        db.session.commit()
