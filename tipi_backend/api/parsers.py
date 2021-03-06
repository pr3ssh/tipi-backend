import datetime

from flask_restplus import reqparse
from tipi_data.models.parliamentarygroup import ParliamentaryGroup
from tipi_data.models.initiative_type import InitiativeType
from tipi_data.schemas.initiative import InitiativeExtendedSchema, InitiativeNoContentSchema, InitiativeSchema

from tipi_backend.api.validators import validate_date


parser_initiatives = reqparse.RequestParser()
# Common parameters
parser_initiatives.add_argument('page', type=int, default=1, location='args', help='Page number')
parser_initiatives.add_argument('per_page', type=int, default=20, location='args', help='Initiatives per page')
# Initiative parameters
parser_initiatives.add_argument('title', type=str, location='args')
parser_initiatives.add_argument('status', type=str, location='args', help='To get the values, check out /initiative-status')
parser_initiatives.add_argument('type', type=str, location='args', help='To get the values, check out /initiative-type')
parser_initiatives.add_argument('reference', type=str, location='args')
parser_initiatives.add_argument('place', type=str, location='args')
parser_initiatives.add_argument('enddate', type=str, location='args', help='Date format must be yyyy-mm-dd')
parser_initiatives.add_argument('startdate', type=str, location='args', help='Date format must be yyyy-mm-dd')
parser_initiatives.add_argument('deputy', type=str, location='args', help='To get the values, check out /deputies')
parser_initiatives.add_argument('author', type=str, location='args', help='To get the values, check out /parliamentary-groups')
parser_initiatives.add_argument('tags', type=str, action='append', location='args', help='To get the values, check out /topics/id')
parser_initiatives.add_argument('subtopics', type=str, action='append', location='args', help='To get the values, check out /topics/id')
parser_initiatives.add_argument('topic', type=str, location='args', help='To get the values, check out /topics')
parser_initiatives.add_argument('serializer', type=str, location='args', help='To choose the fields of the initiative that will be returned. Options: full(default), no-content, simple')

parser_initiative = reqparse.RequestParser()
parser_initiative.add_argument('serializer', type=str, location='args', help='To choose the fields of the initiative that will be returned. Options: full, no-content(default), simple')

parser_stats = reqparse.RequestParser()
parser_stats.add_argument('topic', type=str, required=True, location='args', help='To get the values, check out /topics')
parser_stats.add_argument('subtopic', type=str, location='args', help='To get the values, check out /topics/id')


parser_authors = reqparse.RequestParser()
parser_authors.add_argument('name', type=str, location='args', help='Send a name')


parser_tagger = reqparse.RequestParser()
parser_tagger.add_argument(name='text', type=str, location='form', help='Text to be processed (PREFERENCE)')
parser_tagger.add_argument(name='file', location='files', help='File to be processed')

