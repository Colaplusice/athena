import base64
import os

from crawler_utils.utils import url2path
from flask import current_app
from werkzeug.datastructures import FileStorage

ALLOWED_EXTENSIONS = set(["txt", "pdf", "png", "jpg", "jpeg", "gif"])


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_and_save(file_stream, filename, folder_name):
    if not allowed_file(filename):
        return
    if isinstance(file_stream, str):
        file_stream = file_stream.encode("utf-8")
    filename = url2path(filename)
    folder_path = os.path.dirname(current_app.instance_path)
    file_path = os.path.join(folder_path, folder_name, filename)
    if isinstance(file_stream, FileStorage):
        file_stream.save(file_path)
    else:
        with open(file_path, "wb") as fh:
            fh.write(base64.decodebytes(file_stream))
    return file_path
