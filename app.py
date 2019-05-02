def application(environ, start_response):
    """The web application."""

    response_body = ""
    for key, value in environ.items():
        response_body += "<p>{} : {}\n</p>".format(key, value)

    # Set up the response status and headers
    status = '200 OK'
    response_headers = [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Length', str(len(response_body))),
    ]

    start_response(status, response_headers)
    return [response_body.encode('utf-8')]
