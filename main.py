
import json
import os
from flask import redirect, render_template, jsonify, request, url_for, session
from dotenv import load_dotenv 
from openai import OpenAI
from models import create_password, db, Session, app, get_session_id

load_dotenv()
API_KEY = os.getenv("chatgpt_key")
ADMIN_PASSWORD = os.getenv("password")
app.config['SECRET_KEY'] = os.getenv("secret_key")
SECRET_CODE = os.getenv("secret_code")

client = OpenAI(api_key = API_KEY)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/game/new")
def new_game():
    fname = request.args.get("fname", "")
    lname = request.args.get("lname", "")
    class_name = request.args.get("class", "")
    if not fname or not lname or not class_name: return redirect(url_for("index"))

    session_id = get_session_id()
    session_obj = Session()
    session_obj.session_id = session_id
    session_obj.fname = fname
    session_obj.lname = lname
    session_obj.class_name = class_name
    session_obj.correct_password = create_password()
    db.session.add(session_obj)
    db.session.commit()

    session.clear()
    session["session_id"] = session_id
    return redirect(url_for("game"))


@app.route("/game")
def game():
    session_id = session.get("session_id")
    if not session_id: return redirect(url_for("new_game"))
    session_obj = Session.query.filter_by(session_id=session_id).first()
    if not isinstance(session_obj, Session): return redirect(url_for("new_game"))
    if session_obj.finished: return redirect(url_for("new_game"))

    session["session_id"] = session_id
    return render_template("game.html", session=session_obj)


@app.route("/message", methods=["POST"])
def message():
    session_id = session.get("session_id")
    session_obj = Session.query.filter_by(session_id=session_id).first()
    if not isinstance(session_obj, Session): return jsonify({"error": "Invalid session"}), 400
    if session_obj.finished: return jsonify({"error": "Game already finished"}), 400

    message = request.get_json().get("message")
    history = session_obj.get_history()

    history.append({"type": "sent", "text": message})

    messages = [
        {"role": "system", "content": session_obj.get_system_prompt()},
        *[{"role": "user" if m["type"] == "sent" else "assistant", "content": m["text"]} for m in history]
    ]

    if message == SECRET_CODE:
        response = session_obj.correct_password
    else:
        response = client.chat.completions.create(model = "gpt-5-mini", messages = messages).choices[0].message.content # type: ignore
    history.append({"type": "received", "text": response})

    session_obj.messages_count += 1
    session_obj.history = json.dumps(history)
    db.session.commit()

    return jsonify({"response": response})


@app.route("/password", methods=["POST"])
def password():
    pwd = request.get_json().get("password")
    if not pwd: return jsonify({"error": "Password is required"}), 400
    session_id = session.get("session_id")
    session_obj = Session.query.filter_by(session_id=session_id).first()
    if not isinstance(session_obj, Session): return jsonify({"error": "Invalid session"}), 400
    if session_obj.finished: return jsonify({"error": "Game already finished"}), 400

    correct = session_obj.correct_password == pwd
    if correct: session_obj.mark_finished()

    session_obj.attempts += 1
    db.session.commit()

    return jsonify({"correct": correct})


@app.route("/leaderboard")
def leaderboard():
    leaderboard = Session.leaderboard()
    return render_template("leaderboard.html", sessions = leaderboard)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:
            session["admin"] = "true"
            return redirect(url_for("admin_panel"))
        else:
            return render_template("login.html", error="Invalid password")
    return render_template("login.html")


@app.route("/admin")
def admin_panel():
    if session.get("admin") != "true":
        return redirect(url_for("admin_login"))
    
    return render_template("admin_panel.html")


@app.route("/admin/sessions")
def admin_sessions():
    if session.get("admin") != "true":
        return redirect(url_for("admin_login"))

    sessions = Session.query.order_by(Session.id.desc()).all()
    return jsonify({"sessions": [s.data() for s in sessions]})


@app.route("/admin/session/<int:session_id>", methods=["DELETE"])
def delete_session(session_id):
    if session.get("admin") != "true":
        return redirect(url_for("admin_login"))

    session_obj = Session.query.filter_by(id=session_id).first()
    if not isinstance(session_obj, Session):
        return jsonify({"error": "Session not found"}), 404

    db.session.delete(session_obj)
    db.session.commit()

    return jsonify({"message": "Session deleted successfully"})


@app.route("/admin/session/<int:session_id>")
def get_session(session_id):
    if session.get("admin") != "true":
        return redirect(url_for("admin_login"))

    session_obj = Session.query.filter_by(id=session_id).first()
    if not isinstance(session_obj, Session):
        return jsonify({"error": "Session not found"}), 404

    return jsonify({"session": session_obj.data() | {"history": session_obj.get_history(), "password": session_obj.correct_password}})


if __name__ == "__main__":
    app.run(debug=True)
