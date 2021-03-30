from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask import Flask
from dtcvote.models.orm import Algorithm, Ballot, Candidate, Election, Question, Voter
from typing import NoReturn


def make_admin_if(app: Flask, name: str) -> NoReturn:
    admin = Admin(app, name=name,) #template_mode='bootstrap3')
    [admin.add_view(ModelView(x, app.db_session)) for x in (Algorithm, Ballot, Candidate, Election, Question, Voter)]
