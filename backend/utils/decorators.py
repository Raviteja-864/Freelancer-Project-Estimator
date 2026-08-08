from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from utils.responses import error_response


def role_required(*allowed_roles):
    """
    Restricts an endpoint to specific roles.
    Usage: @role_required("admin") or @role_required("client", "admin")
    Must be used together with @jwt_required() OR it will call verify itself.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in allowed_roles:
                return error_response(
                    "Access denied: insufficient permissions", 403
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def get_current_user_id():
    """Helper to fetch identity (user id) from JWT after verify_jwt_in_request()."""
    from flask_jwt_extended import get_jwt_identity

    return get_jwt_identity()
