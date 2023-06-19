from flask import Response, make_response

from sh_configs.servers import db, storage_client
from sh_configs.config import settings

from datetime import datetime, timezone
from sh_helpers.utils import check_isbn
import logging
logger = logging.getLogger("logger")


def get_book_status(params: dict) -> Response:
    # Given an ISBN, return a book info object
    isbn = params.get('isbn')
    contract = params.get('contract')  # validated in mai and then pushed from headers
    extended_data = True if params.get('extended_data') else False  # make fully True/False not None/True

    if not isbn:
        print(f'no isbn!')
        return make_response({"error": {"message": "No isbn specified", "code": 10}}, 200)

    match = check_isbn(isbn)

    if not match:
        return make_response({"error": {"message": f"incorrect isbn format {isbn}", "code": 23}}, 200)
    settings.get_config()  # call this each time rather than at startup as the app may already be running

    mp3_count, image_count, last_date = get_asset_count(isbn)
    meta = get_meta(isbn, extended_data)

    if not meta:
        return make_response({"error": {"message": f"isbn {isbn} was not found", "code": 21}}, 200)
    else:
        meta_complete, missing_meta = is_meta_complete(meta)

    if meta.get('contract') != contract:
        return make_response({"error": {'message': f'isbn {isbn} does not belong to this publisher', 'code': 20}}, 200)

    info = {
        'mp3_count': mp3_count,
        'image_count': image_count,
        'last_asset_date': last_date,
        'meta_complete': meta_complete,
        'metadata': meta,
        'missing_metadata': missing_meta
    }
    return make_response({"data": info}, 200)


def get_asset_count(isbn: str) -> (int, int, datetime):
    #  Use blob listing to get the
    extensions = ['jpeg', 'jpg', 'png', 'mp3']
    bucket = storage_client.bucket("xigxag-dev.appspot.com")
    blobs = bucket.list_blobs(prefix=f"pending/{isbn}")
    mp3_count = 0
    image_count = 0
    last_date = datetime(1970, 1, 1, tzinfo=timezone.utc)
    for blob in blobs:
        if any(ext in blob.name for ext in extensions):
            last_date = blob.updated if blob.updated > last_date else last_date
            if 'mp3' in blob.name:
                mp3_count += 1
            else:
                image_count += 1

    return mp3_count, image_count, last_date


def get_meta(isbn: str, extended_data: bool) -> dict or None:
    book_dict = db.collection("bookstore").document(isbn).get().to_dict()
    if not book_dict:
        logging.info(f"Failed to find {isbn} in bookstore")
        return None

    return book_to_book_info(book_dict, extended_data)


def book_to_book_info(book: dict, extended_data: bool) -> dict:
    book_data = {'contract': book.get('contract'), 'publishDate': book.get('publishDate')}
    if not book.get('titlePrefix') == "":
        book_data['title'] = book.get('titlePrefix') + " " + book.get('sortTitle')
    else:
        book_data['title'] = book.get('sortTitle')
    book_data['reference'] = book.get('coreSourceReference')
    book_data['latest_meta_update'] = book.get('lastUpdate', [])[0].get('dateTime')
    book_data['latest_meta_file'] = book.get('lastUpdate', [])[0].get('source')
    book_data['author'] = book.get('displayAuthor')
    author_narrator, _author, _narrator = narrator_from_author(book.get('displayAuthor'))
    if author_narrator:
        book_data['author'] = _author
        book_data['narrator'] = _narrator
    else:
        book_data['narrator'] = narrator_from_list(book['narrator'])

    if extended_data:
        book_data['synopsis'] = book.get('synopsis')
        book_data['genres'] = book.get('genres')
        book_data['publisher'] = book.get('publisher')

    return book_data


def narrator_from_author(author):
    # see if we can get a ', Read by XXXX'
    if ', Read by' in author:
        parts = author.split(', Read by')
        author = parts[0]
        narrator = parts[1].strip()
        if ',' in parts[1].strip():
            narrator_parts = parts[1].split(",", maxsplit=1)
            narrator = narrator_parts[0].strip()
            author = f"{author}, {narrator_parts[1].strip()}"
        return True, author, narrator

    else:
        return False, "", ""


def narrator_from_list(narrators: [dict]) -> str:
    narrator_string = ""
    add_comma = ""
    narrator_count = 0
    for narrator in narrators:
        if not len(narrator['first']) and not len(narrator['second']):
            continue
        narrator_string += add_comma + narrator['first'] + " " + narrator['second']
        narrator_count += 1
        add_comma = ", "

    return narrator_string


def is_meta_complete(book_dict: dict) -> (bool, []):
    missing_meta = []
    is_complete = True
    for key in settings.meta_check:
        if len(book_dict.get(key, "")) == 0:
            missing_meta.append(key)
            is_complete = False

    return is_complete, missing_meta
