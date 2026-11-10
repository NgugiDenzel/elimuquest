from sqlalchemy.engine import Connection

MIGRATION_LOCK_KEYS = (1162627393, 20261109)


def acquire_migration_lock(connection: Connection) -> bool:
    if connection.dialect.name != "postgresql":
        return False
    connection.exec_driver_sql(
        "SELECT pg_advisory_lock(%s, %s)", MIGRATION_LOCK_KEYS
    )
    connection.commit()
    return True


def release_migration_lock(connection: Connection) -> None:
    connection.exec_driver_sql(
        "SELECT pg_advisory_unlock(%s, %s)", MIGRATION_LOCK_KEYS
    )
    connection.commit()
