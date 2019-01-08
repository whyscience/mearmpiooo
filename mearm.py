""" ref:
https://gist.github.com/bjpirt/9666d8c623cb98e755c92f1fbeeb6118
https://groups.google.com/group/mearm/attach/18a4eb363ddaa/MeArmPiTechnicalOverviewV0-2DRAFT.pdf?part=0.1
"""

import math
import pigpio
from logging import getLogger, basicConfig, DEBUG

logger = getLogger(__name__)
basicConfig(
    level=DEBUG, format="%(asctime)s %(levelname)s %(name)s :%(message)s")

pi = pigpio.pi()

safe_angle = 25


class Servo:
    def __init__(self, config):
        self.pin = config['pin']
        self.min = config['min']
        self.max = config['max']
        self.minAngle = config['minAngle']
        self.maxAngle = config['maxAngle']

    def moveTo(self, angle):
        self.moveToAngle(angle)

    def moveBy(self, angle):
        newAngle = self.currentAngle + angle
        self.moveToAngle(newAngle)

    def moveToCentre(self):
        centre = self.minAngle + (self.maxAngle - self.minAngle) / 2
        self.moveToAngle(centre)

    def moveToAngle(self, angle):
        """ prevent MeArmPi from moving so far (angle: +- safe_angle) """
        if angle > self.maxAngle - safe_angle:
            angle = self.maxAngle - safe_angle
        if angle < self.minAngle + safe_angle:
            angle = self.minAngle + safe_angle
        self.currentAngle = angle
        self.updateServo()

    def updateServo(self):
        pulseWidth = math.floor(self.min + ((float(
            self.currentAngle - self.minAngle) / float(
                self.maxAngle - self.minAngle)) * (self.max - self.min)))
        logger.debug("updateServo currentAngle:{} pin:{} pulseWidth:{}".format(
            self.currentAngle, self.pin, pulseWidth))
        pi.set_servo_pulsewidth(self.pin, pulseWidth)


class MeArm:
    def __init__(self):
        # ref. https://github.com/mimeindustries/mearm-js/blob/master/lib/MeArmPi.js
        self.lower = Servo({
            'pin': 17,
            'min': 1300,
            'max': 2400,
            'minAngle': 0,
            'maxAngle': 135
        })
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

    def moveToBase(self, angle):
        self.base.moveTo(angle)

    def moveToPosition(self, lower, upper, base, grip):
        self.lower.moveTo(lower)
        self.upper.moveTo(upper)
        self.base.moveTo(base)
        self.grip.moveTo(grip)

    """
    def moveByPosition(self, lower, upper, base, grip):
        self.lower.moveBy(lower)
        self.upper.moveBy(upper)
        self.base.moveBy(base)
        self.grip.moveBy(grip)
    """

    def moveByPosition(self, lower, upper, base):
        self.lower.moveBy(lower)
        self.upper.moveBy(upper)
        self.base.moveBy(base)

    def moveByBase(self, angle):
        self.base.moveBy(angle)

    def moveByUpper(self, angle):
        self.upper.moveBy(angle)

    def moveByLower(self, angle):
        self.lower.moveBy(angle)

    def moveToGrip(self, angle):
        self.grip.moveTo(angle)

    def moveToCentres(self):
        self.base.moveToCentre()
        self.lower.moveToCentre()
        self.upper.moveToCentre()
        self.grip.moveToCentre()
