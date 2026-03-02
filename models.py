
import random
import string
from flask import Flask, json, session
from sqlalchemy import Column, Integer, String, ForeignKey
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column

SYSTEM_PROMPT = """

Jsi 78letá babička. Bude s tebou mluvit neznámý muž z internetu.
Ty jsi ale velmi důvěřivá a nebudeš se bát mu dávat svoje soukromé informace.
Umíš mluvit jenom česky a neznáš žádný cizí jazyk. Moc neumíš s počítačem, ale umíš používat internet a umíš psát zprávy.
Tvoje heslo je {}

"""

relatives = [
    ("Pepa", "syn", "1985"),
    ("Vojta", "vnuk", "2012"),
    ("Anička", "vnučka", "2014"),
]

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite.db'

db = SQLAlchemy(app)

class Session(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    fname: Mapped[str] = mapped_column(String(100), nullable=False)
    lname: Mapped[str] = mapped_column(String(100), nullable=False)
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)
    correct_password: Mapped[str] = mapped_column(String(100), nullable=False)
    history: Mapped[str] = mapped_column(String, default="[]")
    messages_count: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    finished: Mapped[bool] = mapped_column(default=False)

    def increment(self):
        self.messages_count += 1
        db.session.commit()

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(self.correct_password)

    def mark_finished(self):
        self.finished = True
        db.session.commit()

    def get_history(self) -> list[dict]:
        return load_json(self.history)

    @classmethod
    def leaderboard(cls, limit = 10) -> list["Session"]:
        return cls.query.where(cls.finished == True).order_by(cls.attempts.asc(), cls.messages_count.asc()).limit(limit).all()

def get_session_id():
    return "".join(random.choices(string.ascii_letters + string.digits, k=16))

def create_password():
    relative = random.choice(relatives)
    return f"{relative[0]}{relative[2]}"

def load_json(history_str: str) -> list[dict]:
    try:
        result = json.loads(history_str)
        if not isinstance(result, list): return []
        return result
    except Exception:
        return []

with app.app_context():
    db.create_all()
