"""ref: 
https://docs.opencv.org/3.4/db/df8/tutorial_py_meanshift.html
https://github.com/opencv/opencv/blob/master/samples/python/camshift.py
https://docs.opencv.org/3.4.2/df/d9d/tutorial_py_colorspaces.html
"""

import numpy as np
import cv2
import configparser


class CamShift(object):
    def __init__(self, video_prop, margin_window, track_window, target_color):
        # set up initial location of window
        self.init_track_window = track_window
        self.track_window = self.init_track_window
        self.margin_window = margin_window
        self.term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10,
                          1)
        self.target_color = target_color
        if self.target_color:
            config = configparser.ConfigParser()
            config.read('color.ini')
            # define range of color in HSV
            self.lower_color = [
                int(c) for c in config[target_color]['lower'].split(',')
            ]
            self.upper_color = [
                int(c) for c in config[target_color]['upper'].split(',')
            ]

    def object_tracking(self, ret, frame):
        # begin object tracking
        if ret:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            if self.target_color:
                # Threshold the HSV image to get only blue colors
                mask = cv2.inRange(hsv,
                                   np.array(self.lower_color),
                                   np.array(self.upper_color))
            else:
                mask = cv2.inRange(hsv,
                                   np.array((0., 60., 32.)),
                                   np.array((180., 255., 255.)))

            x, y, w, h = self.track_window
            hsv_roi = hsv[y:y + h, x:x + w]
            mask_roi = mask[y:y + h, x:x + w]
            hist = cv2.calcHist([hsv_roi], [0], mask_roi, [16], [0, 180])
            cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
            self.hist = hist.reshape(-1)

            prob = cv2.calcBackProject([hsv], [0], self.hist, [0, 180], 1)
            prob &= mask

            # get location before applying camshift 
            track_window0 = self.track_window

            # apply camshift to get the new location
            ret, self.track_window = cv2.CamShift(prob, self.track_window,
                                                  self.term_crit)
            # Draw it on image
            pts = cv2.boxPoints(ret)
            pts = np.int0(pts)
            frame = cv2.polylines(frame, [pts], True, 255, 2)
            """Draw frame margin on image"""
            xmin, ymin, xmax, ymax = self.margin_window
            frame = cv2.rectangle(frame, (round(xmin), round(ymin)),
                                  (round(xmax), round(ymax)), (0, 0, 255), 1)
            """Draw track init_track_window on image"""
            xtrack_min = self.init_track_window[0]
            ytrack_min = self.init_track_window[1]
            xtrack_max = self.init_track_window[0] + self.init_track_window[2]
            ytrack_max = self.init_track_window[1] + self.init_track_window[3]
            frame = cv2.rectangle(
                frame, (round(xtrack_min), round(ytrack_min)),
                (round(xtrack_max), round(ytrack_max)), (128, 255, 255), 1)
            """convert prob image glay to bgr"""
            prob = cv2.cvtColor(prob, cv2.COLOR_GRAY2BGR)
            """concatenate fame and prob to display them on the same window
               if you dont need this, just comment out under two lines"""
            frame = cv2.vconcat([frame, prob])
            return frame, self.track_window, track_window0
