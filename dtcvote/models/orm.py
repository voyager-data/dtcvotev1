import datetime
from collections import OrderedDict, namedtuple
from turtle import st
from typing import Dict, Iterable, List, NoReturn, Set, Text, Tuple, Union
from unicodedata import name
from itertools import permutations
from dtcvote.config import SQLALCHEMY_DATABASE_URI
from dtcvote.database import commit_or_rollback, db_del, db_exec, db_flush, db_get_by_id, db_get_by_uuid, db_insert, db_connect
from flask import current_app
from sqlalchemy import Column, ForeignKey, Identity, MetaData, UniqueConstraint, create_engine
from sqlalchemy import delete as sql_delete
from sqlalchemy import inspect, select, update
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, JSONB, NUMERIC, UUID, TIMESTAMP, array
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import declarative_base, deferred, registry, relationship
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.sql.expression import Select, Update, func, text
from sqlalchemy.types import Boolean, Integer, Unicode
from dill import dumps, loads

Base = declarative_base()


class BasicMixin(object):
    """
    Base rows and methods for all tables.

    Attrs:
        id: The id of the Election.
        created_dt: The created_dt of the Election.
    # @declared_attr
    # def __tablename__(cls):
    #     return cls.__name__.lower()

    # __table_args__ = {'mysql_engine': 'InnoDB'}
    # __mapper_args__= {'always_refresh': True}
    """

    id = Column(Integer, Identity(start=1), primary_key=True)
    created_dt = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.CURRENT_TIMESTAMP(),
    )

    public_cols: Set[str] = set()
    dir_cols = {"id", "created_dt", "deleted_dt"}
    ChildRel = namedtuple("ChildRel", ("parent_col", "child_cls", "child_dicts"))

    def dict_from_colset(self, listing: bool = False) -> Dict:
        cols = self.dir_cols if listing else self.public_cols
        out = dict()
        for colname in cols:
            val = getattr(self, colname)
            if isinstance(val, (datetime.datetime, datetime.date)) and val:
                out[colname] = val.isoformat()
            elif (
                isinstance(val, list)
                and len(val) > 0
                and isinstance(val[0], BasicMixin)
            ):
                out[colname] = [x.dict_from_colset(listing) for x in val]
            elif val is not None:
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
    def get(cls, id: int) -> Union[dict, NoReturn]:
        """get

        Returns a row based on a single id

        :param id: id of pet to fetch
        """
        x = db_get_by_id(cls, id)
        response = x.dict_from_colset(listing=False) if x else None
        return response

    @classmethod
    def delete(
        cls, id: int, dry_run: bool = False
    ) -> Union[NoReturn, Tuple]:  # noqa: E501
        """delete

        marks for deletion a single row and any one-to-many children
        based on the id supplied

        :param id: id of pet to fetch
        :param dry_run: Validate but don&#39;t actually do it
        """
        stmt = sql_delete(cls).where(cls.id == id)
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
    timezone = Column(Unicode, default='America/New York')
    uuid = Column(UUID)
    secret_number = Column(NUMERIC(precision=78, scale=0))
    manifest = deferred(Column(JSONB))
    pickle_jar = deferred(Column(BYTEA))
    pickle_box = deferred(Column(BYTEA))
    results = deferred(Column(ARRAY(JSONB, dimensions=1)))
    questions = relationship(
        "Question", backref="election", lazy="joined", order_by="Question.sequence"
    )
    ballots = relationship("Ballot", backref="election")
    voters = association_proxy("election_voters", "voter")

    public_cols = {
        "id",
        "created_dt",
        "name",
        "deadline",
        "vote_email",
        "voted_email",
        "not_voted_email",
        "timezone",
        "opened",
        "closed",
        "secret_ballot",
        "results",
        "questions",
    }
    dir_cols = {
        "id",
        "created_dt",
        "name",
        "deadline",
        "opened",
        "secret_ballot",
        "results",
    }

    def voters_for_election(self, only_new: bool = False, as_dict: bool=False):
        if only_new:
            stmt = select(Voter).join(ElectionVoter).where(
                ElectionVoter.created_dt > self.opened,
                ElectionVoter.election_id == self.id
            )
            voters = db_exec(stmt).scalars()
        else:
            voters = self.voters
        if as_dict:
            return [v.dict_from_colset() for v in voters]
        else:
            return voters if voters and len(voters) > 0 else None


    @classmethod
    def put(cls, id: int, request: dict, dry_run: bool = False):
        """elections_id_put

        Replace an election record. Returns an error if voting has been opened.

        :param id: id of pet to fetch
        :param request: Updated election record
        :param dry_run: Validate but don&#39;t actually do it
        """
        questions = request.pop("questions")
        election = db_get_by_id(cls, id)
        if not election:
            return 404
        elif election.opened:
            return 418
        else:
            stmt = sql_delete(Question).where(Question.election_id == id)
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
        "id",
        "created_dt",
        "name",
        "email",
        "uuid",
    }
    dir_cols = {
        "id",
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
        Integer, ForeignKey("election.id", ondelete="CASCADE"), primary_key=True
    )
    voter_id = Column(
        Integer, ForeignKey("voter.id", ondelete="CASCADE"), primary_key=True
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
        id: The id of the Algorithm.
        created_dt: The created_dt of the Algorithm.
        name: The name of the Algorithm.
        description: The description of the Algorithm
    """

    __tablename__ = "algorithm"

    name = Column(Unicode, nullable=False)
    description = Column(Unicode, nullable=False)
    instructions = Column(Unicode, nullable=False)

    public_cols = {"id", "created_dt", "name", "description", "instructions"}
    dir_cols = {"id", "created_dt", "name", "description"}


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
        Integer, ForeignKey("election.id", ondelete="CASCADE"), nullable=False
    )
    algorithm_id = Column(Integer, ForeignKey("algorithm.id"))
    sequence = Column(Integer, nullable=False)
    name = Column(Unicode, nullable=False)
    randomize_candidates = Column(Boolean, nullable=False, server_default=text("False"))
    number_of_winners = Column(Integer, nullable=False, server_default=text("1"))
    algorithm = relationship("Algorithm", lazy="joined")
    candidates = relationship(
        "Candidate", backref="question", lazy="joined", order_by="Candidate.sequence"
    )

    public_cols = {
        "id",
        "created_dt",
        "algorithm_id",
        "sequence",
        "name",
        "randomize_candidates",
        "number_of_winners",
        "candidates",
    }
    dir_cols = {
        "id",
        "created_dt",
        "sequence",
        "name",
    }

    def blt(self):
        election_id = self.election.id
        question_seq = self.sequence
        number_of_candidates = len(self.candidates)
        stmt = select(Ballot).where(Ballot.election_id == election_id)
        ballots = db_exec(stmt).scalars()
        blt_string = f"{number_of_candidates} {self.number_of_winners}\n"
        # count = {p: 0 for p in permutations(range(1, number_of_candidates+1), number_of_candidates)}
        count = dict()


        for b in ballots:
            votes = loads(b.votes[-1])
            # this is a list of dict
            votes_this_q = [v for v in votes if v.get("question_seq") == question_seq]
            this_blt_key = tuple(v["candidate_seq"] for v in sorted(votes_this_q, key=lambda k: k["rank"]))
            if this_blt_key in count.keys():
                count[this_blt_key] += 1
            else:
                count[this_blt_key] = 1

        for k, v in count.items():
            blt_string += f"{str(v)} {' '.join([str(n) for n in k])} 0\n"

        blt_string += "0\n"
        for c in self.candidates:
            blt_string += f"\"{c.name}\"\n"
        blt_string += f"\"{self.name}\"\n"
        current_app.logger.warning(blt_string)
        return blt_string




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
    question_id = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"))
    sequence = Column(Integer, nullable=False)
    name = Column(Unicode, nullable=False)
    party_id = Column(Integer, ForeignKey("party.id"))
    party = relationship("Party")

    public_cols = {"id", "created_dt", "sequence", "name"}
    dir_cols = {
        "id",
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

    public_cols = {"id", "created_dt", "sequence", "name"}
    dir_cols = {
        "id",
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
    election_id = Column(Integer, ForeignKey("election.id"), nullable=False)
    secret_phrase = Column(Unicode)
    uuid = Column(
        UUID(as_uuid=True), nullable=False, server_default=func.gen_random_uuid()
    )
    ballot_content = Column(BYTEA, nullable=False)
    voted_on = Column(
        ARRAY(TIMESTAMP(timezone=True), dimensions=1, as_tuple=True),
        server_default=text("ARRAY[]::timestamptz[]",),
    )
    votes = Column(ARRAY(BYTEA, dimensions=1, as_tuple=True), server_default=text("ARRAY[]::bytea[]"))
    signature = Column(Unicode)

    public_cols = {"id", "created_dt", "uuid", "voted_on", "signature"}

    @classmethod
    def get(cls, uuid):
        b = db_get_by_uuid(Ballot, uuid)
        return b.serialize_response() if b else 404

    @classmethod
    def put(cls, uuid, votes, dry_run):
        b = db_get_by_uuid(Ballot, uuid)
        if b:
            # request is a list of dicts with keys 'question_seq', 'candidate_seq', and 'rank'
            b.votes = b.votes + (dumps(votes),)
            db_flush()
            # get md5 hash of this vote
            stmt = select(text("encode(digest(votes[array_length(votes, 1)], 'md5'::text), 'hex')")).where(Ballot.uuid == b.uuid)
            b.signature = db_exec(stmt).scalar()
            b.voted_on = b.voted_on + array((text("CURRENT_TIMESTAMP"),))
            db_flush()
            response = b.serialize_response()
            commit_or_rollback(dry_run)
            return response
        else:
            return 418

    def serialize_response(self):
        response = dict(created_dt=self.created_dt,
                secret_phrase=self.secret_phrase,
                signature=self.signature,
                voted_on=self.voted_on,
                ballot_content=loads(self.ballot_content),
                votes=[loads(v) for v in self.votes],
                )
        return {k: v for k, v in response.items() if v is not None}



def init_db():
    db_engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True, future=True)
    Base.metadata.create_all(db_engine)
    algs = [Algorithm(name="plurality", description="Traditional first-past-the-post voting. Each voter gets one vote and the candidate with the most votes wins.", instructions="Vote for one candidate."),
            Algorithm(name="majority", description="Same as plurality, but a winner is declared only if a candidate receives >50% of votes cast.", instructions="Vote for one candidate."),
            Algorithm(name="rcv", description="Instant Runoff Ranked Choice Voting", instructions="Rank the candidates according to your preference, with 1 being your most preferred."),
            ]
    election = Election(questions=[Question(candidates=[Candidate(sequence=1, name="Mayela"),
                                                        Candidate(sequence=2, name="Christina"),
                                                        Candidate(sequence=3, name="Nathan"),
                                                        Candidate(sequence=4, name="Monika")
                                                        ],
                                            algorithm_id=3,
                                            name="Who is the fairest one of all?",
                                            number_of_winners=1,
                                            sequence=1,
                                            randomize_candidates=True)
                                    ],
                        deadline="2021-04-28T01:10:08.107Z",
                        name="The Apple of Discord",
                        secret_ballot=False,
                        not_voted_email="you have not voted",
                        vote_email="you must vote",
                        voted_email="you voted"
                        )
    voter = Voter(name="Adam", email="adam@windsordemocrats.com")
    LocalSession = db_connect()
    if not LocalSession.execute(select(Algorithm)).scalar():
        LocalSession.add_all(algs)
    if not LocalSession.execute(select(Voter)).scalar():
        LocalSession.add(voter)
    if not LocalSession.execute(select(Election)).scalar():
        LocalSession.add(election)
        LocalSession.add(ElectionVoter(election_id=1, voter_id=1))
    # LocalSession.execute('create extension pgcrypto;')
    LocalSession.commit()
    LocalSession.close_all()
