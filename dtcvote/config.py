from os import getenv

SQLALCHEMY_DATABASE_URI = getenv("SQLALCHEMY_DATABASE_URI",
                                 "postgresql+psycopg2://db/")
SECRET_KEY = 'x'
FLASK_ADMIN_SWATCH = 'cerulean'
# SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://user:password@host:port/dbname[?key=value&key=value...]"
