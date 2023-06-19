import logging.config
import time
from flask import Flask, request, make_response, Response
from flask_cors import cross_origin

from sh_helpers.book_utils import get_book_status
from sh_helpers.cover_server import process_cover
from sh_helpers.slack_list_fetcher import get_publisher_contract_codes
from sh_helpers.utils import validate_key, isbn_in_contract


logging.config.fileConfig('loggly.conf')
logging.Formatter.converter = time.gmtime
logger = logging.getLogger("logger")

app = Flask(__name__)


@app.route('/publisherContractCodes', methods=['POST'])
@cross_origin()
def publisher_contract_codes():
    return get_publisher_contract_codes()


@app.route('/ppGetCover', methods=['GET'])
@cross_origin()
def get_cover() -> Response:
    req = request  #if req is None else req

    if not validate_key(req.headers.get('key')):
        print(f'no key!')
        return make_response({"error": {"message": "Bad key", "code": 12}}, 400)
    try:
        isbn = req.args['isbn']
    except (KeyError, ValueError):
        return make_response({"error": {"message": "No isbn", "code": 10}}, 400)
    try:
        w = req.args['w']
        h = req.args['h']
    except (KeyError, ValueError):
        w = "200"
        h = "200"
    contract = req.headers.get('contract')
    if not contract:
        print(f'no contract "{contract}"')
        return make_response("Error, no contract", 400)

    if not isbn_in_contract(isbn=isbn, contract=contract):
        print(f'isbn {isbn} not in contract {contract}')
        return make_response({"error": {'message': f'isbn {isbn} not in contract {contract}', 'code': 20}}, 404)

    return process_cover(isbn=isbn, w=w, h=h)


@app.route('/ppGetBookState', methods=['POST'])
@cross_origin()
def get_book_state(req=None) -> Response:
    print("CALL TO GET STATE")
    req = request # if req is None else req

    if not validate_key(req.headers.get('key')):
        print(f'bad key!')
        return make_response({"error": {"message": "Bad api key provided", "code": 12}}, 200)

    json_params = req.get_json(silent=True)
    params = json_params.get('data', {})

    contract = req.headers.get('contract')
    if not contract:
        print(f'no contract')
        return make_response({"error": {"message": "No contract set for this user", "code": 11}}, 200)

    params['contract'] = contract

    return get_book_status(params=params)

  
if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to fw1.yaml.

    app.run(host='127.0.0.1', port=8080, debug=True)
