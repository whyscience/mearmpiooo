""" ref:
https://github.com/ECI-Robotics/opencv_remote_streaming_processing/
"""
# !/usr/bin/env python
# coding: utf-8
import configparser

import cv2

import tracking

""" 加载配置文件 """
config = configparser.ConfigParser()
config.read('config.ini')
frame_prop = eval(config.get('camera', 'frame_prop'))  # 视频帧属性


class VideoCamera(object):
    """视频摄像头类

    处理视频捕获和帧处理的主类
    """
    def __init__(self, algorithm, target_color, stream_only, is_test):
        """初始化视频摄像头

        Args:
            algorithm: 跟踪算法名称
            target_color: 目标颜色
            stream_only: 是否仅视频流模式
            is_test: 是否测试模式
        """
        """ 获取第一帧视频 """
        ##self.video = cv2.VideoCapture(0)
        self.video = cv2.VideoCapture(0, cv2.CAP_V4L)  # 使用V4L驱动打开摄像头
        ret, frame = self.video.read()
        video_prop = self._get_video_prop()  # 获取视频属性
        self.tracking = tracking.Tracking(ret, frame, video_prop, algorithm,
                                       target_color, stream_only, is_test)

    def __del__(self):
        """释放视频资源"""
        self.video.release()

    def _get_video_prop(self):
        """获取视频属性

        Returns:
            tuple: (宽度, 高度, FPS)
        """
        return self.video.get(cv2.CAP_PROP_FRAME_WIDTH), self.video.get(
            cv2.CAP_PROP_FRAME_HEIGHT), self.video.get(cv2.CAP_PROP_FPS)

    def get_frame(self, stream_only, is_test, flip_code):
        """获取处理后的视频帧

        Args:
            stream_only: 是否仅视频流模式
            is_test: 是否测试模式
            flip_code: 图像翻转代码

        Returns:
            bytes: JPEG格式的图像数据
        """
        ret, frame = self.video.read()  # 读取视频帧
        frame = cv2.resize(frame, (frame_prop[0], frame_prop[1]))  # 调整帧大小

        # 根据flip_code进行图像翻转
        if flip_code != "reset":
            frame = cv2.flip(frame, int(flip_code))

        # 获取跟踪处理后的帧
        frame = self.tracking.get_track_frame(ret, frame, stream_only, is_test)
        ret, jpeg = cv2.imencode('1.jpg', frame)  # 将帧编码为JPEG格式

        return jpeg.tostring()
