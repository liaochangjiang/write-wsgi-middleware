class CORSMiddleware(object):
    def __init__(self, app, whitelist=None):
        """Initialize the middleware for the specified app."""
        if whitelist is None:
            whitelist = []
        self.app = app
        self.whitelist = whitelist

    def validate_origin(self, origin):
        """Validate that the origin of the request is whitelisted."""
        return origin and origin in self.whitelist

    def cors_response_factory(self, origin, start_response):
        """Create a start_response method that includes a CORS header for the
        specified origin."""

        def cors_allowed_response(status, response_headers, exc_info=None):
            """This wraps the start_response behavior to add some headers."""
            response_headers.extend([('Access-Control-Allow-Origin', origin)])
            return start_response(status, response_headers, exc_info)

        return cors_allowed_response

    def cors_options_app(self, origin, environ, start_response):
        """A small wsgi app that responds to preflight requests for the
        specified origin."""
        response_body = 'ok'
        status = '200 OK'
        response_headers = [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(len(response_body))),
            ('Access-Control-Allow-Origin', origin),
            ('Access-Control-Allow-Headers', 'Content-Type'),
        ]
        start_response(status, response_headers)
        return [response_body.encode('utf-8')]

    def cors_reject_app(self, origin, environ, start_response):
        response_body = 'rejected'
        status = '200 OK'
        response_headers = [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(len(response_body))),
        ]
        start_response(status, response_headers)
        return [response_body.encode('utf-8')]

    def __call__(self, environ, start_response):
        """Handle an individual request."""
        origin = environ.get('HTTP_ORIGIN')
        if origin:
            if self.validate_origin(origin):
                method = environ.get('REQUEST_METHOD')
                if method == 'OPTIONS':
                    return self.cors_options_app(origin, environ, start_response)

                return self.app(
                    environ, self.cors_response_factory(origin, start_response))
            else:
                return self.cors_reject_app(origin, environ, start_response)

        else:
            return self.app(environ, start_response)
