from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from services.profile_service import ProfileService
from utils.responses import success_response, error_response
from utils.validators import (
    validate_required_fields,
    is_non_negative_number,
    is_positive_int,
    is_valid_url,
)


class ProfileController:

    # ---------------------------------------------------------------
    # OWN PROFILE
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def get_my_profile():
        user_id = get_jwt_identity()
        user = ProfileService.get_user_with_profile(user_id)
        if not user:
            return error_response("User not found", 404)
        return success_response(
            "Profile fetched", data={"user": user.to_dict(include_profile=True)}
        )

    @staticmethod
    @jwt_required()
    def update_my_profile():
        user_id = get_jwt_identity()
        role = get_jwt().get("role")
        user = ProfileService.get_user_with_profile(user_id)
        if not user or not user.profile:
            return error_response("Profile not found", 404)

        data = request.get_json(silent=True) or {}

        # Freelancer-only fields must not be settable by clients
        freelancer_only = ["title", "experience_years", "hourly_rate"]
        if role != "freelancer":
            for field in freelancer_only:
                data.pop(field, None)

        if "experience_years" in data and not is_non_negative_number(data["experience_years"]):
            return error_response("experience_years must be a non-negative number", 422)

        if "hourly_rate" in data and not is_non_negative_number(data["hourly_rate"]):
            return error_response("hourly_rate must be a non-negative number", 422)

        if "phone" in data and data["phone"] and len(str(data["phone"])) > 20:
            return error_response("Phone number is too long", 422)

        profile = ProfileService.update_profile(user.profile, data)
        return success_response("Profile updated", data={"profile": profile.to_dict()})

    # ---------------------------------------------------------------
    # PUBLIC VIEW
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def get_public_profile(user_id):
        user = ProfileService.get_user_with_profile(user_id)
        if not user:
            return error_response("User not found", 404)
        return success_response(
            "Profile fetched", data={"user": user.to_dict(include_profile=True)}
        )

    # ---------------------------------------------------------------
    # SKILLS (freelancer only)
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def add_skill():
        role = get_jwt().get("role")
        if role != "freelancer":
            return error_response("Only freelancers can add skills", 403)

        user_id = get_jwt_identity()
        profile = ProfileService.get_profile_by_user_id(user_id)
        if not profile:
            return error_response("Profile not found", 404)

        data = request.get_json(silent=True) or {}
        missing = validate_required_fields(data, ["name"])
        if missing:
            return error_response("Missing required fields", 422, errors={"missing_fields": missing})

        skill_name = str(data.get("name")).strip()
        if len(skill_name) < 2 or len(skill_name) > 80:
            return error_response("Skill name must be between 2 and 80 characters", 422)

        skill, created = ProfileService.add_skill(profile, skill_name)
        message = "Skill added" if created else "Skill already exists on profile"
        return success_response(message, data={"skill": skill.to_dict()}, status_code=201 if created else 200)

    @staticmethod
    @jwt_required()
    def remove_skill(skill_id):
        role = get_jwt().get("role")
        if role != "freelancer":
            return error_response("Only freelancers can remove skills", 403)

        user_id = get_jwt_identity()
        profile = ProfileService.get_profile_by_user_id(user_id)
        if not profile:
            return error_response("Profile not found", 404)

        removed = ProfileService.remove_skill(profile, skill_id)
        if not removed:
            return error_response("Skill not found on profile", 404)
        return success_response("Skill removed")

    # ---------------------------------------------------------------
    # PORTFOLIO LINKS (freelancer only)
    # ---------------------------------------------------------------
    @staticmethod
    @jwt_required()
    def add_portfolio_link():
        role = get_jwt().get("role")
        if role != "freelancer":
            return error_response("Only freelancers can add portfolio links", 403)

        user_id = get_jwt_identity()
        profile = ProfileService.get_profile_by_user_id(user_id)
        if not profile:
            return error_response("Profile not found", 404)

        data = request.get_json(silent=True) or {}
        missing = validate_required_fields(data, ["url"])
        if missing:
            return error_response("Missing required fields", 422, errors={"missing_fields": missing})

        url = str(data.get("url")).strip()
        if not is_valid_url(url):
            return error_response("Invalid URL — must start with http:// or https://", 422)

        title = str(data.get("title")).strip() if data.get("title") else None

        link = ProfileService.add_portfolio_link(profile, title, url)
        return success_response("Portfolio link added", data={"portfolio_link": link.to_dict()}, status_code=201)

    @staticmethod
    @jwt_required()
    def remove_portfolio_link(link_id):
        role = get_jwt().get("role")
        if role != "freelancer":
            return error_response("Only freelancers can remove portfolio links", 403)

        user_id = get_jwt_identity()
        profile = ProfileService.get_profile_by_user_id(user_id)
        if not profile:
            return error_response("Profile not found", 404)

        removed = ProfileService.remove_portfolio_link(profile, link_id)
        if not removed:
            return error_response("Portfolio link not found", 404)
        return success_response("Portfolio link removed")