class SearchInitiativeParser:

    class DefaultFieldParser():
        @staticmethod
        def get_search_for(key, value):
            return {key: value}

    class TitleFieldParser():
        @staticmethod
        def get_search_for(key, value):
            return {key: {'$regex': value, '$options': 'gi'}}

    class TypeFieldParser():
        @staticmethod
        def get_search_for(key, value):
            try:
                code = InitiativeType.objects.get(name=value)['id']
            except Exception:
                code = ''
            return {'initiative_type': code}

    class TopicFieldParser():
        @staticmethod
        def get_search_for(key, value):
            return {'topics': value}

    class CombinedTagsFieldParser():
        @staticmethod
        def get_search_for(key, value):
            if not len(value['tags']) and not len(value['subtopics']):
                return {}
            elem_match = dict()
            if len(value['tags']):
                elem_match.update({'tag': {'$in': value['tags']}})
            if len(value['subtopics']):
                elem_match.update({'subtopic': {'$in': value['subtopics']}})
            return {'tags': {'$elemMatch': elem_match}}

    class AuthorFieldParser():
        @staticmethod
        def get_search_for(key, value):
            if not ParliamentaryGroup.objects(name=value):
                return {'author_others': value}
            return {'author_parliamentarygroups': value}

    class DeputyFieldParser():
        @staticmethod
        def get_search_for(key, value):
            return {'author_deputies': value}

    class CombinedDateFieldParser():
        @staticmethod
        def get_search_for(key, value):
            def parse_date(str_date):
                array_date = str_date.split('-')
                return datetime.datetime(int(array_date[0]), int(array_date[1]), int(array_date[2]), 0, 0, 0, 0)

            date_interval = value.split('_')
            STARTDATE = 0
            ENDDATE = 1
            if date_interval[STARTDATE] == '' and date_interval[ENDDATE] == '':
                return {}
            date_query = {'updated': {}}
            if date_interval[STARTDATE] != '':
                if validate_date(date_interval[STARTDATE]):
                    date_query['updated']['$gte'] = parse_date(date_interval[STARTDATE])
            if date_interval[ENDDATE] != '':
                if validate_date(date_interval[ENDDATE]):
                    date_query['updated']['$lte'] = parse_date(date_interval[ENDDATE])
            return date_query

    PARSER_BY_PARAMS = {
            'topic': TopicFieldParser,
            'tags': CombinedTagsFieldParser,
            'author': AuthorFieldParser,
            'deputy': DeputyFieldParser,
            'date': CombinedDateFieldParser,
            'place': DefaultFieldParser,
            'reference': DefaultFieldParser(),
            'type': TypeFieldParser(),
            'status': DefaultFieldParser(),
            'title': TitleFieldParser(),
            }

    EMPTY_VALUES = ['', None, []]

    def __init__(self, params):
        self._params = params
        self._clean_params()
        self._per_page = self._return_attr_in_params(attrname='per_page', type=int, default=20, clean=True)
        self._page = self._return_attr_in_params(attrname='page', type=int, default=1, clean=True)
        self._serializer = self._return_attr_in_params(attrname='serializer', type=str, default='', clean=True)
        self._join_tags_and_subtopics_in_params()
        self._join_dates_in_params()
        self._parse_params()

    def _clean_params(self):
        for key, value in self._params.copy().items():
            if value in self.EMPTY_VALUES:
                self._clean_params_for_attr(key)

    def _parse_params(self):
        temp_params = self._params.copy()
        for key, value in temp_params.items():
            del self._params[key]
            self._params.update(self.PARSER_BY_PARAMS[key].get_search_for(key, value))

    def _return_attr_in_params(self, attrname='', type=str, default='', clean=False):
        if attrname in self._params:
            attr = self._params[attrname]
            if clean:
                self._clean_params_for_attr(attrname)
            return type(attr)
        return default

    def _clean_params_for_attr(self, attrname=''):
        if attrname in self._params:
            del self._params[attrname]

    def _join_tags_and_subtopics_in_params(self):
        tags = [] if 'tags' not in self._params else self._params['tags']
        subtopics = [] if 'subtopics' not in self._params else self._params['subtopics']
        self._clean_params_for_attr('tags')
        self._clean_params_for_attr('subtopics')
        self._params['tags'] = {
                'tags': tags,
                'subtopics': subtopics
                }

    def _join_dates_in_params(self):
        if 'startdate' not in self._params:
            self._params['startdate'] = ''
        if 'enddate' not in self._params:
            self._params['enddate'] = ''
        self._params['date'] = "{}_{}".format(
                self._params['startdate'],
                self._params['enddate']
                )
        self._clean_params_for_attr('startdate')
        self._clean_params_for_attr('enddate')

    @property
    def per_page(self):
        return self._per_page

    @property
    def page(self):
        return self._page

    @property
    def params(self):
        return self._params

    @property
    def serializer(self):
        if self._serializer == 'full':
            return InitiativeExtendedSchema
        if self._serializer == 'no-content':
            return InitiativeNoContentSchema
        return InitiativeSchema

class InitiativeParser():
    def __init__(self, params):
        self._params = params
        self._serializer = self._return_attr_in_params(attrname='serializer', type=str, default='')

    @property
    def serializer(self):
        if self._serializer == 'simple':
            return InitiativeSchema
        if self._serializer == 'full':
            return InitiativeExtendedSchema
        return InitiativeNoContentSchema

    def _return_attr_in_params(self, attrname='', type=str, default=''):
        if attrname in self._params:
            attr = self._params[attrname]
            return type(attr)
        return default
