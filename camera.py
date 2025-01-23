""" ref:
https://github.com/ECI-Robotics/opencv_remote_streaming_processing/
"""

import configparser

import cv2

import tracking

""" load configuration """
config = configparser.ConfigParser()
config.read('config.ini')
frame_prop = eval(config.get('camera', 'frame_prop'))


class VideoCamera(object):
    def __init__(self, algorithm, target_color, stream_only, is_test):
        """ get first frame of Video """
        ##self.video = cv2.VideoCapture(0)
        self.video = cv2.VideoCapture(0, cv2.CAP_V4L)
        ret, frame = self.video.read()
        video_prop = self._get_video_prop()
        self.tracking = tracking.Tracking(ret, frame, video_prop, algorithm,
                                          target_color, stream_only, is_test)

    def __del__(self):
        self.video.release()

    def _get_video_prop(self):
        return self.video.get(cv2.CAP_PROP_FRAME_WIDTH), self.video.get(
            cv2.CAP_PROP_FRAME_HEIGHT), self.video.get(cv2.CAP_PROP_FPS)

    def get_frame(self, stream_only, is_test, flip_code):
        ret, frame = self.video.read()
        frame = cv2.resize(frame, (frame_prop[0], frame_prop[1]))

        if flip_code != "reset":
            frame = cv2.flip(frame, int(flip_code))

        frame = self.tracking.get_track_frame(ret, frame, stream_only, is_test)
        ret, jpeg = cv2.imencode('1.jpg', frame)

        return jpeg.tostring()
