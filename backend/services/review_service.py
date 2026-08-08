from extensions import db
from sqlalchemy import func
from models import Review


class ReviewService:

    @staticmethod
    def create_review(project, client_id, freelancer_id, rating, comment):
        review = Review(
            project_id=project.id,
            client_id=client_id,
            freelancer_id=freelancer_id,
            rating=rating,
            comment=comment,
        )
        db.session.add(review)
        db.session.commit()
        return review

    @staticmethod
    def get_by_project(project_id):
        return Review.query.filter_by(project_id=project_id).first()

    @staticmethod
    def list_by_freelancer(freelancer_id, page=1, per_page=20):
        query = Review.query.filter_by(freelancer_id=freelancer_id).order_by(Review.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_average_rating(freelancer_id):
        result = (
            db.session.query(func.avg(Review.rating), func.count(Review.id))
            .filter(Review.freelancer_id == freelancer_id)
            .first()
        )
        avg_rating, count = result if result else (None, 0)
        return (round(float(avg_rating), 2) if avg_rating is not None else None), count
