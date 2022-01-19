from flask import Flask, render_template, request, current_app
from flask_socketio import SocketIO, emit, join_room, leave_room
import os, string, random, threading, time

app = Flask(__name__)
app.config["SECRET_KEY"] = "lol"

import logging

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*")

games = {}
ids = []
names = {}

phrases = ["one", "two", "three"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/play/<idd>")
def join(idd):
    if idd in games:
        if "uid" in request.cookies and (
            request.cookies.get("uid") in games[idd]["players"]
            or request.cookies.get("uid") == games[idd]["host"]
        ):
            return render_template("room.html")
        else:
            return "Game access denied", 403
    else:
        return "Game not found", 404


# host clicks start game
@socketio.on("startGame")
def start_game(data):
    uid = data["uid"]
    game = data["rid"]
    if games[game]["host"] == uid and len(games[game]["players"]) > 0:
        emit("gameStart", room=game)


# connecting to room
@socketio.on("joinGame")
def join_game(data):
    uid = data["uid"]
    game = data["game"]
    if games[game]["host"] == uid or uid in games[game]["players"]:
        join_room(game)
    if games[game]["host"] == uid:
        join_room("host")
    emit(
        "playersUpdate",
        {"players": list(map(lambda uid: names[uid], games[game]["players"]))},
        room=game,
    )


# generating unique ID for each player
@socketio.on("getID")
def get_id():
    chars = string.ascii_letters + string.digits
    name = "".join(random.choices(chars, k=10))
    while name in ids:
        name = "".join(random.choices(chars, k=10))
    ids.append(name)
    emit("id", name)


# player picks username
@socketio.on("setName")
def set_name(dat):
    uid = dat["uid"]
    name = dat["name"]
    names[uid] = name


# clicking join button
@socketio.on("playerJoin")
def player_join(data):
    uid = data["uid"]
    rid = data["rid"]
    if rid not in games:
        emit("gameDNE")
    else:
        if uid not in games[rid]["players"]:
            games[rid]["players"].append(uid)
            emit("join", rid)


# hosting new game
@socketio.on("getHost")
def get_host(idd):
    chars = string.ascii_letters + string.digits
    name = "".join(random.choices(chars, k=6))
    while name in games:
        name = "".join(random.choices(chars, k=6))
    games[name] = {
        "host": idd,
        "players": [idd],
    }
    emit("join", name)


if __name__ == "__main__":
    socketio.run(app, "0.0.0.0")
