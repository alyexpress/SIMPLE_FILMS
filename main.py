from flask import Flask, render_template, request, redirect, jsonify
from flask_login import (LoginManager, login_user, login_required,
                         logout_user, current_user)

from utils import hashing, square_pic, censored_text, time_ago
from os import remove

from config import SECRET_KEY
from data import db_session
from data.users import User
from data.favorites import Favorite
from data.comments import Comment
from data.api_keys import ApiKey
from api import kinovod
from api import kinovod_api


app = Flask(__name__)
# Set random secret key for app
app.config['SECRET_KEY'] = SECRET_KEY
# Database – global init
db_session.global_init("data/database.db")
# Set login manager
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route('/log-out')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.errorhandler(401)
def http_error_handler(error):
    message = "Вы не авторизовались :("
    buttons = [
        {"href": "/log-in", "color": "info", "text": "Войти"},
        {"href": "/sign-up", "color": "warning", "text": "Регистрация"}
    ]
    return render_template("error.html", code=401,
                           message=message, btns=buttons), 401

@app.errorhandler(404)
def http_error_handler(error):
    message = "Такой страницы не существует :("
    buttons = [{"href": "/", "color": "warning", "text": "На главную"}]
    return render_template("error.html", code=404,
                           message=message, btns=buttons), 404


@app.errorhandler(500)
def http_error_handler(error):
    message = "Этот материал недоступен в настоящее время :("
    buttons = [
        {"href": "/", "color": "warning", "text": "На главную"},
        {"href": "", "color": "info", "text": "Сообщить об ошибке"}
    ]
    return render_template("error.html", code=500,
                           message=message, btns=buttons), 500


@app.route('/')
def index():
    data = kinovod.films(count=12)['results']
    return render_template("index.html", data=data)


@app.route('/kinopoisk/<code>')
def kinopoisk(code):
    src = f"https://iframe.cloud/iframe/{code}"
    return render_template("kinopoisk.html", src=src)


@app.route('/log-in', methods=['GET', 'POST'])
def log_in():
    if request.method == 'GET':
        return render_template("log-in.html", data=[], error={})
    elif request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me')
        db_sess = db_session.create_session()
        data = [email, password, remember_me]
        error, user = {}, None
        if email.strip() == "":
            error['email'] = "Вы не указали email!"
        else:
            user = db_sess.query(User).filter(User.email == email).first()
            if user is None:
                error['email'] = "Нет пользователя с таким email!"
        if password.strip() == "":
            error['password'] = "Вы не указали пароль!"
        elif user is not None and hashing(password) != user.hashed_password:
            error['password'] = "Неверный пароль!"
        if error:
            return render_template("log-in.html", data=data, error=error)
        login_user(user, remember=remember_me is not None)
        return redirect('/')


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'GET':
        return render_template("sign-up.html", data=[], error={})
    elif request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        check_password = request.form.get('check_password')
        remember_me = request.form.get('remember_me')
        db_sess = db_session.create_session()
        data = [name, email, password, check_password, remember_me]
        error = {}
        if name.strip() == "":
            error['name'] = "Вы не указали имя!"
        if email.strip() == "":
            error['email'] = "Вы не указали email!"
        elif db_sess.query(User).filter(User.email == email).first():
            error['email'] = "Такой email уже зарегистрирован!"
        if password.strip() == "":
            error['password'] = "Вы не указали пароль!"
        elif len(password) < 6:
            error['password'] = "Пароль короче 6 символов!"
        elif password != check_password:
            error['check_password'] = "Пароли не совпадают!"
        if error:
            return render_template("sign-up.html", data=data, error=error)
        user = User(name=name, email=email, hashed_password=hashing(password))
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=remember_me is not None)
        return redirect("/")


@app.route('/other')
def other():
    return render_template("other.html")

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'GET':
        anonymous = request.args.get('anonymous')
        if anonymous is not None:
            db_sess = db_session.create_session()
            user = db_sess.query(User).get(current_user.id)
            current_user.anonymous = bool(int(anonymous))
            user.anonymous = bool(int(anonymous))
            db_sess.commit()
            return "OK"
        return render_template("settings.html", error=False)
    elif request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if current_user.hashed_password != hashing(password):
            return render_template("settings.html", error=True,
                                   name=name, email=email)
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(current_user.id)
        current_user.name, current_user.email = name, email
        user.name, user.email = name, email
        db_sess.commit()
        return render_template("settings.html", error=False)


@app.route('/set-avatar/<color>')
@login_required
def set_avatar_color(color):
    if request.referrer != request.host_url + 'settings':
        return redirect("/settings")
    if "special/" in current_user.avatar:
        remove("static/avatar/" + current_user.avatar)
    avatar = f'default/{color}.png'
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)
    current_user.avatar, user.avatar = [avatar] * 2
    db_sess.commit()
    return redirect("/settings")


