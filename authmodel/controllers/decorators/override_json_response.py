import logging
from functools import wraps

_logger = logging.getLogger(__name__)
header_odoo_db = 'odoo-db'
header_device = 'device-id'


def override_json_response(headers):
    ''' call a function a number of times '''

    def decorate(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # setattr(JsonRequest, '_json_response', _json_response)  # overwrite the method
            # setattr(JsonRequest, '__init__', __init__)  # overwrite the method
            return fn(*args, **kwargs)

        return wrapper

    return decorate
