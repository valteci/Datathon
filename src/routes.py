from flask import Blueprint, render_template

# cria um blueprint chamado "main"
bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/hello/<name>")
def hello(name):
    return f"Olá, {name}!"
