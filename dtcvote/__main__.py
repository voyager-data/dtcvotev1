#!/usr/bin/env python3
import logging
import re


from connexion import App
from connexion.resolver import Resolver
from flask_admin import Admin

from dtcvote import ENV
from dtcvote.database import db_connect
from dtcvote.models.orm import init_db
from dtcvote.models.admin import make_admin_if

logger = logging.getLogger('connexion.resolver')


class RestyResolver(Resolver):
    """
    connexion's RestyResolver is bugged, so we define it here until the patch is merged.
    Resolves endpoint functions using REST semantics (unless overridden by specifying operationId)
    """

    def __init__(self, default_module_name, collection_endpoint_name='search'):
        """
        :param default_module_name: Default module name for operations
        :type default_module_name: str
        """
        Resolver.__init__(self)
        self.default_module_name = default_module_name
        self.collection_endpoint_name = collection_endpoint_name

    def resolve_operation_id(self, operation):
        """
        Resolves the operationId using REST semantics unless explicitly configured in the spec

        :type operation: connexion.operations.AbstractOperation
        """
        if operation.operation_id:
            return Resolver.resolve_operation_id(self, operation)

        return self.resolve_operation_id_using_rest_semantics(operation)

    def resolve_operation_id_using_rest_semantics(self, operation):
        """
        Resolves the operationId using REST semantics

        :type operation: connexion.operations.AbstractOperation
        """
        fragments = operation.path.split('/')[1:]
        path_match = {
            'resource_name': '.'.join(filter(lambda fragment: not re.match(r'^{[^}]*}', fragment), fragments)),
            'extended_path': fragments[-1] if re.match(r'^{[^}]*}', fragments[-1]) else None,
        }

        def get_controller_name():
            x_router_controller = operation.router_controller

            name = self.default_module_name
            resource_name = path_match.get('resource_name')

            if x_router_controller:
                name = x_router_controller

            elif resource_name:
                resource_controller_name = resource_name.replace('-', '_')
                name += '.' + resource_controller_name

            return name

        def get_function_name():
            method = operation.method

            is_collection_endpoint = \
                method.lower() == 'get' \
                and path_match.get('resource_name', None) \
                and not path_match.get('extended_path', None)

            return self.collection_endpoint_name if is_collection_endpoint else method.lower()

        return '{}.{}'.format(get_controller_name(), get_function_name())


def main():
    # app = Flask(__name__)
    app = App(__name__, specification_dir='./openapi/', debug=(ENV == 'dev'))
    # app.json_encoder = encoder.JSONEncoder
    app.app.config.from_pyfile('config.py')
    app.app.db_session = db_connect()
    app.app.teardown_appcontext(lambda e: app.app.db_session.remove())

    # app.register_blueprint(bp_api_v1.bp)

    app.add_api('openapi.yaml',
                arguments={'title': 'DTC-Vote'},
                pythonic_params=True,
                validate_responses=True,
                strict_validation=True,
                resolver=RestyResolver('dtcvote.controllers'),
                )

    make_admin_if(app.app, __name__)

    app.run(port=80)


if __name__ == '__main__':
    if ENV == 'dev':
        init_db()
    main()
