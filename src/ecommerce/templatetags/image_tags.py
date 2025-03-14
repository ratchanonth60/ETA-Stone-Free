import logging
import re

from django import template
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile
from django.utils.encoding import smart_str
from django.utils.html import escape
from oscar.core.thumbnails import get_thumbnailer

register = template.Library()
kw_pat = re.compile(r'^(?P<key>[\w]+)=(?P<value>.+)$')
logger = logging.getLogger('oscar.thumbnail')


def do_dynamic_image_url(parser, token):
    tokens = token.split_contents()

    if len(tokens) < 2:
        raise template.TemplateSyntaxError(
            "%r tag requires at least an image URL or field" % tokens[0])

    image = tokens[1]

    params = tokens[2:] if len(tokens) > 2 else []
    return DynamicImageNode(image, params)


class DynamicImageNode(template.Node):
    def __init__(self, image, params):
        self.image = image
        self.params = {}

        for p in params:
            try:
                bits = p.split('=')
                self.params[bits[0]] = template.Variable(bits[1])
            except IndexError as e:
                raise template.TemplateSyntaxError(
                    "image tag parameters must be of form key=value, "
                    "you used '%s'" % p
                ) from e

    def render(self, context):
        if host := getattr(settings, 'DYNAMIC_MEDIA_URL', None):
            path = (
                self.image.name
                if isinstance(self.image, ImageFieldFile)
                else self.image
            )
            return self._extracted_from_render_(path, context, host)

    # TODO Rename this here and in `render`
    def _extracted_from_render_(self, path, context, host):
        params = []
        ext = path[path.rfind('.') + 1:]
        ext_changed = False

        for key, v in self.params.items():
            value = v.resolve(context)
            if key == 'format':
                ext = value
                ext_changed = True
            else:
                params.append(f'{key}-{value}')

        if params:
            path = '.'.join((path, '_'.join(params), ext))
        elif ext_changed:
            path = '.'.join((path, ext)) if params else '.'.join((path, 'to', ext))
        return host + path


class ThumbnailNode(template.Node):
    no_resolve = {'True': True, 'False': False, 'None': None}

    def __init__(self, parser, token):
        args = token.split_contents()
        # The first argument is the source file.
        self.source_var = parser.compile_filter(args[1])
        # The second argument is the size/geometry.
        self.size_var = parser.compile_filter(args[2])

        is_context_variable = args[-2] == 'as'
        if is_context_variable:
            self.context_name = args[-1]
            args = args[3:-2]
        else:
            self.context_name = None
            args = args[3:]

        self.options = []
        for arg in args:
            m = kw_pat.match(arg)
            key = smart_str(m.group('key'))
            expr = parser.compile_filter(m.group('value'))
            self.options.append((key, expr))

    def get_thumbnail_options(self, context):
        return {'size': self.size_var.resolve(context)}

    def render(self, context):
        try:
            return self._render(context)
        except Exception as e:
            if getattr(settings, 'OSCAR_THUMBNAIL_DEBUG', settings.DEBUG):
                raise e

            logger.exception(e)
            return ''

    def _render(self, context):
        source = self.source_var.resolve(context)
        options = self.get_thumbnail_options(context)
        for key, expr in self.options:
            value = self.no_resolve.get(str(expr), expr.resolve(context))
            options[key] = value

        thumbnailer = get_thumbnailer()
        thumbnail = thumbnailer.generate_thumbnail(source, **options)

        if self.context_name is None:
            return escape(thumbnail.url)
        context[self.context_name] = thumbnail
        return ''


def thumbnail(parser, token):
    return ThumbnailNode(parser, token)


register.tag('image', do_dynamic_image_url)
register.tag('thumbnail', thumbnail)
