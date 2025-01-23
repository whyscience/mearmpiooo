# !/usr/bin/env python
# coding: utf-8
import configparser
import threading
from logging import getLogger, basicConfig, INFO
from time import time, sleep

logger = getLogger(__name__)
basicConfig(
    level=INFO,
    format="%(asctime)s %(levelname)s %(name)s %(funcName)s(): %(message)s")

import mearm

""" 加载配置文件 """
config = configparser.ConfigParser()
config.read('config.ini')
# 从配置文件读取机械臂各个关节的运动范围限制
base_by = eval(config.get('mearm', 'base_by'))  # 底座旋转范围
upper_by = eval(config.get('mearm', 'upper_by'))  # 上臂运动范围
lower_by = eval(config.get('mearm', 'lower_by'))  # 下臂运动范围
min_area = eval(config.get('tracking', 'min_area'))  # 最小跟踪区域
back_arm_ratio = eval(config.get('tracking', 'back_arm_ratio'))  # 后退臂比例
forward_arm_ratio = eval(config.get('tracking', 'forward_arm_ratio'))  # 前进臂比例


class MearmMove(object):
    """机械臂运动控制类"""
    def __init__(self, is_test):
        self.is_test = is_test
        self.time_now = time()  # 当前时间
        self.time_old = time()  # 上一次时间
        self.time_delta = 0  # 时间差
        self.my_mearm = mearm.MeArm()  # 初始化机械臂对象
        """ 首次更新当前角度 """
        self.my_mearm.move_to_centres()
        # 创建夹持器控制线程
        self.grip_t = threading.Thread(target=self._grip_mearm)
        self.grip_t.start()

    def _calc_angle(self, mearm, move_ratio, track_area_ratio):
        """计算各关节运动角度

        Args:
            mearm: 机械臂关节名称 ("base", "upper", "lower")
            move_ratio: 移动比例
            track_area_ratio: 跟踪区域比例

        Returns:
            计算后的角度值
        """
        angle = 0
        if mearm == "base":  # 底座旋转角度计算
            angle = round(self.my_mearm.base.maxAngle * move_ratio[0])
            if abs(angle) > base_by[1]:
                angle = base_by[1]
            if abs(angle) < base_by[0]:
                angle = base_by[0]
        elif mearm == "upper":  # 上臂角度计算
            angle = round(self.my_mearm.upper.maxAngle * move_ratio[1])
            if abs(angle) > upper_by[1]:
                angle = upper_by[1]
            if abs(angle) < upper_by[0]:
                angle = upper_by[0]
        elif mearm == "lower":  # 下臂角度计算
            angle = round(self.my_mearm.lower.maxAngle * move_ratio[1])
            if abs(angle) > lower_by[1]:
                angle = lower_by[1]
            if abs(angle) < lower_by[0]:
                angle = lower_by[0]
        return abs(angle)

    def _forward_back_mearm(self, track_area_ratio):
        """根据跟踪区域比例计算前进/后退动作

        Args:
            track_area_ratio: 跟踪区域比例

        Returns:
            计算后的下臂角度
        """
        if back_arm_ratio[0] < track_area_ratio < back_arm_ratio[1]:
            return lower_by[0] * -1  # 后退
        elif forward_arm_ratio[0] < track_area_ratio < forward_arm_ratio[1]:
            return lower_by[0]  # 前进
        else:
            logger.debug("当前位置合适{}".format(track_area_ratio))

    def _grip_mearm(self):
        """控制夹持器开合
        当时间差超过2秒时执行夹持动作
        """
        self.time_now = time()
        """ 更新时间差
            当时间差超过2秒时开始夹持动作
        """
        self.time_delta = self.time_delta + (self.time_now - self.time_old)
        if self.time_delta > 2:
            logger.info(
                "!! grip close !! time_delta:{}".format(self.time_delta))
            if not self.is_test:
                self.my_mearm.move_to_grip(60)
            sleep(0.2)
            logger.info(
                "!! grip open !! time_delta:{}".format(self.time_delta))
            if not self.is_test:
                self.my_mearm.move_to_grip(30)
            sleep(0.2)
            self.time_delta = 0
        self.time_old = self.time_now

    def _move_angles(self, *args):
        """移动机械臂到指定角度

        Args:
            args[0]: 下臂角度
            args[1]: 上臂角度
            args[2]: 底座角度
        """
        logger.info("机械臂移动位置: 下臂 {} 上臂 {} 底座 {}".format(
            args[0], args[1], args[2]))
        if not self.is_test:
            self.my_mearm.move_by_position(args[0], args[1], args[2])

    def motion(self, track_window, track_area_ratio, move_ratio, margin_window,
               is_test):
        """机械臂运动主控制函数

        Args:
            track_window: 跟踪窗口 (x, y, w, h)
            track_area_ratio: 跟踪区域比例
            move_ratio: 移动比例
            margin_window: 边界窗口 (xmin, ymin, xmax, ymax)
            is_test: 是否测试模式
        """
        self.is_test = is_test
        """ 获取窗口位置
            x, y, w, h: 当前跟踪窗口的位置
            xmin, ymin, xmax, ymax: 边界窗口的位置
            当当前位置超出边界窗口时，机械臂开始移动
        """
        x, y, w, h = track_window
        xmin, ymin, xmax, ymax = margin_window
        logger.debug(
            "track_window x, y, w, h:{}, margin_window m_x, m_y, m_w, m_h:{}".
            format(track_window, margin_window))
        """ 当跟踪可能失败时不执行动作 """
        if x < xmin and x + w > xmax or y < ymin and y + h > ymax:
            logger.debug(
                "tracking might be failed: track_window area is larger than margin_window area: track_window:{}, margin_window:{}".
                format(track_window, margin_window))
            return
        elif track_window[2] * track_window[3] < min_area:
            logger.debug(
                "tacking might be failed: track_window area is smaller than {} w:{}, h:{}".
                format(min_area, w, h))
            return
        """ 当锁定目标时执行夹持动作 """
        if move_ratio == (0, 0):
            if not self.grip_t.is_alive():
                self.grip_t = threading.Thread(target=self._grip_mearm)
                self.grip_t.start()
            return
        """ 初始化角度 """
        base_angle = 0
        upper_angle = 0
        lower_angle = 0
        """ 控制底座旋转 """
        if x < xmin:
            base_angle = self._calc_angle("base", move_ratio,
                                          track_area_ratio) * -1
        if x > xmax - w:
            base_angle = self._calc_angle("base", move_ratio, track_area_ratio)
        """ 控制上下臂移动 """
        if y < ymin:
            upper_angle = self._calc_angle("upper", move_ratio,
                                           track_area_ratio)
            lower_angle = self._calc_angle("upper", move_ratio,
                                           track_area_ratio) * -1
        if y > ymax - h:
            upper_angle = self._calc_angle("upper", move_ratio,
                                           track_area_ratio) * -1
            lower_angle = self._calc_angle("upper", move_ratio,
                                           track_area_ratio)
        if base_angle or upper_angle or lower_angle != 0:
            logger.debug("lower_angle, upper_angle, base_angle:{} {} {}".
                         format(lower_angle, upper_angle, base_angle))
            self._move_angles(lower_angle, upper_angle, base_angle)
        if xmin < x < xmax - w and ymin < y < ymax - h:
            lower_angle = self._forward_back_mearm(track_area_ratio)
            if lower_angle:
                logger.debug("inside margin window track_area_ratio:{}".format(
                    track_area_ratio))
                self._move_angles(lower_angle, upper_angle, base_angle)
