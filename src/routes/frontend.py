import os
from pathlib import Path

from flask import Blueprint, send_from_directory

frontend = Blueprint(
    "frontend",
    __name__,
    static_folder=Path(os.path.abspath(__file__)).parent.parent.joinpath("frontend"),
)
print(str(Path(os.path.abspath(__file__)).parent.parent.joinpath("frontend")))

@frontend.get("/scripts.js")
def scripts():
    return frontend.send_static_file("scripts.js")

@frontend.get("/styles.css")
def styles():  return frontend.send_static_file("styles.css")

@frontend.route("/", methods=["GET"])
def root():
    return send_from_directory(frontend.static_folder, "index.html")


@frontend.route("/projects", methods=["GET"])
def projects():
    return send_from_directory(frontend.static_folder, "projects.html")


@frontend.route("/github", methods=["GET"])
def github():
    return send_from_directory(frontend.static_folder, "github.html")


@frontend.route("/blog", methods=["GET"])
def blog():
    return send_from_directory(frontend.static_folder, "blog.html")


@frontend.route("/about", methods=["GET"])
def about():
    return send_from_directory(frontend.static_folder, "about.html")


@frontend.route("/resume", methods=["GET"])
def resume():
    return send_from_directory(frontend.static_folder, "resume.html")
