###############################################################################
#                          License Agreement
#               For Open Source Computer Vision Library
#                       (3-clause BSD License)
#
# Copyright (C) 2000-2018, Intel Corporation, all rights reserved.
# Copyright (C) 2009-2011, Willow Garage Inc., all rights reserved.
# Copyright (C) 2009-2016, NVIDIA Corporation, all rights reserved.
# Copyright (C) 2010-2013, Advanced Micro Devices, Inc., all rights reserved.
# Copyright (C) 2015-2016, OpenCV Foundation, all rights reserved.
# Copyright (C) 2015-2016, Itseez Inc., all rights reserved.
# Third party copyrights are property of their respective owners.
#
# Released under the MIT license
# https://github.com/opencv/opencv/blob/master/LICENSE
#
###############################################################################
# !/usr/bin/env python
# coding: utf-8
import configparser

import cv2
import numpy as np


class MeanShift(object):
    """MeanShift目标跟踪类"""
    def __init__(self, video_prop, margin_window, track_window, target_color):
        """初始化MeanShift跟踪器

        Args:
            video_prop: 视频属性
            margin_window: 边界窗口
            track_window: 跟踪窗口
            target_color: 目标颜色
        """
        # 设置窗口的初始位置
        self.init_track_window = track_window  # 初始跟踪窗口
        self.track_window = self.init_track_window  # 当前跟踪窗口
        self.margin_window = margin_window  # 边界窗口
        # 设置终止条件
        self.term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
        self.target_color = target_color
        if self.target_color:
            config = configparser.ConfigParser()
            config.read('color.ini')
            # 在HSV色彩空间中定义颜色范围
            self.lower_color = [
                int(c) for c in config[target_color]['lower'].split(',')
            ]  # 颜色下限
            self.upper_color = [
                int(c) for c in config[target_color]['upper'].split(',')
            ]  # 颜色上限

    def object_tracking(self, ret, frame):
        """执行目标跟踪

        Args:
            ret: 帧读取状态
            frame: 输入帧

        Returns:
            tuple: (概率图, 处理后的帧, 当前跟踪窗口, 上一帧跟踪窗口)
        """
        # 开始目标跟踪
        if ret:
            # 将图像转换到HSV色彩空间
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            if self.target_color:
                # 根据设定的颜色范围进行阈值处理
                mask = cv2.inRange(hsv,
                                 np.array(self.lower_color),
                                 np.array(self.upper_color))
            else:
                # 使用默认的颜色范围
                mask = cv2.inRange(hsv,
                                 np.array((0., 60., 32.)),
                                 np.array((180., 255., 255.)))

            # 提取跟踪窗口区域
            x, y, w, h = self.track_window
            hsv_roi = hsv[y:y + h, x:x + w]
            mask_roi = mask[y:y + h, x:x + w]
            # 计算直方图
            hist = cv2.calcHist([hsv_roi], [0], mask_roi, [16], [0, 180])
            cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
            self.hist = hist.reshape(-1)

            # 计算反向投影
            prob = cv2.calcBackProject([hsv], [0], self.hist, [0, 180], 1)
            # 使用掩码更新概率图
            prob = cv2.bitwise_and(prob, mask)

            # 保存应用MeanShift之前的位置
            track_window0 = self.track_window

            # 应用MeanShift算法获取新的位置
            ret, self.track_window = cv2.meanShift(prob.astype(np.uint8),
                                                 self.track_window,
                                                 self.term_crit)

            # 在图像上绘制跟踪框
            frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0),
                                2)
            """ 在图像上绘制边界框 """
            xmin, ymin, xmax, ymax = self.margin_window
            frame = cv2.rectangle(frame, (round(xmin), round(ymin)),
                                (round(xmax), round(ymax)), (0, 0, 255), 1)

            """ 将概率图转换为BGR格式 """
            prob = cv2.cvtColor(prob.astype(np.uint8), cv2.COLOR_GRAY2BGR)

            return prob, frame, self.track_window, track_window0
