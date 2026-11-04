import os
from pathlib import Path

from flask import Blueprint, Response, send_from_directory

frontend = Blueprint(
    "frontend",
    __name__,
    static_folder=Path(os.path.abspath(__file__)).parent.parent.joinpath("frontend"),
)

FAVICON_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 512'>"
    "<path fill='#00f5ff' d='M392.8 1.2c-17-4.9-34.7 5-39.6 22l-128 448c-4.9 17 5 34.7 22 39.6s34.7-5 39.6-22l128-448c4.9-17-5-34.7-22-39.6zm80.6 120.1c-12.5 12.5-12.5 32.8 0 45.3L562.7 256l-89.4 89.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l112-112c12.5-12.5 12.5-32.8 0-45.3l-112-112c-12.5-12.5-32.8-12.5-45.3 0zm-306.7 0c-12.5-12.5-32.8-12.5-45.3 0l-112 112c-12.5 12.5-12.5 32.8 0 45.3l112 112c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L77.3 256l89.4-89.4c12.5-12.5 12.5-32.8 0-45.3z'/>"
    "</svg>"
)


@frontend.get("/favicon.ico")
def favicon():
    return Response(FAVICON_SVG, mimetype="image/svg+xml")


@frontend.get("/scripts.js")
def scripts():
    return frontend.send_static_file("scripts.js")


@frontend.get("/styles.css")
def styles():
    return frontend.send_static_file("styles.css")


@frontend.route("/", methods=["GET"])
def root():
    return send_from_directory(frontend.static_folder, "index.html")


@frontend.route("/projects", methods=["GET"])
def projects():
    return send_from_directory(frontend.static_folder, "projects.html")


@frontend.route("/blog", methods=["GET"])
def blog():
    return send_from_directory(frontend.static_folder, "blog.html")


@frontend.route("/resume", methods=["GET"])
def resume():
    return send_from_directory(frontend.static_folder, "resume.html")
