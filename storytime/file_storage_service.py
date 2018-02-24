#
# Story Time App
# Exposes functions that deal with file storage
#

import os
import uuid

from flask_uploads import UploadSet
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from storytime.story_time_db_init import UploadFile


def _generate_file_name(file_extension: str):
    """
    Generates a unique file name from UUID.
    :param file_extension: the extension to add to the new file name
    :return: a string in the form filename.extension
    """
    uid = uuid.uuid1()
    return secure_filename('{}{}'.format(uid, file_extension))


def save_file(file: FileStorage, upload_set: UploadSet):
    """
    Save a file to the file system using the Flask-Uploads config.
    :param file: the file to save to the file system
    :param upload_set: the upload set to save the file to
    :return: the UploadFile object representing the file that was saved
    """
    orig_filename, file_extension = os.path.splitext(file.filename)

    # Give file a new randomly generated filename
    file.filename = _generate_file_name(file_extension=file_extension)
    saved_filename = upload_set.save(file)
    url = upload_set.url(saved_filename)
    upload_file = UploadFile(filename=saved_filename, url=url)
    return upload_file


def delete_file(file: UploadFile, upload_set: UploadSet):
    """
    Delete from the file system the file associated with the given UploadFile
    :param file: the UploadFile associated with the file to delete
    :param upload_set: the upload set to retrieve the file from
    """
    file_path = upload_set.path(file.filename)
    try:
        os.remove(file_path)
    except OSError:
        pass
