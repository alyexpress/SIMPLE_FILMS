from flask import Flask, render_template, request, redirect, jsonify
from api import kinovod
from api import kinovod_api

app = Flask(__name__)


@app.route('/')
def index():
    data = kinovod.films(count=12)['results']
    return render_template("index.html", data=data)

@app.route('/kinopoisk/<code>')
def kinopoisk(code):
    src = f"https://iframe.cloud/iframe/{code}"
    return render_template("kinopoisk.html", src=src)

@app.route('/log-in')
def log_in():
    return render_template("log-in.html")

@app.route('/sign-up')
def sign_up():
    return render_template("sign-up.html")

@app.route('/other')
def other():
    return render_template("other.html")

@app.route('/search', methods=['GET'])
def get_search():
    query = request.args.get("query")
    return redirect(f"/search/{query}")

@app.route('/search/<query>')
def search(query):
    data = kinovod.search(query)['results']
    return render_template("search.html", query=query, data=data)

@app.route('/film/k<code>')
def kinovod_film(code):
    data = kinovod.info(code)
    if data['serial']:
        return redirect(f"/serial/k{code}")
    for field in "Жанр Страна Режиссер Актеры".split():
        if field not in data.keys():
            data[field] = ""
    return render_template("film.html", data=data)

@app.route('/serial/k<code>')
def kinovod_serial(code):
    data = kinovod.info(code)
    for field in "Жанр Страна Режиссер Актеры".split():
        if field not in data.keys():
            data[field] = ""
    return render_template("serial.html", data=data)


if __name__ == '__main__':
    app.register_blueprint(kinovod_api.blueprint)
    app.run(host="0.0.0.0", port=8080, debug=True)