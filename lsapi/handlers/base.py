import os
import json
import logging
import tornado.web

from lsapi import cloudutils
from lsapi.helpers.exceptions import APIException, InvalidAPIToken

logging.basicConfig(
    format='[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)',
    datefmt='%d/%m/%Y %I:%M:%S %p',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        return json.JSONEncoder.default(self, o)


class CheckHandler(tornado.web.RequestHandler):

    def get(self):
        """
           This method is responsible for the health check of the API.
        """
        logger.info('health checking')
        self.set_status(200)
        self.finish()


class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        self.json_args = None
        super(BaseHandler, self).__init__(application, request, **kwargs)

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, DELETE')

    def write_error(self, status_code, **kwargs):
        exc_info = kwargs["exc_info"]
        if len(exc_info) > 0:
            self.add_header("Content-Type", "application/json")

            info = exc_info[1]
            message = str(info)

            if isinstance(info, APIException):
                self.respond(message, status_code)
            else:
                logger.error('API Error: ' + message)
                self.respond(
                    "Unknown error. Contact the author for more details.", status_code)

    @staticmethod
    def _check_basic_auth(headers):
        granted = False
        auth_str = headers.get('Authorization')
        auth_tkn = auth_str.split()[-1]
        api_tkn = os.getenv('API_TOKEN')
        if not api_tkn:
            raise InvalidAPIToken('Cannot find API TOKEN as os env')
        if auth_tkn == api_tkn:
            granted = True
        return granted

    def prepare(self, **kwargs):
        logger.debug("Preparing request data")
        is_granted = self._check_basic_auth(self.request.headers)
        if not is_granted:
            raise APIException(401, 'Invalid authorization token', )

        if self.request.method in ('DELETE', 'POST'):
            try:
                self.json_args = json.loads(self.request.body)
            except json.JSONDecodeError:
                logger.error("Error decoding body JSON")

    def respond(self, data, code=200):
        self.set_header('Content-Type', 'application/json')
        self.set_status(code)
        data = {"message": data}
        self.write(JSONEncoder().encode({
            **data
        }))
        self.finish()

    def get(self, **kwargs):
        """
        basic get using headers to check a ELB information
        :param kwargs:
        """
        elb = kwargs.get('key')
        logger.info('Getting ELB information')
        elb_response = cloudutils.list_elb_instances(elb)
        if isinstance(elb_response, list):
            self.respond(elb_response, 200)
        else:
            self.respond("The elb does not exist", 404)

    def post(self, **kwargs):
        """
            Endpoint responsible for add instances into ELB
        """
        logger.info("Receiving request for ELB attachment.")
        try:
            if not kwargs.get('key'):
                raise APIException(404, 'Invalid path key on url')
            if not isinstance(self.json_args.get('instanceId'), str):
                raise APIException(400, 'Wrong data format')
            elb_response = cloudutils.add_instance_on_elb(kwargs.get('key'), self.json_args.get('instanceId'))
            if not elb_response:
                self.respond('Instance not found', 400)
            elif elb_response.get('status') == 201:
                self.respond(elb_response.get('info'), 201)
            elif elb_response.get('status') == 409:
                self.respond('Instance already on ELB', 409)
        except APIException as e:
            self.respond(e.log_message, e.status_code)

    def delete(self, **kwargs):
        """
           Endpoint responsible for remove instances from  ELB
        """
        logger.info("Receiving request for ELB detachment.")
        try:
            if not kwargs.get('key'):
                raise APIException(404, 'Invalid path key on url')
        except APIException as e:
            self.respond(e.log_message, e.status_code)
        try:
            if not isinstance(self.json_args.get('instanceId'), str):
                raise APIException(400, 'Wrong data format')
            elb_response = cloudutils.rem_instance_from_elb(kwargs.get('key'), self.json_args.get('instanceId'))
            if not elb_response:
                self.respond('Instance not found', 400)
            elif elb_response.get('status') == 201:
                self.respond(elb_response.get('info'))
            elif elb_response.get('status') == 409:
                self.respond('Instance is not on ELB', 409)
        except APIException as e:
            self.respond(e.log_message, e.status_code)
