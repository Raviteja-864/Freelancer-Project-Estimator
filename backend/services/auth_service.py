from datetime import datetime
from extensions import db, bcrypt
from models import User, Profile, RoleEnum, AccountStatusEnum


class AuthService:

    @staticmethod
    def user_exists(email):
        return User.query.filter_by(email=email.strip().lower()).first() is not None

    @staticmethod
    def register_user(name, email, password, role):
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=hashed_pw,
            role=RoleEnum(role),
            account_status=AccountStatusEnum.ACTIVE,
        )
        db.session.add(user)
        db.session.flush()  # get user.id before commit

        # Auto-create an empty profile for the user
        profile = Profile(user_id=user.id)
        db.session.add(profile)

        db.session.commit()
        return user

    @staticmethod
    def authenticate(email, password):
        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user:
            return None, "Invalid email or password"

        if user.account_status != AccountStatusEnum.ACTIVE:
            return None, f"Account is {user.account_status.value}. Contact support."

        if not bcrypt.check_password_hash(user.password_hash, password):
            return None, "Invalid email or password"

        return user, None

    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get(user_id)
