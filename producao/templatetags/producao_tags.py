import json
from django import template
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter(name='jsonify')
def jsonify(object):
    return mark_safe(json.dumps(object, cls=DjangoJSONEncoder))
