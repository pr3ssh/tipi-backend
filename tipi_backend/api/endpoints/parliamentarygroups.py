import logging

from flask import request
from flask_restplus import Resource
from mongoengine.queryset import DoesNotExist
from tipi_backend.api.restplus import api
from tipi_backend.api.business import get_parliamentarygroups, get_parliamentarygroup

log = logging.getLogger(__name__)

ns = api.namespace('parliamentarygroups', description='Operations related to parliamentary groups')


@ns.route('/')
class ParliamentaryGroupsCollection(Resource):

    def get(self):
        """Returns list of parliamentary groups."""
        return get_parliamentarygroups()


@ns.route('/<id>')
@ns.param(name='id', description='Identifier', type=str, required=True, location=['path'], help='Invalid identifier')
@api.response(404, 'Parliamentary group not found.')
class ParliamentaryGroupItem(Resource):

    def get(self, id):
        """Returns details of a parliamentary group."""
        try:
            return get_parliamentarygroup(id)
        except:
            raise(DoesNotExist)
