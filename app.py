"""ref:
https://github.com/ECI-Robotics/opencv_remote_streaming_processing/
"""

from flask import Flask, Response
from camera import VideoCamera
from logging import getLogger, basicConfig, DEBUG, INFO
import argparse
import configparser

logger = getLogger(__name__)
basicConfig(
    level=INFO,
    format="%(asctime)s %(levelname)s %(name)s %(funcName)s(): %(message)s")
app = Flask(__name__, static_url_path='')


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/video_feed')
def video_feed():
    video_camera = VideoCamera(algorithm, target_color, stream_only, is_test)
    return Response(
        gen(video_camera),
        mimetype='multipart/x-mixed-replace; boundary=frame')


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
