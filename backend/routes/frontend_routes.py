from flask import Blueprint, render_template, redirect

frontend_bp = Blueprint("frontend", __name__)


@frontend_bp.route("/")
def index():
    return render_template("landing.html")


@frontend_bp.route("/login")
def login_page():
    return render_template("auth/login.html")


@frontend_bp.route("/register")
def register_page():
    return render_template("auth/register.html")


@frontend_bp.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@frontend_bp.route("/find-work")
def find_work_page():
    return render_template("find_work.html")


@frontend_bp.route("/projects/new")
def new_project_page():
    return render_template("new_project.html")


@frontend_bp.route("/projects/<int:project_id>")
def project_detail_page(project_id):
    return render_template("project_detail.html")


@frontend_bp.route("/messages/<int:project_id>")
def messages_page(project_id):
    return render_template("messages.html")


@frontend_bp.route("/payments/<int:project_id>")
def payment_page(project_id):
    return render_template("payment.html")


@frontend_bp.route("/projects/<int:project_id>/review")
def project_review_page(project_id):
    return render_template("project_review.html")


@frontend_bp.route("/freelancers/<int:user_id>/reviews")
def freelancer_reviews_page(user_id):
    return render_template("freelancer_reviews.html")


@frontend_bp.route("/admin")
def admin_page():
    return render_template("admin.html")

