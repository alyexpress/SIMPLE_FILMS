from flask import Blueprint, jsonify, request, redirect
from . import kinovod
from data import db_session
from data.api_keys import ApiKey


blueprint = Blueprint('kinovod_api', __name__,
                      template_folder='templates')


@blueprint.route('/api/film/k<code>/<api_key>')
def kinovod_film(code, api_key):
    if request.referrer == request.host_url + "film/k" + code:
        return jsonify(kinovod.film(code))
    db_sess = db_session.create_session()
    if db_sess.query(ApiKey).get(api_key):
        return jsonify(kinovod.film(code))
    return jsonify({'error': '403 Forbidden'}), 403


@blueprint.route('/api/serial/k<code>/e<int:e>/<api_key>')
def kinovod_serial_e(code, e, api_key):
    if request.referrer == request.host_url + "serial/k" + code:
        return jsonify(kinovod.serial(code, 0, e))
    db_sess = db_session.create_session()
    if db_sess.query(ApiKey).get(api_key):
        return jsonify(kinovod.serial(code, 0, e))
    return jsonify({'error': '403 Forbidden'}), 403



@blueprint.route('/api/serial/k<code>/s<int:s>e<int:e>/<api_key>')
def kinovod_serial(code, s, e, api_key):
    if request.referrer == request.host_url + "serial/k" + code:
        return jsonify(kinovod.serial(code, s, e))
    db_sess = db_session.create_session()
    if db_sess.query(ApiKey).get(api_key):
        return jsonify(kinovod.serial(code, s, e))
    return jsonify({'error': '403 Forbidden'}), 403


@blueprint.route('/api', methods=['GET'])
def api_redirect():
    _type = request.args.get('type')
    server = request.args.get('server')
    code = request.args.get('code')
    api_key = request.args.get('apikey')
    if (server not in ['kinovod', 'zona', 'rutube']
            or _type not in ['film', 'serial'] or
            code is None or api_key is None):
        return jsonify({'error': '400 Bad Request'}), 400
    if _type == "film":
        return redirect(f"api/film/{server[0]}{code}/{api_key}")
    season = request.args.get('season')
    episode = request.args.get('episode')
    if (episode is None or not episode.isdigit() or
            season is not None and not season.isdigit()):
        return jsonify({'error': '400 Bad Request'}), 400
    if season is None:
        return redirect(f"api/serial/{server[0]}{code}/e{episode}/{api_key}")
    return redirect(f"api/serial/{server[0]}{code}/s"
                    + f"{season}e{episode}/{api_key}")