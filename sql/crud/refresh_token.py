from sqlalchemy.orm import Session
from sql.models import refresh_tokens as refresh_token_model


def get_token_by_jti_or_user_id(
    db: Session, jti: str = None, user_id: int = None, revoked: bool = False
) -> refresh_token_model.RefreshToken:
    print(f"Getting token with jti: {jti}, user_id: {user_id}, revoked: {revoked}")
    query = db.query(refresh_token_model.RefreshToken)
    if jti:
        query = query.filter(refresh_token_model.RefreshToken.jti == jti)
    elif user_id:
        query = query.filter(refresh_token_model.RefreshToken.user_id == user_id)

    token = query.filter(refresh_token_model.RefreshToken.revoked == revoked).first()
    return token


def create_or_update_refresh_token(
    db: Session,
    user_id: int,
    jti: str = None,
    token: str = None,
    expires_at=None,
    revoked: bool = False,
) -> refresh_token_model.RefreshToken:
    refresh_token = get_token_by_jti_or_user_id(db, user_id=user_id, revoked=False)
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
