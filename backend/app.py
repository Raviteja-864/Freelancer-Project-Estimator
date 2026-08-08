import os
from flask import Flask
from config import config_by_name
from extensions import db, bcrypt, jwt, cors
from utils.responses import error_response
from blocklist import BLOCKLIST


def create_app(config_name=None):
    app = Flask(__name__)

    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name[config_name])

    # ---- Init extensions ----
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # ---- JWT callbacks ----
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return error_response("Token has expired", 401)

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return error_response("Invalid token", 401)

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return error_response("Authorization token is required", 401)

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return error_response("Token has been revoked. Please log in again.", 401)

    # ---- Register blueprints ----
    from routes.auth_routes import auth_bp
    from routes.profile_routes import profile_bp
    from routes.project_routes import project_bp
    from routes.bid_routes import bid_bp
    from routes.message_routes import message_bp
    from routes.review_routes import review_bp
    from routes.payment_routes import payment_bp
    from routes.admin_routes import admin_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.frontend_routes import frontend_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(bid_bp)
    app.register_blueprint(message_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(frontend_bp)

    # ---- Global error handlers ----
    @app.errorhandler(404)
    def not_found(e):
        return error_response("Resource not found", 404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error_response("Method not allowed", 405)

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return error_response("Internal server error", 500)

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        db.session.rollback()
        app.logger.exception(e)
        return error_response(f"Unexpected error: {str(e)}", 500)

    # ---- Health check ----
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return {"status": "ok", "service": "FreelanceHub API"}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
