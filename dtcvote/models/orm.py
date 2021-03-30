import datetime
from collections import OrderedDict, namedtuple
from typing import Dict, Iterable, List, NoReturn, Set, Text, Tuple, Union

from dtcvote.config import SQLALCHEMY_DATABASE_URI
from dtcvote.database import (
    commit_or_rollback,
    db_del,
    db_exec,
    db_get_by_id,
    db_insert,
)
from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Identity,
    MetaData,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy import delete
from sqlalchemy import delete as sql_delete
from sqlalchemy import inspect, select, update
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, JSONB, NUMERIC, UUID, array
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import declarative_base, deferred, registry, relationship
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.sql.expression import Select, Update, func, text
from sqlalchemy.types import Boolean, Integer, Unicode

Base = declarative_base()

from flask import current_app


class BasicMixin(object):
    """
    Base rows and methods for all tables.

    Attrs:
        ID: The ID of the Election.
        created_dt: The created_dt of the Election.
    # @declared_attr
    # def __tablename__(cls):
    #     return cls.__name__.lower()

    # __table_args__ = {'mysql_engine': 'InnoDB'}
    # __mapper_args__= {'always_refresh': True}
    """

    ID = Column(Integer, Identity(start=1), primary_key=True)
    created_dt = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
    )

    public_cols = set()
    dir_cols = {"ID", "created_dt", "deleted_dt"}
    ChildRel = namedtuple("ChildRel", ("parent_col", "child_cls", "child_dicts"))

    def dict_from_colset(self, listing: bool = False, random: bool = False) -> Dict:
        cols = self.dir_cols if listing else self.public_cols
        out = dict()
        for colname in cols:
            val = getattr(self, colname)
            if isinstance(val, (datetime.datetime, datetime.date)):
                out[colname] = val.isoformat()
            elif (
                isinstance(val, list)
                and len(val) > 0
                and isinstance(val[0], BasicMixin)
            ):
                out[colname] = [x.dict_from_colset(listing) for x in val]
            elif val is not None:
                current_app.logger.warning(colname)
                current_app.logger.warning(out)
                current_app.logger.warning(val)
                out[colname] = val
        return out

    @classmethod
    def from_dict(cls, d):
        r_cols = [
            cls.ChildRel(k, v.entity.class_, d.pop(k, []))
            for k, v in cls.__mapper__.relationships.items()
        ]
        obj = cls(**d)
        for r in r_cols:
            if len(r.child_dicts) > 0:
                children = [r.child_cls.from_dict(c) for c in r.child_dicts]
                setattr(obj, r.parent_col, children)
        return obj

    @classmethod
    def search(cls) -> List[Dict]:  # noqa: E501
        """get

        Returns all table rows from the system that the user has access to  # noqa: E501
        """
        x = select(cls)
        x = db_exec(x).unique().scalars()
        # current_app.logger.warning([y.__dict__ for y in x])
        response = [y.dict_from_colset(listing=True) for y in x]
        return response

    @classmethod
    def post(
        cls, request: List[dict], dry_run: bool = False
    ) -> List[dict]:  # noqa: E501
        """post

        Creates new records

        :param request: Pets to add to the store
        :param dry_run: Validate but don&#39;t actually do it
        """
        new_rows = [cls.from_dict(d) for d in request]
        inserted = db_insert(new_rows)
        response = [e.dict_from_colset(listing=False) for e in inserted]
        commit_or_rollback(dry_run)
        return response

    @classmethod
    def get(cls, ID: int) -> Union[dict, NoReturn]:
        """get

        Returns a row based on a single ID

        :param ID: ID of pet to fetch
        """
        x = db_get_by_id(cls, ID)
        response = x.dict_from_colset(listing=False) if x else None
        return response

    @classmethod
    def delete(
        cls, ID: int, dry_run: bool = False
    ) -> Union[NoReturn, Tuple]:  # noqa: E501
        """delete

        marks for deletion a single row and any one-to-many children
        based on the ID supplied

        :param ID: ID of pet to fetch
        :param dry_run: Validate but don&#39;t actually do it
        """
        stmt = sql_delete(cls).where(cls.ID == ID)
        if db_exec(stmt):
            commit_or_rollback(dry_run)
            return None
        else:
            return 404


