from django import template
from oscar.core.loading import feature_hidden

register = template.Library()


@register.simple_tag(takes_context=True)
def get_parameters(context, except_field):
    """
    Renders current get parameters except for the specified parameter
    """
    getvars = context['request'].GET.copy()
    getvars.pop(except_field, None)
    return f"{getvars.urlencode()}&" if len(getvars.keys()) > 0 else ''


@register.tag()
def iffeature(parser, token):
    nodelist = parser.parse(('endiffeature',))
    try:
        tag_name, app_name, = token.split_contents()
    except ValueError as e:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        ) from e
    if app_name[0] != app_name[-1] or app_name[0] not in ('"', "'"):
        raise template.TemplateSyntaxError(
            "%r tag's argument should be in quotes" % tag_name)
    parser.delete_first_token()
    return ConditionalOutputNode(nodelist, app_name[1:-1])


class ConditionalOutputNode(template.Node):
    def __init__(self, nodelist, feature_name):
        self.nodelist = nodelist
        self.feature_name = feature_name

    def render(self, context):
        return '' if feature_hidden(self.feature_name) else self.nodelist.render(context)
