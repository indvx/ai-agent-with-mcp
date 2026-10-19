from sqlalchemy.orm import Session
from sql.models import users as user_model, role as role_model
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def verify_password(plain_password, hashed_password):
    """Verifies a plaintext password against an Argon2/bcrypt hash."""
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Hashes a plaintext password using the recommended algorithm."""
    return password_hash.hash(password)


def get_user(db: Session, email: str):
    """Retrieves a user record matching the given email address."""
    return db.query(user_model.User).filter(user_model.User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    """Retrieves a user record matching the primary key ID."""
    return db.query(user_model.User).filter(user_model.User.id == user_id).first()


def create_user(
    db: Session, data: dict, default_role: role_model.Role = None
) -> user_model.User:
    """Inserts a new user record with hashed password and assigns their default role."""
    user = user_model.User(
        full_name=data.get("full_name", "test"),
    )
    user.email = data["email"]
    user.password_hash = get_password_hash(data["password"])
    user.full_name = data["full_name"]
    user.is_active = True
    user.is_verified = True

    if default_role:
        user.roles.append(default_role)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_users(db: Session, page: int = 1, limit: int = 100):
    """Fetches a paginated slice of user records and metadata."""
    query = db.query(user_model.User)

    total_items = query.count()

    if page and page > 0:
        skip = (page - 1) * limit
        query = query.offset(skip).limit(limit)

    users = query.all()
    meta = {
        "limit": limit,
        "page": page,
        "total_items": total_items,
        "current_items": len(users),
    }
    return {"users": users, "meta": meta}


def delete_user(db: Session, user_id: int) -> bool:
    """Deletes a user record by ID. Returns True if found and deleted, otherwise False."""
    user = get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
