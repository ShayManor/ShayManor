import os

from flask import Flask, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")


@app.route("/", methods=["GET"])
def root():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<page>", methods=["GET"])
def any_page(page):
    return send_from_directory(app.static_folder, f"{page}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
