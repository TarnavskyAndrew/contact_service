from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from src.database.models import Base 
from src.conf.config import settings

# Alembic Config object (reads alembic.ini)
config = context.config

# Override database URL from settings
config.set_main_option("sqlalchemy.url", settings.sync_db_url)

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata (SQLAlchemy models) for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    
    """
    Run migrations in 'offline' mode.

    - Uses a database URL (no actual DB connection).
    - Generates SQL scripts instead of applying directly.
    - Suitable for environments without DB access.

    Example::

        alembic upgrade head --sql
    """
    
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    
    """
    Run migrations in 'online' mode.

    - Creates a database engine and opens a connection.
    - Applies migrations directly to the database.

    Example::

        alembic upgrade head
    """
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        
        with context.begin_transaction():
            context.run_migrations()


# Entrypoint: detect mode and run migrations
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
