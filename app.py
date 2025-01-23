###############################################################################
# 
# The MIT License (MIT)
# 
# Copyright (c) 2014 Miguel Grinberg
# 
# Released under the MIT license
# https://github.com/miguelgrinberg/flask-video-streaming/blob/master/LICENSE
#
###############################################################################

import argparse
import configparser
import json
from logging import getLogger, basicConfig, INFO

from flask import Flask, Response, render_template, request, jsonify

from camera import VideoCamera

""" load configuration """
config = configparser.ConfigParser()
config.read('config.ini')
flip_code = eval(config.get('camera', 'flipcode'))

app = Flask(__name__)

logger = getLogger(__name__)
basicConfig(
    level=INFO,
    format="%(asctime)s %(levelname)s %(name)s %(funcName)s(): %(message)s")


def gen(camera):
    while True:
        frame = camera.get_frame(stream_only, is_test, flip_code)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/')
def index():
    return render_template('index.html', flip_code=flip_code)


@app.route('/video_feed')
def video_feed():
    video_camera = VideoCamera(algorithm, target_color, stream_only, is_test)
    return Response(
        gen(video_camera),
        mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/tracking', methods=['POST'])
def tracking():
    global stream_only
    global is_test
    global flip_code

    mearmpi_response = ""
    command = request.json['command']

    if command == "streamonly":
        stream_only = True
        is_test = False
        mearmpi_response = "true"
    elif command == "tracking":
        stream_only = False
        is_test = False
        mearmpi_response = "true"
    elif command == "test":
        stream_only = False
        is_test = True
        mearmpi_response = "true"

    if command == "flip-x":
        flip_code = "0"
    elif command == "flip-y":
        flip_code = "1"
    elif command == "flip-xy":
        flip_code = "-1"
    elif command == "flip-reset":
        flip_code = "reset"

    result = {
        "command": command,
        "result": mearmpi_response,
        "flip_code": flip_code
    }
    logger.info(
        "sent:{} res:{} flip: {}".format(command, mearmpi_response, flip_code))
    return jsonify(ResultSet=json.dumps(result))


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('color.ini')
    colors = config.sections()

    parser = argparse.ArgumentParser(
        description='opencv object tracking with MearmPi')
    parser.add_argument(
        '-a',
        '--algorithm',
        help='select object tracking algorithm',
        default='camshift',
        choices=['camshift', 'meanshift'])
    parser.add_argument(
        '-s',
        '--stream_only',
        help='stream mode (without object traking)',
        action='store_true')
    parser.add_argument(
        '-t',
        '--test',
        help='test mode (without moving arms)',
        action='store_true')
    parser.add_argument(
        '-c',
        '--color',
        help='select tracking color in color.ini',
        default='',
        choices=colors)
    args = parser.parse_args()

    algorithm = args.algorithm
    target_color = args.color
    stream_only = args.stream_only
    is_test = args.test

    app.run(host='0.0.0.0', threaded=True)
