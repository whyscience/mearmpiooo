""" 参考:
https://github.com/ECI-Robotics/opencv_remote_streaming_processing/
"""
# !/usr/bin/env python
# coding: utf-8
import configparser
import math
from timeit import default_timer as timer

import cv2

import camshift
import meanshift
import mearmlib

""" 加载配置文件 """
config = configparser.ConfigParser()
config.read('config.ini')
frame_prop = eval(config.get('camera', 'frame_prop'))  # 帧属性
frame_margin = eval(config.get('camera', 'frame_margin'))  # 帧边界
track_area = eval(config.get('tracking', 'track_area'))  # 跟踪区域


class Tracking(object):
    """目标跟踪类"""
    def __init__(self, ret, frame, video_prop, algorithm, target_color,
                 stream_only, is_test):
        """初始化跟踪器

        Args:
            ret: 视频帧读取状态
            frame: 视频帧
            video_prop: 视频属性
            algorithm: 跟踪算法
            target_color: 目标颜色
            stream_only: 是否仅流模式
            is_test: 是否测试模式
        """
        self.init_track_window = self._set_track_window()  # 初始跟踪窗口
        self.track_window = self.init_track_window  # 当前跟踪窗口
        self.track_window0 = self.track_window  # 上一帧跟踪窗口
        self.margin_window = self._set_margin_window()  # 边界窗口
        """ 创建机械臂控制实例 """
        self.myMeArmMove = mearmlib.MearmMove(is_test)
        """ 创建OpenCV跟踪器实例 """
        if algorithm == "meanshift":
            self.tracking = meanshift.MeanShift(frame_prop, self.margin_window,
                                              self.track_window,
                                              target_color)
        else:
            self.tracking = camshift.CamShift(frame_prop, self.margin_window,
                                            self.track_window, target_color)
        """ 设置帧上显示的文本 """
        self.params = "{} * {} ({}) resize:{} {} {} {}".format(
            round(video_prop[0]),
            round(video_prop[1]),
            round(video_prop[2]), frame_prop, frame_margin, algorithm,
            target_color)
        self.track_data = "跟踪窗口:{}({}) {}".format(0, 0, 0)
        """ 计算FPS """
        self.accum_time = 0  # 累计时间
        self.curr_fps = 0  # 当前FPS
        self.fps = "FPS: ??"  # FPS显示文本
        self.prev_time = timer()  # 上一帧时间
        """ 初始化视频捕获 """
        self.video = cv2.VideoCapture(0, cv2.CAP_V4L)

    def __del__(self):
        """释放视频资源"""
        self.video.release()

    def _get_video_prop(self):
        """获取视频属性"""
        return self.video.get(cv2.CAP_PROP_FRAME_WIDTH), self.video.get(
            cv2.CAP_PROP_FRAME_HEIGHT), self.video.get(cv2.CAP_PROP_FPS)

    def _set_margin_window(self):
        """设置边界窗口"""
        frame_width, frame_height = frame_prop[:-1]
        xmargin = frame_width * frame_margin
        ymargin = frame_height * frame_margin
        return xmargin, ymargin, frame_width - xmargin, frame_height - ymargin

    def _set_track_window(self):
        """设置跟踪窗口"""
        frame_width, frame_height = frame_prop[:-1]
        xtrack = frame_width / 2 - (track_area[0] / 2)
        ytrack = frame_height / 2 - (track_area[1] / 2)
        return int(xtrack), int(ytrack), track_area[0], track_area[1]

    def _calc_move_ratio(self, track_window, track_window0):
        """计算移动比例

        Args:
            track_window: 当前跟踪窗口
            track_window0: 上一帧跟踪窗口

        Returns:
            移动比例元组 (x方向比例, y方向比例)
        """
        x, y, w, h = track_window
        x0, y0, w0, h0 = track_window0
        diff = (x0 - x, y0 - y, w0 - w, h0 - h)
        move_ratio = (round(diff[0] / frame_prop[0], 5),
                     round(diff[1] / frame_prop[1], 5))
        return move_ratio

    def _calc_track_area_ratio(self, track_window, track_area):
        """计算跟踪区域比例

        Args:
            track_window: 跟踪窗口
            track_area: 目标区域大小

        Returns:
            跟踪区域与目标区域的比例
        """
        track_area = track_area[0] * track_area[1]
        track_window_area = track_window[2] * track_window[3]
        return round(math.sqrt(track_area) / math.sqrt(track_window_area), 2)

    def get_track_frame(self, ret, frame, stream_only, is_test):
        """获取跟踪后的视频帧

        Args:
            ret: 帧读取状态
            frame: 输入帧
            stream_only: 是否仅流模式
            is_test: 是否测试模式

        Returns:
            处理后的视频帧
        """
        prob = None

        if is_test:
            mode = ("test", (0, 128, 0))
        else:
            mode = ("tracking", (0, 0, 255))

        if not stream_only:
            prob, frame, track_window, track_window0 = self.tracking.object_tracking(
                ret, frame)
            track_area_ratio = self._calc_track_area_ratio(track_window,
                                                         track_area)
            move_ratio = self._calc_move_ratio(track_window, track_window0)
            self.myMeArmMove.motion(track_window, track_area_ratio, move_ratio,
                                  self.margin_window, is_test)
            """ 在帧上绘制边界窗口 """
            xmin, ymin, xmax, ymax = self.margin_window
            frame = cv2.rectangle(frame, (round(xmin), round(ymin)),
                                (round(xmax), round(ymax)), mode[1], 1)
            """ 在帧上绘制初始窗口 """
            init_xmin = self.init_track_window[0]
            init_ymin = self.init_track_window[1]
            init_xmax = self.init_track_window[0] + self.init_track_window[2]
            init_ymax = self.init_track_window[1] + self.init_track_window[3]
            frame = cv2.rectangle(frame, (round(init_xmin), round(init_ymin)),
                                  (round(init_xmax), round(init_ymax)),
                                  (128, 255, 255), 1)
            self.track_data = "track win:{} area:({}/{} {})".format(
                track_window, track_area[0] * track_area[1],
                track_window[2] * track_window[3], track_area_ratio)
            frame = cv2.putText(
                frame,
                self.params, (10, 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.25, (255, 255, 255),
                thickness=1)
            frame = cv2.putText(
                frame,
                self.track_data, (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.3, (255, 255, 255),
                thickness=1)
            frame = cv2.putText(
                frame,
                "mode:" + mode[0], (10, frame_prop[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.3,
                mode[1],
                thickness=1)

        # 计算FPS
        curr_time = timer()
        exec_time = curr_time - self.prev_time
        self.prev_time = curr_time
        self.accum_time = self.accum_time + exec_time
        self.curr_fps = self.curr_fps + 1
        if self.accum_time > 1:
            self.accum_time = self.accum_time - 1
            self.fps = "FPS: " + str(self.curr_fps)
            self.curr_fps = 0

        # 在左上角绘制FPS
        cv2.rectangle(frame, (frame_prop[0] - 50, 0), (frame_prop[0], 17),
                     (255, 255, 255), -1)
        cv2.putText(frame, self.fps, (frame_prop[0] - 50 + 3, 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)

        if prob is not None:
            frame = cv2.vconcat([frame, prob])

        return frame
