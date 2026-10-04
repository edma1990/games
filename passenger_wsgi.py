"""cPanel/Passenger entry point.

Passenger expects a WSGI callable, while FastAPI is ASGI. a2wsgi provides the
adapter required for regular HTTP and Bale webhook requests.
"""

from a2wsgi import ASGIMiddleware

from app.main import app

application = ASGIMiddleware(app)