class Election(BasicMixin, Base):
    """
    SQLAlchemy model protocol.

    Attrs:
        name: The name of the Election.
        deadline: The deadline of the Election.
        vote_email: The vote_email of the Election.
        voted_email: The voted_email of the Election.
        not_voted_email: The not_voted_email of the Election.
        opened: The opened of the Election.
        closed: The closed of the Election.
        secret_ballot: The secret_ballot of the Election.
        questions: The questions of the Election.
        ballots: The ballots of the Election.
        voters: The voters of the Election.

    """

    __tablename__ = "election"

    name = Column(Unicode, nullable=False)
    deadline = Column(TIMESTAMP(timezone=True))
    vote_email = deferred(Column(Unicode))
    voted_email = deferred(Column(Unicode))
    not_voted_email = deferred(Column(Unicode))
    opened = Column(TIMESTAMP(timezone=True))
    closed = Column(TIMESTAMP(timezone=True))
    secret_ballot = Column(Boolean)
    uuid = Column(UUID)
    secret_number = Column(NUMERIC(precision=78, scale=0))
    manifest = Column(JSONB)
    results = Column(ARRAY(JSONB, dimensions=1))
    questions = relationship(
        "Question", backref="election", lazy="joined", order_by="Question.sequence"
    )
    ballots = relationship("Ballot", backref="election")
    voters = association_proxy("election_voters", "voter")

    public_cols = {
        "ID",
        "created_dt",
        "name",
        "deadline",
        "vote_email",
        "voted_email",
        "not_voted_email",
        "opened",
        "closed",
        "secret_ballot",
        "results",
        "questions",
    }
    dir_cols = {
        "ID",
        "created_dt",
        "name",
        "deadline",
        "opened",
        "secret_ballot",
        "results",
    }

    def voters_for_election(self, only_new: bool = False):
        if only_new:
            stmt = select(Voter).where(
                ElectionVoter.created_dt > self.opened
                and ElectionVoter.election_id == self.ID
            )
            voters = db_exec(stmt).scalar()
        else:
            voters = self.voters
        return [v.dict_from_colset() for v in voters]

    @classmethod
    def put(cls, ID: int, request: dict, dry_run: bool = False):
        """elections_id_put

        Replace an election record. Returns an error if voting has been opened.

        :param ID: ID of pet to fetch
        :param request: Updated election record
        :param dry_run: Validate but don&#39;t actually do it
        """
        questions = request.pop("questions")
        election = db_get_by_id(cls, ID)
        if not election:
            return 404
        elif election.opened:
            return 418
        else:
            stmt = delete(Question).where(Question.election_id == ID)
            db_exec(stmt)
            for k, v in request.items():
                setattr(election, k, v)
            response = election.dict_from_colset(listing=False)
            response["questions"] = [Question.post(d, dry_run)[0] for d in questions]
            return response


class Voter(BasicMixin, Base):
    """
    SQLAlchemy model protocol.

    Attrs:
        uuid: The uuid of the Voter.
        elections: The elections of the Voter.
        name: The name of the Voter.
        email: The email of the Voter.

    """

    __tablename__ = "voter"
    # Model properties
    uuid = Column(
        UUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    name = Column(Unicode, nullable=False)
    email = Column(Unicode, nullable=False)
    elections = association_proxy("election_voters", "election")

    public_cols = {
        "ID",
        "created_dt",
        "name",
        "email",
        "uuid",
    }
    dir_cols = {
        "ID",
        "created_dt",
        "name",
        "email",
    }


class ElectionVoter(Base):
    """
    Many to many table connecting Elections and Voters

    Attrs:
        election_id: FK to Election
        voter_id: FK to Voter.
        created_dt: The created_dt of the ElectionVoter.
    """

    __tablename__ = "election_voter"

    # Model properties
    election_id = Column(
        Integer, ForeignKey("election.ID", ondelete="CASCADE"), primary_key=True
    )
    voter_id = Column(
        Integer, ForeignKey("voter.ID", ondelete="CASCADE"), primary_key=True
    )
    created_dt = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
    )
    election = relationship(Election, backref="election_voters")
    voter = relationship(Voter, backref="election_voters")


