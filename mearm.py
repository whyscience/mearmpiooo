""" 参考:
https://gist.github.com/bjpirt/9666d8c623cb98e755c92f1fbeeb6118
https://groups.google.com/group/mearm/attach/18a4eb363ddaa/MeArmPiTechnicalOverviewV0-2DRAFT.pdf?part=0.1
"""
# !/usr/bin/env python
# coding: utf-8

import math
from logging import getLogger, basicConfig, DEBUG

import pigpio

logger = getLogger(__name__)
basicConfig(
    level=DEBUG, format="%(asctime)s %(levelname)s %(name)s :%(message)s")

pi = pigpio.pi()

safe_angle = 25  # 安全角度限制


class Servo:
    """舵机控制类"""
    def __init__(self, config):
        """初始化舵机参数

        Args:
            config: 舵机配置字典，包含以下参数:
                pin: GPIO引脚号
                min: 最小脉冲宽度
                max: 最大脉冲宽度
                minAngle: 最小角度
                maxAngle: 最大角度
        """
        self.currentAngle = None  # 当前角度
        self.pin = config['pin']  # GPIO引脚
        self.min = config['min']  # 最小脉冲宽度
        self.max = config['max']  # 最大脉冲宽度
        self.minAngle = config['minAngle']  # 最小角度
        self.maxAngle = config['maxAngle']  # 最大角度

    def move_to(self, angle):
        """移动到指定角度"""
        self.move_to_angle(angle)

    def move_by(self, angle):
        """按相对角度移动"""
        new_angle = self.currentAngle + angle
        self.move_to_angle(new_angle)

    def move_to_centre(self):
        """移动到中心位置"""
        centre = self.minAngle + (self.maxAngle - self.minAngle) / 2
        self.move_to_angle(centre)

    def move_to_angle(self, angle):
        """移动到指定角度，并进行安全限制

        防止机械臂移动过远(角度限制在 ±safe_angle 范围内)
        """
        if angle > self.maxAngle - safe_angle:
            angle = self.maxAngle - safe_angle
        if angle < self.minAngle + safe_angle:
            angle = self.minAngle + safe_angle
        self.currentAngle = angle
        self.update_servo()

    def update_servo(self):
        """更新舵机位置

        将角度值转换为脉冲宽度，并设置舵机
        """
        pulseWidth = math.floor(self.min + ((float(
            self.currentAngle - self.minAngle) / float(
            self.maxAngle - self.minAngle)) * (self.max - self.min)))
        logger.debug("更新舵机 当前角度:{} 引脚:{} 脉冲宽度:{}".format(
            self.currentAngle, self.pin, pulseWidth))
        pi.set_servo_pulsewidth(self.pin, pulseWidth)


class MeArm:
    """机械臂控制类"""
    def __init__(self):
        # 参考: https://github.com/mimeindustries/mearm-js/blob/master/lib/MeArmPi.js
        # 从前面看 右边的舵机 - 控制下臂
        self.lower = Servo({
            'pin': 17,
            'min': 1300,
            'max': 2400,
            'minAngle': 0,
            'maxAngle': 135
        })
        # 从后面看 左边的舵机 - 控制上臂
        self.upper = Servo({
            'pin': 22,
            'min': 530,
            'max': 2000,
            'minAngle': 0,
            'maxAngle': 135
        })
        # 底座舵机 - 控制左右旋转
        self.base = Servo({
            'pin': 4,
            'min': 530,
            'max': 2400,
            'minAngle': -90,
            'maxAngle': 90
        })
        # 夹持器舵机
        self.grip = Servo({
            'pin': 10,
            'min': 1400,
            'max': 2400,
            'minAngle': 0,
            'maxAngle': 90
        })

    def move_to_base(self, angle):
        """移动底座到指定角度"""
        self.base.move_to(angle)

    def move_to_position(self, lower, upper, base, grip):
        """移动所有关节到指定角度

        Args:
            lower: 下臂角度
            upper: 上臂角度
            base: 底座角度
            grip: 夹持器角度
        """
        self.lower.move_to(lower)
        self.upper.move_to(upper)
        self.base.move_to(base)
        self.grip.move_to(grip)

    def move_by_position(self, lower, upper, base):
        """按相对角度移动关节

        Args:
            lower: 下臂相对角度
            upper: 上臂相对角度
            base: 底座相对角度
        """
        self.lower.move_by(lower)
        self.upper.move_by(upper)
        self.base.move_by(base)

    def move_by_base(self, angle):
        """底座按相对角度移动"""
        self.base.move_by(angle)

    def move_by_upper(self, angle):
        """上臂按相对角度移动"""
        self.upper.move_by(angle)

    def move_by_lower(self, angle):
        """下臂按相对角度移动"""
        self.lower.move_by(angle)

    def move_to_grip(self, angle):
        """移动夹持器到指定角度"""
        self.grip.move_to(angle)

    def move_to_centres(self):
        """移动所有关节到中心位置"""
        self.base.move_to_centre()
        self.lower.move_to_centre()
        self.upper.move_to_centre()
        self.grip.move_to_centre()
