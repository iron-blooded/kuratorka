from flask import Flask
from threading import Thread
from random import randint


app = Flask("")


@app.route("/")
def home():
    return "Я жив\n" + str(randint(0, 999999))


def run():
    app.run(host="0.0.0.0", port=80)


def живем():
    t = Thread(target=run, daemon=True)
    t.start()
