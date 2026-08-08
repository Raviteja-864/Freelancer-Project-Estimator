from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from services.auth_service import AuthService
from utils.responses import success_response, error_response
from utils.validators import (
    is_valid_email,
    is_valid_password,
    is_valid_role,
    validate_required_fields,
)
from blocklist import BLOCKLIST


class AuthController:

    @staticmethod
    def register():
        data = request.get_json(silent=True) or {}

        missing = validate_required_fields(data, ["name", "email", "password", "role"])
        if missing:
            return error_response(
                "Missing required fields", 422, errors={"missing_fields": missing}
            )

        name = data.get("name").strip()
        email = data.get("email").strip()
        password = data.get("password")
        role = data.get("role").strip().lower()

        if len(name) < 2:
            return error_response("Name must be at least 2 characters", 422)

        if not is_valid_email(email):
            return error_response("Invalid email format", 422)

        if not is_valid_password(password):
            return error_response(
                "Password must be at least 6 characters and include a letter and a number",
                422,
            )

        if not is_valid_role(role) or role == "admin":
            # Admin accounts should not be self-registered via public API
            return error_response("Role must be either 'client' or 'freelancer'", 422)

        if AuthService.user_exists(email):
            return error_response("An account with this email already exists", 409)

        try:
            user = AuthService.register_user(name, email, password, role)
        except Exception as e:
            return error_response(f"Registration failed: {str(e)}", 500)

        access_token = create_access_token(
            identity=str(user.id), additional_claims={"role": user.role.value}
        )
        refresh_token = create_refresh_token(identity=str(user.id))

        return success_response(
            "Registration successful",
            data={
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
            status_code=201,
        )

    @staticmethod
    def login():
        data = request.get_json(silent=True) or {}

        missing = validate_required_fields(data, ["email", "password"])
        if missing:
            return error_response(
                "Missing required fields", 422, errors={"missing_fields": missing}
            )

        email = data.get("email").strip()
        password = data.get("password")

        user, err = AuthService.authenticate(email, password)
        if err:
            return error_response(err, 401)

        access_token = create_access_token(
            identity=str(user.id), additional_claims={"role": user.role.value}
        )
        refresh_token = create_refresh_token(identity=str(user.id))

        return success_response(
            "Login successful",
            data={
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
        )

    @staticmethod
    @jwt_required()
    def logout():
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return success_response("Logout successful")

    @staticmethod
    @jwt_required(refresh=True)
    def refresh():
        identity = get_jwt_identity()
        claims = get_jwt()
        new_token = create_access_token(
            identity=identity, additional_claims={"role": claims.get("role")}
        )
        return success_response("Token refreshed", data={"access_token": new_token})

    @staticmethod
    @jwt_required()
    def get_current_user():
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return error_response("User not found", 404)
        return success_response("User fetched", data={"user": user.to_dict(include_profile=True)})
