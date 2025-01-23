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
# !/usr/bin/env python
# coding: utf-8
import argparse
import configparser
import json
from logging import getLogger, basicConfig, INFO

from flask import Flask, Response, render_template, request, jsonify

from camera import VideoCamera

""" 加载配置 """
config = configparser.ConfigParser()
config.read('config.ini')
flip_code = eval(config.get('camera', 'flipcode'))  # 图像翻转代码

app = Flask(__name__)

logger = getLogger(__name__)
basicConfig(
    level=INFO,
    format="%(asctime)s %(levelname)s %(name)s %(funcName)s(): %(message)s")


def gen(camera):
    """生成视频流帧

    Args:
        camera: VideoCamera实例

    Yields:
        JPEG格式的视频帧数据
    """
    while True:
        frame = camera.get_frame(stream_only, is_test, flip_code)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/')
def index():
    """渲染主页

    Returns:
        渲染后的HTML页面
    """
    return render_template('index.html', flip_code=flip_code)


@app.route('/video_feed')
def video_feed():
    """视频流路由

    Returns:
        包含MJPEG视频流的Response对象
    """
    video_camera = VideoCamera(algorithm, target_color, stream_only, is_test)
    return Response(
        gen(video_camera),
        mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/tracking', methods=['POST'])
def tracking():
    """处理跟踪命令

    处理前端发送的跟踪控制命令，包括:
    - streamonly: 仅视频流模式
    - tracking: 跟踪模式
    - test: 测试模式
    - flip-x: X轴翻转
    - flip-y: Y轴翻转
    - flip-xy: XY轴翻转
    - flip-reset: 重置翻转

    Returns:
        包含命令执行结果的JSON响应
    """
    global stream_only
    global is_test
    global flip_code

    mearm_pi_response = ""
    command = request.json['command']

    if command == "streamonly":
        stream_only = True
        is_test = False
        mearm_pi_response = "true"
    elif command == "tracking":
        stream_only = False
        is_test = False
        mearm_pi_response = "true"
    elif command == "test":
        stream_only = False
        is_test = True
        mearm_pi_response = "true"

    if command == "flip-x":
        flip_code = "0"  # X轴翻转
    elif command == "flip-y":
        flip_code = "1"  # Y轴翻转
    elif command == "flip-xy":
        flip_code = "-1"  # XY轴翻转
    elif command == "flip-reset":
        flip_code = "reset"  # 重置翻转

    result = {
        "command": command,
        "result": mearm_pi_response,
        "flip_code": flip_code
    }
    logger.info(
        "sent:{} res:{} flip: {}".format(command, mearm_pi_response, flip_code))
    return jsonify(ResultSet=json.dumps(result))


if __name__ == '__main__':
    # 读取颜色配置文件
    config = configparser.ConfigParser()
    config.read('color.ini')
    colors = config.sections()

    # 命令行参数解析
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

    # 初始化全局变量
    algorithm = args.algorithm  # 跟踪算法
    target_color = args.color  # 目标颜色
    stream_only = args.stream_only  # 是否仅视频流模式
    is_test = args.test  # 是否测试模式

    # 启动Flask应用
    app.run(host='0.0.0.0', threaded=True)
