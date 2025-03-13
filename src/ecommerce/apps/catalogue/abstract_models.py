import logging
import os

from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.core.exceptions import ImproperlyConfigured


class MissingProductImage(object):

    """
    Mimics a Django file field by having a name property.

    :py:mod:`sorl-thumbnail` requires all it's images to be in MEDIA_ROOT. This class
    tries symlinking the default "missing image" image in STATIC_ROOT
    into MEDIA_ROOT for convenience, as that is necessary every time an Oscar
    project is setup. This avoids the less helpful NotFound IOError that would
    be raised when :py:mod:`sorl-thumbnail` tries to access it.
    """

    def __init__(self, name=None):
        self.name = name if name else settings.OSCAR_MISSING_IMAGE_URL
        media_file_path = os.path.join(settings.MEDIA_ROOT, self.name)
        # don't try to symlink if MEDIA_ROOT is not set (e.g. running tests)
        if settings.MEDIA_ROOT and not os.path.exists(media_file_path):
            self.symlink_missing_image(media_file_path)

    def symlink_missing_image(self, media_file_path):
        static_file_path = find("eta/img/%s" % self.name)
        if static_file_path is not None:
            try:
                # Check that the target directory exists, and attempt to
                # create it if it doesn't.
                media_file_dir = os.path.dirname(media_file_path)
                if not os.path.exists(media_file_dir):
                    os.makedirs(media_file_dir)
                os.symlink(static_file_path, media_file_path)
            except OSError:
                raise ImproperlyConfigured(
                    (
                        "Please copy/symlink the "
                        "'missing image' image at %s into your MEDIA_ROOT at %s. "
                        "This exception was raised because Oscar was unable to "
                        "symlink it for you."
                    )
                    % (static_file_path, settings.MEDIA_ROOT),
                )
            else:
                logging.info(
                    (
                        "Symlinked the 'missing image' image at %s into your "
                        "MEDIA_ROOT at %s"
                    ),
                    static_file_path,
                    settings.MEDIA_ROOT,
                )
