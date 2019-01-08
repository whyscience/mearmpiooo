""" ref:
https://github.com/ECI-Robotics/opencv_remote_streaming_processing/
"""

import cv2
import meanshift
import camshift
import mearmlib
from time import sleep
import configparser
import math
from timeit import default_timer as timer

""" load configuration """
config = configparser.ConfigParser()
config.read('config.ini')
frame_prop = eval(config.get('camera', 'frame_prop'))
frame_margin = eval(config.get('camera', 'frame_margin'))
track_area = eval(config.get('tracking', 'track_area'))


class Tracking(object):
    def __init__(self, ret, frame, video_prop, algorithm, target_color, stream_only, is_test):
        self.frame = frame
        self.init_track_window = self._set_track_window()
        self.track_window = self.init_track_window
        self.track_window0 = self.track_window
        self.margin_window = self._set_margin_window()

        """ Create MeArmMove instnace """
        if not stream_only:
            self.myMeArmMove = mearmlib.MearmMove(is_test)

        """ Create opencv tracking instnace """
        if algorithm == "meanshift":
            self.tracking = meanshift.MeanShift(
                frame_prop, self.margin_window, self.track_window, target_color)
        else:
            self.tracking = camshift.CamShift(
                frame_prop, self.margin_window, self.track_window, target_color)

        """ Set text put on frames """
        self.params = "{} * {} ({}) margin:{} {} {} is_test:{}".format(
            round(video_prop[0]), round(video_prop[1]), round(video_prop[2]), frame_prop, frame_margin, algorithm, target_color)
        self.track_data = "track window:{}({}) {}".format(0, 0, 0)

        """ Calcurate FPS """
        self.accum_time = 0
        self.curr_fps = 0
        self.fps = "FPS: ??"
        self.prev_time = timer()

    def __del__(self):
        self.video.release()

    def _get_video_prop(self):
        return self.video.get(cv2.CAP_PROP_FRAME_WIDTH), self.video.get(
            cv2.CAP_PROP_FRAME_HEIGHT), self.video.get(cv2.CAP_PROP_FPS)

    def _set_margin_window(self):
        frame_width, frame_height = frame_prop[:-1]
        xmargin = frame_width * frame_margin
        ymargin = frame_height * frame_margin
        return xmargin, ymargin, frame_width - xmargin, frame_height - ymargin

    def _set_track_window(self):
        frame_width, frame_height = frame_prop[:-1]
        xtrack = frame_width / 2 - (track_area[0] / 2)
        ytrack = frame_height / 2 - (track_area[1] / 2)
        return int(xtrack), int(ytrack), track_area[0], track_area[1]

    def _calc_move_ratio(self, track_window, track_window0):
        x, y, w, h = track_window
        x0, y0, w0, h0 = track_window0
        diff = (x0 - x, y0 - y, w0 - w, h0 - h)
        move_ratio = (round(diff[0] / frame_prop[0], 5),
                      round(diff[1] / frame_prop[1], 5))
        return move_ratio

    def _calc_track_area_ratio(self, track_window, track_area):
        track_area = track_area[0] * track_area[1]
        track_window_area = track_window[2] * track_window[3]
        return round(math.sqrt(track_area) / math.sqrt(track_window_area), 2)

    def get_track_frame(self, ret, frame, stream_only, is_test):
        prob = None

        if is_test:
            mode = ("test", (0, 128, 0))
        else:
            mode = ("tracking", (0, 0, 255))

        if not stream_only:
            prob, frame, track_window, track_window0 = self.tracking.object_tracking(ret, frame)
            track_area_ratio = self._calc_track_area_ratio(track_window, track_area)
            move_ratio = self._calc_move_ratio(track_window, track_window0)
            self.myMeArmMove.motion(track_window, track_area_ratio, move_ratio, self.margin_window)

            """ draw margin window on the frame"""
            xmin, ymin, xmax, ymax = self.margin_window
            self.frame = cv2.rectangle(self.frame, (
                round(xmin), round(ymin)), (round(xmax), round(ymax)), mode[1], 1)

            """ draw init window on the frame """
            init_xmin = self.init_track_window[0]
            init_ymin = self.init_track_window[1]
            init_xmax = self.init_track_window[0] + self.init_track_window[2]
            init_ymax = self.init_track_window[1] + self.init_track_window[3]
            self.frame = cv2.rectangle(self.frame, (
                round(init_xmin), round(init_ymin)), (round(init_xmax), round(init_ymax)), (128, 255, 255), 1)
            self.track_data = "track win:{} area:({}/{} {})".format(
                track_window, track_area[0] * track_area[1], track_window[2] * track_window[3], track_area_ratio)
            frame = cv2.putText(frame, self.params, (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.25, (255, 255, 255), thickness=1)
            frame = cv2.putText(frame, self.track_data, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), thickness=1)

        # Calculate FPS
        curr_time = timer()
        exec_time = curr_time - self.prev_time
        self.prev_time = curr_time
        self.accum_time = self.accum_time + exec_time
        self.curr_fps = self.curr_fps + 1
        if self.accum_time > 1:
            self.accum_time = self.accum_time - 1
            self.fps = "FPS: " + str(self.curr_fps)
            self.curr_fps = 0

        # Draw FPS in top left corner
        cv2.rectangle(frame, (frame_prop[0] - 50, 0), (frame_prop[0], 17), (255, 255, 255), -1)
        cv2.putText(frame, self.fps, (frame_prop[0] - 50 + 3, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)

        if not prob is None:
            frame = cv2.vconcat([frame, prob])

        return frame
