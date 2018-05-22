import marshmallow_mongoengine as ma
from tipi_backend.database.models.topic import Topic


class TagsField(ma.fields.Field):
    def _serialize(self, value, attr, obj):
        return [{'subtopic': v['subtopic'], 'tag': v['tag']} for v in value]


class TopicSchema(ma.ModelSchema):
    class Meta:
        model = Topic
        model_fields_kwargs = {
                'tags': {'load_only': True}
                }


class TopicExtendedSchema(ma.ModelSchema):
    class Meta:
        model = Topic
    tags = TagsField(attribute="tags")
