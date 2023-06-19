import re

from sh_configs.config import settings
from sh_configs.servers import db

import logging
import string
import random

logger = logging.getLogger("logger")


def check_isbn(isbn: str) -> bool:
    match = re.search(pattern=settings.isbn_pattern, string=isbn)
    if match:
        return True and len(isbn) == 13
    return False


def validate_key(key: str) -> bool:
    # id_token = None
    if not key:
        return False
    rec_snap = db.collection("system").document('apiKeys').collection("publishers").document(key).get()
    if rec_snap:
        key_info = rec_snap.to_dict()
        if key_info:
            return key_info.get("enabled", False)

    logging.error(f"No match for key {key} found!")
    return False


def isbn_in_contract(isbn: str, contract: str, book_dict: dict or None = None) -> bool:
    # return True if the isbn belongs to contract
    # return False if isbn doesn't exist or isn't a match to contract
    # pass in a book_dict for efficiency if we have one
    if not isbn:
        return False

    if not book_dict:
        book_dict = db.collection("bookstore").document(isbn).get().to_dict()

    if not book_dict:
        logging.info(f"Failed to find {isbn} in bookstore")
        return False

    return contract == book_dict.get('contract')


def generate_code(code_length: int) -> str:

    alphabet = string.ascii_letters
    code = "".join(random.choices(alphabet, k=code_length))
    return code