class Algorithm(BasicMixin, Base):
    """
    SQLAlchemy model protocol.

    Attrs:
        ID: The ID of the Algorithm.
        created_dt: The created_dt of the Algorithm.
        name: The name of the Algorithm.
        description: The description of the Algorithm
    """

    __tablename__ = "algorithm"

    name = Column(Unicode, nullable=False)
    description = Column(Unicode, nullable=False)
    instructions = Column(Unicode, nullable=False)

    public_cols = {"ID", "created_dt", "name", "description", "instructions"}
    dir_cols = {"ID", "created_dt", "name", "description"}


class Question(BasicMixin, Base):
    """
    SQLAlchemy model protocol.

    Attrs:
        election: The election of the Question.
        name: The name of the Question.
        algorithm: The algorithm of the Question.
        randomize_candidates: The randomize_candidates of the Question.
        number_of_winners: The number_of_winners of the Question.
        candidates: The candidates of the Question.
    """

    # Table properties
    __tablename__ = "question"
    __table_args__ = (UniqueConstraint("election_id", "sequence"),)

    # Model properties
    election_id = Column(
        Integer, ForeignKey("election.ID", ondelete="CASCADE"), nullable=False
    )
    algorithm_id = Column(Integer, ForeignKey("algorithm.ID"))
    sequence = Column(Integer, nullable=False)
    name = Column(Unicode, nullable=False)
    randomize_candidates = Column(Boolean, nullable=False, server_default=text("False"))
    number_of_winners = Column(Integer, nullable=False, server_default=text("1"))
    algorithm = relationship("Algorithm", lazy="joined")
    candidates = relationship(
        "Candidate", backref="question", lazy="joined", order_by="Candidate.sequence"
    )

    public_cols = {
        "ID",
        "created_dt",
        "algorithm_id",
        "sequence",
        "name",
        "randomize_candidates",
        "number_of_winners",
        "candidates",
    }
    dir_cols = {
        "ID",
        "created_dt",
        "sequence",
        "name",
    }


class Candidate(BasicMixin, Base):
    """
    SQLAlchemy model protocol.

    Attrs:
        sequence: The sequence of the Candidate.
        question_id: The question of the Candidate.
        name: The name of the Candidate.

    """

    # Table properties
    __tablename__ = "candidate"
    __table_args__ = (UniqueConstraint("question_id", "sequence"),)

    # Model properties
    question_id = Column(Integer, ForeignKey("question.ID", ondelete="CASCADE"))
    sequence = Column(Integer, nullable=False)
    name = Column(Unicode, nullable=False)
    party_id = Column(Integer, ForeignKey("party.ID"))
    party = relationship("Party")

    public_cols = {"ID", "created_dt", "sequence", "name"}
    dir_cols = {
        "ID",
        "created_dt",
        "sequence",
        "name",
    }


class Party(BasicMixin, Base):
    """
    SQLAlchemy model protocol.

    Attrs:
        sequence: The sequence of the Candidate.
        question_id: The question of the Candidate.
        name: The name of the Candidate.

    """

    # Table properties
    __tablename__ = "party"

    # Model properties
    sequence = Column(Integer, nullable=False)
    name = Column(Unicode, nullable=False)

    public_cols = {"ID", "created_dt", "sequence", "name"}
    dir_cols = {
        "ID",
        "created_dt",
        "sequence",
        "name",
    }


class Ballot(BasicMixin, Base):
    """
    SQLAlchemy model protocol.

    Attrs:
        uuid: The uuid of the Ballot.
        ballot_content: The ballot_content of the Ballot.
        voted_on: Array of timestamps, from earliest to latest vote. Initializes to empty array.
        voted: Array of encrypted ballots, from earliest to latest vote. Initializes to empty array.
        signature: The signature of the Ballot.
        election: The election of the Ballot.

    """

    __tablename__ = "ballot"

    # Model properties
    election_id = Column(Integer, ForeignKey("election.ID"), nullable=False)
    uuid = Column(
        UUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    ballot_content = Column(BYTEA, nullable=False)
    voted_on = Column(
        ARRAY(TIMESTAMP(timezone=True), dimensions=1),
        server_default=text("ARRAY[]::timestamptz[]"),
    )
    votes = Column(ARRAY(BYTEA, dimensions=1), server_default=text("ARRAY[]::bytea[]"))
    signature = Column(Unicode)

    public_cols = {"ID", "created_dt", "uuid", "voted_on", "signature"}


def init_db():
    db_engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True, future=True)
    Base.metadata.create_all(db_engine)
