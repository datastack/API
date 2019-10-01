import logging
from settings import settings
from lsapi.urls import url_patterns

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.autoreload
import tornado.web
from tornado.options import options


logging.basicConfig(
    format='[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)',
    datefmt='%d/%m/%Y %I:%M:%S %p'
)

logger = logging.getLogger(__name__)

class TornadoApplication(tornado.web.Application):
    def __init__(self,):
        tornado.web.Application.__init__(self, url_patterns, **settings)

def main():
    app = TornadoApplication()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()