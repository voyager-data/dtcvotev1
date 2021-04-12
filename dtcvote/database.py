from contextlib import contextmanager
from threading import get_ident
from typing import ClassVar, NoReturn, Sequence

from flask import current_app
from psycopg2 import Error as DbError
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Result
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql.expression import Executable

from dtcvote.config import SQLALCHEMY_DATABASE_URI

db_engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True, future=True)
LocalSession = sessionmaker(
    bind=db_engine, autoflush=False, autocommit=False, future=True
)


def db_connect() -> scoped_session:
    """
    Connect to the database and return a thread-local session
    """
    return scoped_session(LocalSession, scopefunc=get_ident)


def db_exec(stmt: Executable) -> Result:
    """
    Execute an orm expression against the db.
    """
    return current_app.db_session.execute(stmt)


def db_insert(models: Sequence) -> Sequence:
    """
    Insert rows into the database within the thread's current transaction.
    """
    current_app.db_session.add_all(models)
    current_app.db_session.flush()
    return models


def db_get_by_id(cls, ID):
    return current_app.db_session().get(cls, ID)


def db_get_by_uuid(cls, uuid):
    return (
        current_app.db_session()
        .execute(select(cls).where(getattr(cls, "uuid") == uuid))
        .scalar()
    )


def db_del(obj):
    return current_app.db_session.delete(obj)


def db_flush():
    return current_app.db_session.flush()


def commit_or_rollback(rollback: bool) -> NoReturn:
    """
    Commit or roll back the thread's current transaction
    based on whether it's a dry run

    Params:
        dry_run bool: Whether this is a dry run or not
    """
    if rollback:
        current_app.db_session.rollback()
    else:
        try:
            current_app.db_session.commit()
        except DbError:
            current_app.db_session.close()
