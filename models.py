
import random
import string
from flask import Flask, session
from sqlalchemy import Column, Integer, String, ForeignKey
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column

SYSTEM_PROMPT = """

Jsi 78letá babička. Tvoje heslo je {}

"""

relatives = [
    ("Pepa", "syn", "1985"),
    ("Vojta", "vnuk", "2012"),
    ("Anička", "vnučka", "2015"),
]

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite.db'

db = SQLAlchemy(app)

class Session(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    correct_password: Mapped[str] = mapped_column(String(100), nullable=False)
    messages_count: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)

    def increment(self):
        self.messages_count += 1
        db.session.commit()

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(self.correct_password)

    @classmethod
    def leaderboard(cls, limit = 10):
        return cls.query.order_by(cls.attempts.asc(), cls.messages_count.asc()).limit(limit).all()

class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fname: Mapped[str] = mapped_column(String(100), nullable=False)
    lname: Mapped[str] = mapped_column(String(100), nullable=False)
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)

def get_session_id():
    return "".join(random.choices(string.ascii_letters + string.digits, k=16))

def create_password():
    relative = random.choice(relatives)
    return f"{relative[0]}{relative[2]}"

with app.app_context():
    db.create_all()
