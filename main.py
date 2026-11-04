import gzip
import os

from flask import Flask, request
from flask_cors import CORS

from src.routes.blog import blog
from src.routes.frontend import frontend

app = Flask(__name__, static_folder="src/frontend", static_url_path="")
app.url_map.strict_slashes = False
app.register_blueprint(blog)
app.register_blueprint(frontend)
CORS(app)

COMPRESSIBLE_TYPES = (
    "text/html",
    "text/css",
    "text/plain",
    "text/xml",
    "text/javascript",
    "application/javascript",
    "application/json",
    "application/xml",
    "image/svg+xml",
)


@app.after_request
def optimize_response(response):
    path = request.path or "/"
    if path.startswith("/assets/") or path in ("/styles.css", "/scripts.js", "/favicon.ico"):
        response.headers["Cache-Control"] = "public, max-age=86400"
    elif path in ("/robots.txt", "/sitemap.xml"):
        response.headers["Cache-Control"] = "public, max-age=3600"
    elif response.mimetype == "text/html" and response.status_code == 200:
        response.headers["Cache-Control"] = "public, max-age=300"

    if (
        response.status_code == 200
        and "Content-Encoding" not in response.headers
        and "gzip" in request.headers.get("Accept-Encoding", "").lower()
        and any(response.mimetype.startswith(t) for t in COMPRESSIBLE_TYPES)
    ):
        response.direct_passthrough = False
        data = response.get_data()
        if len(data) >= 256:
            compressed = gzip.compress(data, compresslevel=6)
            response.set_data(compressed)
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Content-Length"] = str(len(compressed))
            response.vary.add("Accept-Encoding")

    return response


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
