import os
import sys
import io
import base64
from urllib.parse import urlencode

# Ensure backend directory is in sys.path for proper imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import create_app
from extensions import db

# Create Flask Application instance
flask_app = create_app("production")

# Ensure database tables exist
with flask_app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Warning during DB table creation: {e}")

# Check if serverless_wsgi is available, otherwise use custom WSGI handler
try:
    import serverless_wsgi
    def handler(event, context):
        return serverless_wsgi.handle_request(flask_app, event, context)
except ImportError:
    def handler(event, context):
        path = event.get("path", "/")
        http_method = event.get("httpMethod", "GET")
        headers = event.get("headers") or {}
        query_params = event.get("queryStringParameters") or {}
        body = event.get("body") or ""
        
        if event.get("isBase64Encoded", False):
            body_bytes = base64.b64decode(body)
        else:
            body_bytes = body.encode("utf-8") if isinstance(body, str) else body

        query_string = urlencode(query_params)
        
        server_name = "localhost"
        server_port = "443"
        host = headers.get("host", headers.get("Host", ""))
        if host:
            parts = host.split(":")
            server_name = parts[0]
            if len(parts) > 1:
                server_port = parts[1]

        url_scheme = headers.get("x-forwarded-proto", headers.get("X-Forwarded-Proto", "https"))

        environ = {
            "REQUEST_METHOD": http_method,
            "SCRIPT_NAME": "",
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
            "SERVER_NAME": server_name,
            "SERVER_PORT": server_port,
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": url_scheme,
            "wsgi.input": io.BytesIO(body_bytes),
            "wsgi.errors": sys.stderr,
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
        }

        for key, value in headers.items():
            key_upper = key.upper().replace("-", "_")
            if key_upper not in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                key_upper = "HTTP_" + key_upper
            environ[key_upper] = str(value)

        response_status = "200 OK"
        response_headers = []

        def start_response(status, headers, exc_info=None):
            nonlocal response_status, response_headers
            response_status = status
            response_headers = headers

        # Execute WSGI Flask app
        response_iterable = flask_app(environ, start_response)
        response_body = b"".join(response_iterable)

        try:
            status_code = int(response_status.split(" ")[0])
        except Exception:
            status_code = 200

        res_headers = {}
        for k, v in response_headers:
            res_headers[k] = v

        is_b64 = False
        try:
            body_str = response_body.decode("utf-8")
        except UnicodeDecodeError:
            body_str = base64.b64encode(response_body).decode("utf-8")
            is_b64 = True

        return {
            "statusCode": status_code,
            "headers": res_headers,
            "body": body_str,
            "isBase64Encoded": is_b64
        }