@app.route('/set-avatar', methods=['POST'])
@login_required
def set_avatar():
    if request.referrer != request.host_url + 'settings':
        return redirect("/settings")
    avatar = request.files.get('avatar')
    ext = avatar.filename.split(".")[-1]
    path = f"special/{current_user.id}.{ext}"
    if "special/" in current_user.avatar:
        remove("static/avatar/" + current_user.avatar)
    avatar.save(f"static/avatar/{path}")
    square_pic("static/avatar/" + path)
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)
    current_user.avatar, user.avatar = [path] * 2
    db_sess.commit()
    return redirect("/settings")
    # ext = request.form.get('avatar').split('.')[-1]
    # avatar = request.files.get('avatar')
    # print(ext, avatar, sep=" – ")
    # return "Hello"


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
            data[field] = "–"
    db_sess, comments = db_session.create_session(), []
    favorite = (bool(db_sess.query(Favorite).filter(Favorite.code ==
        "k" + code, Favorite.user_id == current_user.id).first())
        if current_user.is_authenticated else False)
    for comment in db_sess.query(Comment).filter(Comment.code == "k" + code):
        user = db_sess.query(User).get(comment.user_id)
        avatar = "default/anonymous.png" if user is None else user.avatar
        name = "Аноним" if user is None else user.name
        comments.append({"avatar": avatar, "name": name,
                         "text": comment.text.replace("\n", "<br>"),
                         "time": time_ago(comment.created_date)})
    return render_template("film.html", data=data,
                           favorite=favorite, comments=comments[::-1])


@app.route('/serial/k<code>')
def kinovod_serial(code):
    data = kinovod.info(code)
    for field in "Жанр Страна Режиссер Актеры".split():
        if field not in data.keys():
            data[field] = "–"
    db_sess, comments = db_session.create_session(), []
    favorite = (bool(db_sess.query(Favorite).filter(Favorite.code ==
        "k" + code, Favorite.user_id == current_user.id).first())
        if current_user.is_authenticated else False)
    for comment in db_sess.query(Comment).filter(Comment.code == "k" + code):
        user = db_sess.query(User).get(comment.user_id)
        avatar = "default/anonymous.png" if user is None else user.avatar
        name = "Аноним" if user is None else user.name
        comments.append({"avatar": avatar, "name": name,
                         "text": comment.text.replace("\n", "<br>"),
                         "time": time_ago(comment.created_date)})
    return render_template("serial.html", data=data,
                           favorite=favorite, comments=comments[::-1])


@app.route('/film/k<code>/favorite')
@app.route('/serial/k<code>/favorite')
@login_required
def kinovod_favorite(code):
    data = kinovod.info(code)
    db_sess = db_session.create_session()
    favorite = db_sess.query(Favorite).filter(Favorite.code ==
        "k" + code, Favorite.user_id == current_user.id).first()
    if favorite is not None:
        db_sess.delete(favorite)
        db_sess.commit()
        return "removed"
    favorite = Favorite(code="k" + code,
        preview=data['preview'].split(".pro/")[1],
        title=data['title'], year=data['Год'][0],
        rating=data['rating'], user_id=current_user.id)
    db_sess.add(favorite)
    db_sess.commit()
    return "added"


@app.route('/favorites')
@login_required
def favorites():
    db_sess = db_session.create_session()
    favourites = db_sess.query(Favorite).filter(
        Favorite.user_id == current_user.id).all()
    data = []
    for favorite in favourites[::-1]:
        preview = f"{kinovod.SERVER}/{favorite.preview}"
        title, year = favorite.title, favorite.year
        rating, code = favorite.rating, favorite.code
        data.append({"code": code, "preview": preview,
             "title": title, "year": year, "rating": rating})
    return render_template("favorites.html", data=data)



@app.route('/leave-comment', methods=['POST'])
@login_required
def leave_comment():
    text = request.json.get("text", "Пустой комментарий")
    mark = request.json.get("mark")
    if not request.referrer.startswith(request.host_url):
        return jsonify({"error": "400 Bad Request"}), 400
    comment = Comment(code=request.referrer.split("/")[-1],
                      text=censored_text(text), mark=mark)
    if not current_user.anonymous:
        comment.user_id = current_user.id
    db_sess = db_session.create_session()
    db_sess.add(comment)
    db_sess.commit()
    return comment.text, 200


@app.route('/apikey')
@login_required
def apikey():
    db_sess = db_session.create_session()
    api_key = db_sess.query(ApiKey).filter(
        ApiKey.user_id == current_user.id).first()
    if api_key is not None:
        return api_key.key
    api_key = ApiKey(user_id=current_user.id)
    db_sess.add(api_key)
    db_sess.commit()
    return api_key.key


if __name__ == '__main__':
    app.register_blueprint(kinovod_api.blueprint)
    app.run(host="0.0.0.0", port=8080, debug=True)