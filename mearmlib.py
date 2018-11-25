from logging import getLogger, basicConfig, DEBUG, INFO
from time import time, sleep
import threading
import configparser

logger = getLogger(__name__)
basicConfig(
    level=INFO,
    format="%(asctime)s %(levelname)s %(name)s %(funcName)s(): %(message)s")

import mearm
"""load config"""
config = configparser.ConfigParser()
config.read('config.ini')
base_by = eval(config.get('mearm', 'base_by'))
upper_by = eval(config.get('mearm', 'upper_by'))
lower_by = eval(config.get('mearm', 'lower_by'))
min_area = eval(config.get('tracking', 'min_area'))
back_arm_ratio = eval(config.get('tracking', 'back_arm_ratio'))
forward_arm_ratio = eval(config.get('tracking', 'forward_arm_ratio'))


class MearmMove(object):
    def __init__(self, is_test):
        self.is_test = is_test
        self.time_now = time()
        self.time_old = time()
        self.time_delta = 0
        self.myMeArm = mearm.MeArm()
        """update current angles at the first time"""
        if not self.is_test:
            self.myMeArm.moveToCentres()
        self.grip_t = threading.Thread(target=self._grip_mearm)
        self.grip_t.start()

    def _calc_angle(self, mearm, move_ratio, track_area_ratio):
        if mearm == "base":
            angle = round(self.myMeArm.base.maxAngle * move_ratio[0])
            if abs(angle) > base_by[1]:
                angle = base_by[1]
            if abs(angle) < base_by[0]:
                angle = base_by[0]
        elif mearm == "upper":
            angle = round(self.myMeArm.upper.maxAngle * move_ratio[1])
            if abs(angle) > upper_by[1]:
                angle = upper_by[1]
            if abs(angle) < upper_by[0]:
                angle = upper_by[0]
        elif mearm == "lower":
            angle = round(self.myMeArm.lower.maxAngle * move_ratio[1])
            if abs(angle) > lower_by[1]:
                angle = lower_by[1]
            if abs(angle) < lower_by[0]:
                angle = lower_by[0]
        return abs(angle)

    def _forward_back_mearm(self, track_area_ratio):
        if back_arm_ratio[0] < track_area_ratio < back_arm_ratio[1]:
            return lower_by[0] * -1
        elif forward_arm_ratio[0] < track_area_ratio < forward_arm_ratio[1]:
            return lower_by[0]
        else:
            logger.debug("good position{}".format(track_area_ratio))

    def _grip_mearm(self):
        self.time_now = time()
        """update time_delta
           mearm grip stars wheh time_delta exceed 2(sec)
        """
        self.time_delta = self.time_delta + (self.time_now - self.time_old)
        if self.time_delta > 2:
            logger.info(
                "!! grip close !! time_delta:{}".format(self.time_delta))
            if not self.is_test:
                self.myMeArm.moveToGrip(60)
            sleep(0.2)
            logger.info(
                "!! grip open !! time_delta:{}".format(self.time_delta))
            if not self.is_test:
                self.myMeArm.moveToGrip(30)
            sleep(0.2)
            self.time_delta = 0
        self.time_old = self.time_now

    def _move_angles(self, *args):
        logger.info("myMeArm.moveByPosition: lower {} upper {} base {}".format(
            args[0], args[1], args[2]))
        if not self.is_test:
            self.myMeArm.moveByPosition(args[0], args[1], args[2])

    def motion(self, track_window, track_area_ratio, move_ratio, video_prop,
               margin_window):
        """ get window position
            x, y, w, h :
              current positon of track window.
            xmin, ymin, xmax, ymax :
              position of margin window.
              robot arms starts to move when current position go out margin window.
        """
        x, y, w, h = track_window
        xmin, ymin, xmax, ymax = margin_window
        logger.debug(
            "track_window x, y, w, h:{}, margin_window m_x, m_y, m_w, m_h:{}".
            format(track_window, margin_window))
        """Nothing to be done when tracking object might be failed"""
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
        """mearm "grip"s object locked on"""
        if move_ratio == (0, 0):
            if not self.grip_t.is_alive():
                self.grip_t = threading.Thread(target=self._grip_mearm)
                self.grip_t.start()
            return
        """initialize angle"""
        base_angle = 0
        upper_angle = 0
        lower_angle = 0
        """move base"""
        if x < xmin:
            base_angle = self._calc_angle("base", move_ratio,
                                          track_area_ratio) * -1
        if x > xmax - w:
            base_angle = self._calc_angle("base", move_ratio, track_area_ratio)
        """move upper and lower arm"""
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
            self._move_angles(lower_angle, upper_angle, base_angle)
        if x > xmin and x < xmax - w and y > ymin and y < ymax - h:
            lower_angle = self._forward_back_mearm(track_area_ratio)
            if lower_angle:
                logger.debug("inside margin window track_area_ratio:{}".format(
                    track_area_ratio))
                self._move_angles(lower_angle, upper_angle, base_angle)