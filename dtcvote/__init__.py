from logging.config import dictConfig
from os import getenv

ENV = getenv("DTC_ENVIRONMENT", "dev")

if ENV == 'dev':
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': 'WARNING',
            'handlers': ['wsgi']
        }
    })
