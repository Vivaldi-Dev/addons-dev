import datetime
import json
import logging
from werkzeug.wrappers import Response

_logger = logging.getLogger(__name__)


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if isinstance(o, bytes):
        return str(o)


from odoo.http import Response
from typing import Optional, Dict


class DlinkHelper:

    @staticmethod
    def JsonValidResponse(data: any, meta: Optional[Dict] = None, valid_code: Optional[int] = 200,
                          type: Optional[str] = 'json') -> Dict[str, any]:
        """
        Return a JsonResponse with the given data and status code if code is valid or no exceptions.
        """
        json_return = {"http_status": valid_code, 'data': data}
        if meta:
            json_return['meta'] = meta
        # Response.status = str(valid_code)
        if type == 'http':
            return Response(
                mimetype='application/json',
                status=valid_code,
                content_type="application/json; charset=utf-8",
                response=json.dumps(data, default=default)
            )

        return json_return

    @staticmethod
    def JsonErrorResponse(error: any, error_code: Optional[int] = 400, type: Optional[str] = 'json') -> Dict[str, any]:
        """
        Return a JsonResponse with the given data and status code if code is not valid or with exceptions.
        """

        json_return = {"http_status": error_code, 'error': error}
        # Response.status = str(error_code)
        if type == 'http':
            return Response(
                mimetype='application/json',
                status=error_code,
                content_type="application/json; charset=utf-8",
                response=json.dumps(json_return, default=default)
            )

        return json_return
