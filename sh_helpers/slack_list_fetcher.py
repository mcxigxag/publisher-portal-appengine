from flask import Response, make_response
from sh_configs.servers import db


def get_publisher_contract_codes() -> Response:

    contract_codes = db.collection('system').document('publishers').get().to_dict()
    if not contract_codes:
        return make_response(options_from_list(["Sorry, something has gone wrong"]), 200)

    contract_codes_data = contract_codes.get('ids', ['Sorry, something has gone wrong'])

    return make_response(options_from_list(contract_codes_data), 200)


def options_from_list(codes: [str]) -> dict:
    # take a string of codes and return a Slack options block
    # https://api.slack.com/reference/block-kit/composition-objects#option

    return {'options': [{"text":{'type':'plain_text', 'text': a}, 'value': a} for a in codes]}


if __name__ == '__main__':
    print(options_from_list(['XX-HC', 'XX-BOOKWIRE']))