import time


class ResponseTimingMiddleware(object):
    """A wrapper around an app to print out the response time for each
    request."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        """Meaure the time spent in the application."""
        start_time = time.time()
        response = self.app(environ, start_response)
        response_time = (time.time() - start_time) * 1000
        timing_text = "总共耗时: {:.10f}ms \n".format(response_time)
        response = [timing_text.encode('utf-8') + response[0]]

        return response
