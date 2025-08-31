import json
from django import template
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter(name='jsonify')
def jsonify(object):
    return json.dumps(object, cls=DjangoJSONEncoder)
