import logging
import time

from threading import Thread
from wsgiref.simple_server import make_server


def application(environ, start_response):
    """Serve the button HTML."""
    with open('button.html') as f:
        response_body = f.read()
    status = '200 OK'
    response_headers = [
        ('Content-Type', 'text/html'),
        ('Content-Length', str(len(response_body))),
    ]
    start_response(status, response_headers)
    return [response_body.encode('utf-8')]


log = logging.getLogger()


def run_server(port):
    """Serve the client app on the specified port."""
    print("Client is running at http://localhost:{} . Press Ctrl+C to stop.".format(port))
    httpd = make_server('localhost', port, application)
    httpd.serve_forever()


# Run three different wsgi servers on different ports
for port in range(9000, 9002 + 1):
    server = Thread(target=run_server, args=[port])
    server.daemon = True
    server.start()
    time.sleep(0.5)

# Wait until we kill the server
while True:
    time.sleep(0.5)
