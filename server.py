from wsgiref.simple_server import make_server
from app import application
from middlewares.cors import CORSMiddleware
from middlewares.timing import ResponseTimingMiddleware

print("Server is running at http://localhost:8000 . Press Ctrl+C to stop.")
app = ResponseTimingMiddleware(
    CORSMiddleware(
        app=application,
        whitelist=[
            'http://localhost:9000',
            'http://localhost:9001'
        ]
    )
)
server = make_server('localhost', 8000, app)
server.serve_forever()
