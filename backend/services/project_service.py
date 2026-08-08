from extensions import db
from models import Project, ProjectStatusEnum, Bid, BidStatusEnum

# Allowed forward transitions for project status.
# Reached from the *current* status, mapping to the set of statuses it may move to.
ALLOWED_TRANSITIONS = {
    ProjectStatusEnum.OPEN: {ProjectStatusEnum.IN_PROGRESS, ProjectStatusEnum.CANCELLED},
    ProjectStatusEnum.IN_PROGRESS: {ProjectStatusEnum.COMPLETED, ProjectStatusEnum.CANCELLED},
    ProjectStatusEnum.COMPLETED: set(),
    ProjectStatusEnum.CANCELLED: set(),
}


class ProjectService:

    @staticmethod
    def create_project(client_id, data):
        project = Project(
            client_id=client_id,
            title=data["title"].strip(),
            description=data["description"].strip(),
            category=data.get("category", "").strip() or None,
            budget_min=data.get("budget_min"),
            budget_max=data.get("budget_max"),
            deadline=data.get("deadline"),  # already parsed to a date by controller
            status=ProjectStatusEnum.OPEN,
        )
        db.session.add(project)
        db.session.commit()
        return project

    @staticmethod
    def get_by_id(project_id):
        return Project.query.get(project_id)

    @staticmethod
    def list_projects(filters, page=1, per_page=20):
        query = Project.query

        status = filters.get("status")
        if status:
            query = query.filter(Project.status == ProjectStatusEnum(status))
        else:
            # Default marketplace view: only show open projects unless explicitly overridden
            if filters.get("default_open_only"):
                query = query.filter(Project.status == ProjectStatusEnum.OPEN)

        if filters.get("category"):
            # Supports a single category or a comma-separated list
            # (matches the Browse Projects page's multi-select checkboxes).
            categories = [c.strip() for c in filters["category"].split(",") if c.strip()]
            if categories:
                query = query.filter(
                    db.or_(*[Project.category.ilike(f"%{c}%") for c in categories])
                )

        if filters.get("keyword"):
            kw = f"%{filters['keyword']}%"
            query = query.filter(
                db.or_(Project.title.ilike(kw), Project.description.ilike(kw))
            )

        if filters.get("budget_min") is not None:
            query = query.filter(
                db.or_(Project.budget_max == None, Project.budget_max >= filters["budget_min"])  # noqa: E711
            )

        if filters.get("budget_max") is not None:
            query = query.filter(
                db.or_(Project.budget_min == None, Project.budget_min <= filters["budget_max"])  # noqa: E711
            )

        if filters.get("client_id"):
            query = query.filter(Project.client_id == filters["client_id"])

        sort = filters.get("sort") or "newest"
        if sort == "budget_desc":
            # NULLS LAST so unset budgets don't dominate the top of the list
            query = query.order_by(db.nullslast(Project.budget_max.desc()))
        elif sort == "bids_asc":
            bid_count_subq = (
                db.session.query(Bid.project_id, db.func.count(Bid.id).label("bid_count"))
                .group_by(Bid.project_id)
                .subquery()
            )
            query = query.outerjoin(
                bid_count_subq, Project.id == bid_count_subq.c.project_id
            ).order_by(db.func.coalesce(bid_count_subq.c.bid_count, 0).asc())
        else:  # "newest" (default)
            query = query.order_by(Project.created_at.desc())

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def update_project(project, data):
        editable_fields = ["title", "description", "category", "budget_min", "budget_max", "deadline"]
        for field in editable_fields:
            if field in data:
                value = data[field]
                if isinstance(value, str):
                    value = value.strip() or None
                setattr(project, field, value)
        db.session.commit()
        return project

    @staticmethod
    def delete_project(project):
        db.session.delete(project)
        db.session.commit()

    @staticmethod
    def can_transition(current_status, new_status):
        return new_status in ALLOWED_TRANSITIONS.get(current_status, set())

    @staticmethod
    def update_status(project, new_status):
        project.status = new_status
        db.session.commit()
        return project

    @staticmethod
    def get_bids_for_project(project_id):
        return Bid.query.filter_by(project_id=project_id).order_by(Bid.created_at.desc()).all()

    @staticmethod
    def has_accepted_bid(project_id):
        return Bid.query.filter_by(project_id=project_id, status=BidStatusEnum.ACCEPTED).first() is not None
