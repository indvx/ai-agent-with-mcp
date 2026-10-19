"""Alembic migration environment configuration for offline and online schema migrations."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from database import Base, SQLALCHEMY_DATABASE_URL, create_engine
# Import all models so Base.metadata is fully populated for autogenerate detection
from sql.models.permission import Permission
from sql.models.refresh_tokens import RefreshToken
from sql.models.role import Role
from sql.models.user_roles import UserRoles
from sql.models.users import User
from alembic import context
import os

# Alembic Config object providing access to alembic.ini values
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata

print(print(Base.metadata.tables.keys()))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode without an active database connection."""
    url = config.get_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with an established engine connection."""
    connectable = create_engine(SQLALCHEMY_DATABASE_URL)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

