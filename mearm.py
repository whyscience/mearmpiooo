""" ref:
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

safe_angle = 25


class Servo:
    def __init__(self, config):
        self.currentAngle = None
        self.pin = config['pin']
        self.min = config['min']
        self.max = config['max']
        self.minAngle = config['minAngle']
        self.maxAngle = config['maxAngle']

    def move_to(self, angle):
        self.move_to_angle(angle)

    def move_by(self, angle):
        new_angle = self.currentAngle + angle
        self.move_to_angle(new_angle)

    def move_to_centre(self):
        centre = self.minAngle + (self.maxAngle - self.minAngle) / 2
        self.move_to_angle(centre)

    def move_to_angle(self, angle):
        """ prevent MeArmPi from moving so far (angle: +- safe_angle) """
        if angle > self.maxAngle - safe_angle:
            angle = self.maxAngle - safe_angle
        if angle < self.minAngle + safe_angle:
            angle = self.minAngle + safe_angle
        self.currentAngle = angle
        self.update_servo()

    def update_servo(self):
        pulseWidth = math.floor(self.min + ((float(
            self.currentAngle - self.minAngle) / float(
            self.maxAngle - self.minAngle)) * (self.max - self.min)))
        logger.debug("updateServo currentAngle:{} pin:{} pulseWidth:{}".format(
            self.currentAngle, self.pin, pulseWidth))
        pi.set_servo_pulsewidth(self.pin, pulseWidth)


class MeArm:
    def __init__(self):
        # ref. https://github.com/mimeindustries/mearm-js/blob/master/lib/MeArmPi.js
        # 从前面看 右边的舵机
        self.lower = Servo({
            'pin': 17,
            'min': 1300,
            'max': 2400,
            'minAngle': 0,
            'maxAngle': 135
        })
        # 从后面看 左边的舵机
        self.upper = Servo({
            'pin': 22,
            'min': 530,
            'max': 2000,
            'minAngle': 0,
            'maxAngle': 135
        })
        self.base = Servo({
            'pin': 4,
            'min': 530,
            'max': 2400,
            'minAngle': -90,
            'maxAngle': 90
        })
        self.grip = Servo({
            'pin': 10,
            'min': 1400,
            'max': 2400,
            'minAngle': 0,
            'maxAngle': 90
        })

    def move_to_base(self, angle):
        self.base.move_to(angle)

    def move_to_position(self, lower, upper, base, grip):
        self.lower.move_to(lower)
        self.upper.move_to(upper)
        self.base.move_to(base)
        self.grip.move_to(grip)

    """
    def moveByPosition(self, lower, upper, base, grip):
        self.lower.moveBy(lower)
        self.upper.moveBy(upper)
        self.base.moveBy(base)
        self.grip.moveBy(grip)
    """

    def move_by_position(self, lower, upper, base):
        self.lower.move_by(lower)
        self.upper.move_by(upper)
        self.base.move_by(base)

    def move_by_base(self, angle):
        self.base.move_by(angle)

    def move_by_upper(self, angle):
        self.upper.move_by(angle)

    def move_by_lower(self, angle):
        self.lower.move_by(angle)

    def move_to_grip(self, angle):
        self.grip.move_to(angle)

    def move_to_centres(self):
        self.base.move_to_centre()
        self.lower.move_to_centre()
        self.upper.move_to_centre()
        self.grip.move_to_centre()
