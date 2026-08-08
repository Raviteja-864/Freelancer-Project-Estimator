from extensions import db
from models import Profile, Skill, FreelancerSkill, PortfolioLink, User


class ProfileService:

    @staticmethod
    def get_profile_by_user_id(user_id):
        return Profile.query.filter_by(user_id=user_id).first()

    @staticmethod
    def get_user_with_profile(user_id):
        return User.query.get(user_id)

    @staticmethod
    def update_profile(profile, data):
        """Updates whitelisted fields only. Freelancer-only fields (title,
        experience_years, hourly_rate) are accepted regardless of role here —
        the controller decides which fields are allowed for the caller's role."""
        allowed_fields = [
            "bio", "phone", "location", "title",
            "experience_years", "hourly_rate", "profile_picture",
        ]
        for field in allowed_fields:
            if field in data:
                setattr(profile, field, data[field])
        db.session.commit()
        return profile

    @staticmethod
    def add_skill(profile, skill_name):
        skill_name = skill_name.strip()
        skill = Skill.query.filter_by(name=skill_name).first()
        if not skill:
            skill = Skill(name=skill_name)
            db.session.add(skill)
            db.session.flush()

        existing = FreelancerSkill.query.filter_by(
            profile_id=profile.id, skill_id=skill.id
        ).first()
        if existing:
            return skill, False  # already added

        link = FreelancerSkill(profile_id=profile.id, skill_id=skill.id)
        db.session.add(link)
        db.session.commit()
        return skill, True

    @staticmethod
    def remove_skill(profile, skill_id):
        link = FreelancerSkill.query.filter_by(
            profile_id=profile.id, skill_id=skill_id
        ).first()
        if not link:
            return False
        db.session.delete(link)
        db.session.commit()
        return True

    @staticmethod
    def add_portfolio_link(profile, title, url):
        link = PortfolioLink(profile_id=profile.id, title=title, url=url)
        db.session.add(link)
        db.session.commit()
        return link

    @staticmethod
    def remove_portfolio_link(profile, link_id):
        link = PortfolioLink.query.filter_by(
            id=link_id, profile_id=profile.id
        ).first()
        if not link:
            return False
        db.session.delete(link)
        db.session.commit()
        return True
