import logging

from flask import request
from flask_restplus import Resource
from mongoengine.queryset import DoesNotExist
from tipi_backend.api.restplus import api
from tipi_backend.api.business import get_deputies, get_deputy

log = logging.getLogger(__name__)

ns = api.namespace('deputies', description='Operations related to deputies')


@ns.route('/')
class DeputiesCollection(Resource):

    def get(self):
        """Returns list of active deputies."""
        return get_deputies()


@ns.route('/<id>')
@ns.param(name='id', description='Identifier', type=str, required=True, location=['path'], help='Invalid identifier')
@ns.param(name='id', description='Identifier', type=str, required=True, location=['path'], help='Invalid identifier')
@api.response(404, 'Deputy not found.')
class DeputyItem(Resource):

    def get(self, id):
        """Returns details of a deputy."""
        try:
            return get_deputy(id)
        except:
            raise(DoesNotExist)
