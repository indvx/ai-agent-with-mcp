from sqlalchemy.orm import Session
from sql.models import refresh_tokens as refresh_token_model
from datetime import timezone, datetime


def get_token_by_jti_or_user_id(
    db: Session, jti: str = None, user_id: int = None, revoked: bool = None
) -> refresh_token_model.RefreshToken:
    query = db.query(refresh_token_model.RefreshToken)
    if jti:
        query = query.filter(refresh_token_model.RefreshToken.jti == jti)
    elif user_id:
        query = query.filter(refresh_token_model.RefreshToken.user_id == user_id)

    if revoked is not None:
        query = query.filter(refresh_token_model.RefreshToken.revoked == revoked)
    token = query.first()
    return token


def create_or_update_refresh_token(
    db: Session,
    user_id: int,
    jti: str = None,
    token: str = None,
    expires_at=None,
    revoked: bool = False,
) -> refresh_token_model.RefreshToken:
    refresh_token = get_token_by_jti_or_user_id(db, user_id=user_id)
    if refresh_token:
        if jti != "" or jti is not None:
            refresh_token.jti = jti
        if token != "" or token is not None:
            refresh_token.token = token
        if expires_at is not None:
            refresh_token.expires_at = expires_at
        if revoked is not None:
            refresh_token.revoked = revoked
        db.commit()

    else:
        refresh_token = refresh_token_model.RefreshToken(
            user_id=user_id,
            jti=jti,
            token=token,
            expires_at=expires_at,
            revoked=revoked,
        )

    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def is_refresh_token_expired(refresh_token: refresh_token_model.RefreshToken) -> bool:
    expires_at = refresh_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at = expires_at.astimezone(timezone.utc)

    return expires_at < datetime.now(timezone.utc)
