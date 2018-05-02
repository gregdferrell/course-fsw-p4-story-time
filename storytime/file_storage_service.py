#
# Story Time App
# Exposes functions that deal with file storage
#

import os
import uuid

from flask_uploads import IMAGES, UploadSet
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from storytime.story_time_db_init import UploadFile

upload_set_photos = UploadSet('photos', IMAGES)


def _generate_file_name(file_extension: str):
    """
    Generates a unique file name from UUID.
    :param file_extension: the extension to add to the new file name
    :return: a string in the form filename.extension
    """
    uid = uuid.uuid1()
    return secure_filename('{}{}'.format(uid, file_extension))


def save_file(file: FileStorage):
    """
    Save a file to the file system using the Flask-Uploads config.
    :param file: the file to save to the file system
    :return: the UploadFile object representing the file that was saved
    """
    orig_filename, file_extension = os.path.splitext(file.filename)

    # Give file a new randomly generated filename
    file.filename = _generate_file_name(file_extension=file_extension)
    saved_filename = upload_set_photos.save(file)
    url = upload_set_photos.url(saved_filename)
    upload_file = UploadFile(filename=saved_filename, url=url)
    return upload_file


def delete_file(file: UploadFile):
    """
    Delete from the file system the file associated with the given UploadFile
    :param file: the UploadFile associated with the file to delete
    """
    file_path = upload_set_photos.path(file.filename)
    try:
        os.remove(file_path)
    except OSError:
        pass
