from lsapi.handlers import base

url_patterns = [
    (r"/healthcheck", base.CheckHandler),
    (r"/elb/(?P<key>[A-Za-z0-9-]+)", base.BaseHandler)]
