from flask import Blueprint, jsonify, request
from . import kinovod


blueprint = Blueprint('kinovod_api', __name__,
                      template_folder='templates')


@blueprint.route('/api/film/k<code>/<api_key>')
def kinovod_film(code, api_key):
    if (request.referrer == request.host_url + "film/k" + code
            or api_key == "p7Kwv6z7y4MX2i0LaCxl"):
        return jsonify(kinovod.film(code))
    return jsonify({'error': '403 Forbidden'})


@blueprint.route('/api/serial/k<code>/e<int:e>/<api_key>')
def kinovod_serial_e(code, e, api_key):
    if (request.referrer == request.host_url + "serial/k" + code
            or api_key == "p7Kwv6z7y4MX2i0LaCxl"):
        return jsonify(kinovod.serial(code, 0, e))
    return jsonify({'error': '403 Forbidden'})



@blueprint.route('/api/serial/k<code>/s<int:s>e<int:e>/<api_key>')
def kinovod_serial(code, s, e, api_key):
    if (request.referrer == request.host_url + "serial/k" + code
            or api_key == "p7Kwv6z7y4MX2i0LaCxl"):
        return jsonify(kinovod.serial(code, s, e))
    return jsonify({'error': '403 Forbidden'})