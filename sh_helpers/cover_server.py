from io import BytesIO  # for memory image
from PIL import Image
from flask import Response, make_response
from sh_configs.servers import storage_client
import google.cloud.exceptions as cloud_exceptions
import os
from sh_helpers.utils import check_isbn
import logging
logger = logging.getLogger("logger")


def process_cover(isbn: str, w: str, h: str) -> Response:
    # download file
    # convert file
    # return file bytes
    try:
        width = int(w)
        height = int(h)
    except ValueError:
        height = 200
        width = 200

    match = check_isbn(isbn)
    if not match:
        logging.info(f"Incorrect isbn format {isbn}")
        return make_response({"error": {"message": f"incorrect isbn format {isbn}", "code": 23}}, 404)

    dl_file = get_cover_image(isbn)
    if not dl_file:
        logging.info(f"Image not found {isbn}")
        return make_response({"error": {"message": "Image not found", "code": 30}}, 404)

    try:
        im = Image.open(dl_file)
        im.thumbnail((width, height), Image.ANTIALIAS)
    except FileNotFoundError:
        logging.error(f"Image conversion error for {isbn}")
        return make_response({"error": {"message": "Image conversion error", "code": 31}}, 404)

    io = BytesIO()
    im.save(io, format='JPEG')
    os.remove(dl_file)
    return Response(io.getvalue(), mimetype='image/jpeg')


def get_cover_image(isbn: str) -> str or None:
    # get a cover, download to /tmp and then return the downloaded file
    blob_name = get_image_from_bucket(isbn)
    logging.info(f"Got a file '{blob_name}'")
    if not blob_name:
        return None
    # download blob to isbn.extension
    extension = os.path.splitext(blob_name)[-1]

    local_file_path = f"/tmp/{isbn}{extension}"
    bucket = storage_client.bucket("xigxag-dev.appspot.com")
    blob = bucket.blob(blob_name)
    try:
        blob.download_to_filename(local_file_path)
    except cloud_exceptions.NotFound:
        logging.error(f"Error downloading {blob.name}")
        return None

    return local_file_path


def get_image_from_bucket(isbn: str) -> str or None:
    #  Use blob listing to get the
    extensions = ['jpeg', 'jpg', 'png']
    bucket = storage_client.bucket("xigxag-dev.appspot.com")
    blobs = bucket.list_blobs(prefix=f"pending/{isbn}")
    logging.info(f"looking in pending/{isbn}")
    for blob in blobs:
        if any(ext in blob.name for ext in extensions):
            logging.info(f"Found {blob.name}")
            return blob.name
    return None
