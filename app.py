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

from flask import Flask, Response, render_template, request, jsonify
from camera import VideoCamera
from logging import getLogger, basicConfig, DEBUG, INFO
import argparse
import configparser
import json

app = Flask(__name__)

logger = getLogger(__name__)
basicConfig(
    level=INFO,
    format="%(asctime)s %(levelname)s %(name)s %(funcName)s(): %(message)s")

def gen(camera):
    while True:
        frame = camera.get_frame(stream_only, is_test)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/')
def index():
    return render_template('index.html')

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
    command = request.json['command']
    if command == "streamonly":
        stream_only = True
        is_test = False
        mearmpi_response = "True"
    elif command == "tracking":
        stream_only = False
        is_test = False
        mearmpi_response = "True"
    elif command == "test":
        stream_only = False
        is_test = True
        mearmpi_response = "True"
    result = {
        "command": command,
        "result": mearmpi_response,
    }
    logger.info("sent:{} res:{}".format(command, mearmpi_response))
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

    app.run(host='0.0.0.0')
