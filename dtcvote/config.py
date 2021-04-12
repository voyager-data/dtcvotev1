from os import getenv

SQLALCHEMY_DATABASE_URI = getenv("SQLALCHEMY_DATABASE_URI",
                                 "postgresql+psycopg2://db/")
SECRET_KEY = 'x'
FLASK_ADMIN_SWATCH = 'cerulean'
GUI_URL = 'https://vote.windsordemocrats.com'
EMAIL_FROM = 'Windsor Democrats <adam@windsordemocrats.com>'
# SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://user:password@host:port/dbname[?key=value&key=value...]"
