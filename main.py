
import json
import os
from flask import redirect, render_template, jsonify, request, session, url_for
from dotenv import load_dotenv
from openai import OpenAI
from models import create_password, db, Session, app, get_session_id, load_json
from flask import make_response

load_dotenv()
API_KEY = os.getenv("chatgpt_key")

client = OpenAI(api_key = API_KEY)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/game/new")
def new_game():
    session_id = get_session_id()
    session = Session()
    session.session_id = session_id
    session.correct_password = create_password()
    session.user_id = 1
    db.session.add(session)
    db.session.commit()

    response = redirect(url_for("game"))
    response.set_cookie("session_id", session_id)
    return response


@app.route("/game")
def game():
    session_id = request.cookies.get("session_id")
    if not session_id: return redirect(url_for("new_game"))
    session = Session.query.filter_by(session_id=session_id).first()
    if not isinstance(session, Session): return redirect(url_for("new_game"))
    if session.finished: return redirect(url_for("new_game"))

    response = make_response(render_template("game.html"))
    response.set_cookie("session_id", session_id)

    return response


@app.route("/message", methods=["POST"])
def message():
    session_id = request.cookies.get("session_id")
    session = Session.query.filter_by(session_id=session_id).first()
    if not isinstance(session, Session): return jsonify({"error": "Invalid session"}), 400
    if session.finished: return jsonify({"error": "Game already finished"}), 400

    message = request.get_json().get("message")
    hisotry_str = request.cookies.get("history", "[]")
    history = load_json(hisotry_str)

    history.append({"type": "sent", "text": message})

    messages = [
        {"role": "system", "content": session.get_system_prompt()},
        *[{"role": "user" if m["type"] == "sent" else "assistant", "content": m["text"]} for m in history]
    ]

    response = client.chat.completions.create(model = "gpt-5-mini", messages = messages).choices[0].message.content # type: ignore
    history.append({"type": "received", "text": response})

    session.increment()

    response_json = jsonify({"response": response})
    response_json.set_cookie("history", json.dumps(history))
    return response_json


@app.route("/password", methods=["POST"])
def password():
    pwd = request.get_json().get("password")
    if not pwd: return jsonify({"error": "Password is required"}), 400
    session_id = request.cookies.get("session_id")
    session = Session.query.filter_by(session_id=session_id).first()
    if not isinstance(session, Session): return jsonify({"error": "Invalid session"}), 400
    if session.finished: return jsonify({"error": "Game already finished"}), 400

    correct = session.correct_password == pwd
    if correct: session.mark_finished()

    session.attempts += 1
    db.session.commit()

    return jsonify({"correct": correct})


@app.route("/leaderboard")
def leaderboard():
    sessions = Session.leaderboard()
    return render_template("leaderboard.html", sessions=sessions)


if __name__ == "__main__":
    app.run(debug=True)
