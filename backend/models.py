"""
FreelanceHub Database Models
=============================
Normalized MySQL schema via SQLAlchemy ORM.

Tables:
  - users              : core auth + role info
  - profiles           : extended profile data (1-1 with users)
  - skills             : master skill list
  - freelancer_skills  : many-to-many (freelancer <-> skill)
  - portfolio_links    : freelancer portfolio items (1-many)
  - projects           : client-posted projects
  - bids               : freelancer bids on projects
  - messages           : chat between client & freelancer per project
  - payments           : payment status tracking per project
  - reviews            : client -> freelancer ratings/reviews
"""

from datetime import datetime
from extensions import db
import enum


# ---------------------------------------------------------------------------
# ENUMS
# ---------------------------------------------------------------------------
class RoleEnum(str, enum.Enum):
    CLIENT = "client"
    FREELANCER = "freelancer"
    ADMIN = "admin"


class ProjectStatusEnum(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BidStatusEnum(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class AccountStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


# ---------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.CLIENT)
    account_status = db.Column(
        db.Enum(AccountStatusEnum), nullable=False, default=AccountStatusEnum.ACTIVE
    )
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = db.relationship(
        "Profile", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    projects_posted = db.relationship(
        "Project", backref="client", foreign_keys="Project.client_id",
        cascade="all, delete-orphan"
    )
    bids = db.relationship(
        "Bid", backref="freelancer", foreign_keys="Bid.freelancer_id",
        cascade="all, delete-orphan"
    )
    sent_messages = db.relationship(
        "Message", backref="sender", foreign_keys="Message.sender_id"
    )
    reviews_given = db.relationship(
        "Review", backref="client_reviewer", foreign_keys="Review.client_id"
    )
    reviews_received = db.relationship(
        "Review", backref="freelancer_reviewed", foreign_keys="Review.freelancer_id"
    )

    def to_dict(self, include_profile=False):
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value if isinstance(self.role, RoleEnum) else self.role,
            "account_status": self.account_status.value
            if isinstance(self.account_status, AccountStatusEnum)
            else self.account_status,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_profile and self.profile:
            data["profile"] = self.profile.to_dict()
        return data


# ---------------------------------------------------------------------------
# PROFILES (1-1 with users) - shared by clients & freelancers
# ---------------------------------------------------------------------------
class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(120), nullable=True)

    # Freelancer-specific fields (nullable for clients)
    title = db.Column(db.String(150), nullable=True)          # e.g. "Full Stack Developer"
    experience_years = db.Column(db.Integer, nullable=True)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    skills = db.relationship(
        "FreelancerSkill", backref="profile", cascade="all, delete-orphan"
    )
    portfolio_links = db.relationship(
        "PortfolioLink", backref="profile", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bio": self.bio,
            "profile_picture": self.profile_picture,
            "phone": self.phone,
            "location": self.location,
            "title": self.title,
            "experience_years": self.experience_years,
            "hourly_rate": float(self.hourly_rate) if self.hourly_rate else None,
            "skills": [s.skill.name for s in self.skills] if self.skills else [],
            "portfolio_links": [p.to_dict() for p in self.portfolio_links],
        }


# ---------------------------------------------------------------------------
# SKILLS (master list) + FREELANCER_SKILLS (junction table)
# ---------------------------------------------------------------------------
class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class FreelancerSkill(db.Model):
    __tablename__ = "freelancer_skills"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)

    skill = db.relationship("Skill")

    __table_args__ = (
        db.UniqueConstraint("profile_id", "skill_id", name="uq_profile_skill"),
    )


# ---------------------------------------------------------------------------
# PORTFOLIO LINKS (1-many with profile)
# ---------------------------------------------------------------------------
class PortfolioLink(db.Model):
    __tablename__ = "portfolio_links"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)
    title = db.Column(db.String(150), nullable=True)
    url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "url": self.url}


# ---------------------------------------------------------------------------
# PROJECTS
# ---------------------------------------------------------------------------
class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=True, index=True)
    budget_min = db.Column(db.Numeric(10, 2), nullable=True)
    budget_max = db.Column(db.Numeric(10, 2), nullable=True)
    deadline = db.Column(db.Date, nullable=True)

    status = db.Column(
        db.Enum(ProjectStatusEnum), nullable=False, default=ProjectStatusEnum.OPEN, index=True
    )
    accepted_bid_id = db.Column(db.Integer, db.ForeignKey("bids.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bids = db.relationship(
        "Bid", backref="project", foreign_keys="Bid.project_id",
        cascade="all, delete-orphan"
    )
    messages = db.relationship("Message", backref="project", cascade="all, delete-orphan")
    payment = db.relationship(
        "Payment", backref="project", uselist=False, cascade="all, delete-orphan"
    )
    review = db.relationship(
        "Review", backref="project", uselist=False, cascade="all, delete-orphan"
    )
    accepted_bid = db.relationship("Bid", foreign_keys=[accepted_bid_id], post_update=True)

    def to_dict(self, include_bids=False):
        data = {
            "id": self.id,
            "client_id": self.client_id,
            "client_name": self.client.name if self.client else None,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "budget_min": float(self.budget_min) if self.budget_min else None,
            "budget_max": float(self.budget_max) if self.budget_max else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "status": self.status.value if isinstance(self.status, ProjectStatusEnum) else self.status,
            "accepted_bid_id": self.accepted_bid_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "bid_count": len(self.bids) if self.bids else 0,
        }
        if include_bids:
            data["bids"] = [b.to_dict() for b in self.bids]
        return data


# ---------------------------------------------------------------------------
# BIDS
# ---------------------------------------------------------------------------
class Bid(db.Model):
    __tablename__ = "bids"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    freelancer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    price = db.Column(db.Numeric(10, 2), nullable=False)
    proposal = db.Column(db.Text, nullable=False)
    estimated_days = db.Column(db.Integer, nullable=False)

    status = db.Column(
        db.Enum(BidStatusEnum), nullable=False, default=BidStatusEnum.PENDING, index=True
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("project_id", "freelancer_id", name="uq_project_freelancer_bid"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "project_title": self.project.title if self.project else None,
            "freelancer_id": self.freelancer_id,
            "freelancer_name": self.freelancer.name if self.freelancer else None,
            "price": float(self.price) if self.price else None,
            "proposal": self.proposal,
            "estimated_days": self.estimated_days,
            "status": self.status.value if isinstance(self.status, BidStatusEnum) else self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# MESSAGES (chat)
# ---------------------------------------------------------------------------
class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.name if self.sender else None,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# PAYMENTS (status tracking only - no gateway)
# ---------------------------------------------------------------------------
class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), unique=True, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(
        db.Enum(PaymentStatusEnum), nullable=False, default=PaymentStatusEnum.PENDING
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "amount": float(self.amount) if self.amount else None,
            "status": self.status.value if isinstance(self.status, PaymentStatusEnum) else self.status,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ---------------------------------------------------------------------------
# REVIEWS
# ---------------------------------------------------------------------------
class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    freelancer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="chk_rating_range"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "client_id": self.client_id,
            "client_name": self.client_reviewer.name if self.client_reviewer else None,
            "freelancer_id": self.freelancer_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
