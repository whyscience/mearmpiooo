"""ref:
https://blog.miguelgrinberg.com/post/video-streaming-with-flask
https://github.com/ECI-Robotics/opencv_remote_streaming_processing/
"""

import cv2
import meanshift
import camshift
import mearmlib
from time import sleep
from logging import getLogger, basicConfig, DEBUG, INFO
import configparser
import math

logger = getLogger(__name__)
basicConfig(
    level=INFO,
    format="%(asctime)s %(levelname)s %(name)s %(funcName)s(): %(message)s")
"""load config"""
config = configparser.ConfigParser()
config.read('config.ini')
frame_prop = eval(config.get('camera', 'frame_prop'))
frame_margin = eval(config.get('camera', 'frame_margin'))
flipcode = eval(config.get('camera', 'flipcode'))
track_area = eval(config.get('tracking', 'track_area'))


class VideoCamera(object):
    def __init__(self, algorithm, target_color, stream_only, is_test):
        self.video = cv2.VideoCapture(0)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, frame_prop[0])
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_prop[1])
        self.video.set(cv2.CAP_PROP_FPS, frame_prop[2])
        """get video prop again
          because "The returned value might be different from what really used by the device
          effective behaviour depends from device driver and API Backend"
          https://docs.opencv.org/3.4.0/d8/dfe/classcv_1_1VideoCapture.html#aa6480e6972ef4c00d74814ec841a2939
        """
        self.video_prop = self._get_video_prop()
        self.stream_only = stream_only
        self.margin_window = self._set_margin_window()
        self.track_window = self._set_track_window()
        if not self.stream_only:
            self.myMeArmMove = mearmlib.MearmMove(is_test)
        if algorithm == "meanshift":
            self.tracking = meanshift.MeanShift(
                self.video_prop, self.margin_window, self.track_window,
                target_color)
        else:
            self.tracking = camshift.CamShift(self.video_prop,
                                              self.margin_window,
                                              self.track_window, target_color)
        self.params = "{} * {} ({}) {} {} {} is_test:{}".format(
            self.video_prop[0], self.video_prop[1], self.video_prop[2],
            frame_margin, algorithm, target_color, is_test)

    def __del__(self):
        self.video.release()

    def _get_video_prop(self):
        return self.video.get(cv2.CAP_PROP_FRAME_WIDTH), self.video.get(
            cv2.CAP_PROP_FRAME_HEIGHT), self.video.get(cv2.CAP_PROP_FPS)

    def _set_margin_window(self):
        frame_width, frame_height = self.video_prop[:-1]
        xmargin = frame_width * frame_margin
        ymargin = frame_height * frame_margin
        return xmargin, ymargin, frame_width - xmargin, frame_height - ymargin

    def _set_track_window(self):
        frame_width, frame_height = self.video_prop[:-1]
        xtrack = frame_width / 2 - (track_area[0] / 2)
        ytrack = frame_height / 2 - (track_area[1] / 2)
        return int(xtrack), int(ytrack), track_area[0], track_area[1]

    def _calc_move_ratio(self, track_window, track_window0):
        x, y, w, h = track_window
        x0, y0, w0, h0 = track_window0
        diff = (x0 - x, y0 - y, w0 - w, h0 - h)
        move_ratio = (round(diff[0] / self.video_prop[0], 5),
                      round(diff[1] / self.video_prop[1], 5))
        return move_ratio

    def _calc_track_area_ratio(self, track_window, track_area):
        track_area = track_area[0] * track_area[1]
        track_window_area = track_window[2] * track_window[3]
        return round(math.sqrt(track_area) / math.sqrt(track_window_area), 2)

    def get_frame(self):
        ret, frame = self.video.read()
        frame = cv2.flip(frame, flipcode)
        if not self.stream_only:
            frame, track_window, track_window0 = self.tracking.object_tracking(
                ret, frame)
            track_area_ratio = self._calc_track_area_ratio(track_window,
                                                           track_area)
            move_ratio = self._calc_move_ratio(track_window, track_window0)
            self.myMeArmMove.motion(track_window, track_area_ratio, move_ratio,
                                    self.video_prop, self.margin_window)
            track_data = "track win:{} area:({}/{} {})".format(
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
                track_data, (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.3, (255, 255, 255),
                thickness=1)
        ret, jpeg = cv2.imencode('1.jpg', frame)
        return jpeg.tostring()
