# Object tracking with MearmPi

## What's this

This is test code of object tracking with Mearm Pi.

You can do followings:
* View opencv video capture streaming via browser.
* Chose Object tracking algorithm (meanshift or camshift)
* Color Tracking configuration

[![](https://img.youtube.com/vi/vpYcX1vJjsI/0.jpg)](https://www.youtube.com/watch?v=vpYcX1vJjsI)


## Reference


MeaArmPi TechnicalOverview

This document is very helpful. Plese read this first and test demo code with your MeArmPi.
https://groups.google.com/group/mearm/attach/18a4eb363ddaa/MeArmPiTechnicalOverviewV0-2DRAFT.pdf?part=0.1


Mearm(Python library)

https://gist.github.com/bjpirt/9666d8c623cb98e755c92f1fbeeb6118


Flask Video streaming

http://blog.miguelgrinberg.com/post/video-streaming-with-flask
https://github.com/ECI-Robotics/opencv_remote_streaming_processing/

OpenCV (camshift sample code)

https://github.com/opencv/opencv/tree/master/samples/python



## Prerequisites

* MeArmPi
* Raspberry Pi 3B / PiCamera module V2
* Python 3.5

## Required Packages

You need to install packages on Raspberry Pi

* OpenCV prerequisite libraries

```sh
sudo apt update
sudo apt install pip3-python -y
sudo apt install libatlas3-base libwebp6 libtiff5 libjasper1 libilmbase12 libopenexr22 -y
sudo apt install libgstreamer1.0-0 libavcodec57 libavformat57 libswscale4 libqtgui4 libqt4-test -y
```

* Required packages with this app. 

```sh
pip3 install opencv-python
pip3 install flask
pip3 install pigpio
pip3 install picamera
```

## How to use

Make sure to be enable picamera(rasp-config) and modprobe bcm2835-v412.

```sh
sudo modprobe bcm2835-v4l2
```

You must also start pigpiod daemon.

```sh
sudo pigpiod
```

Command Option

```sh
$ python3 app.py -h
usage: app.py [-h] [-a {camshift,meanshift}] [-s] [-t]
              [-c {blue,red,yellow,green}]

opencv object tracking with MearmPi

optional arguments:
  -h, --help            show this help message and exit
  -a {camshift,meanshift}, --algorithm {camshift,meanshift}
                        select object tracking algorithm
  -s, --stream_only     stream mode (without object traking)
  -t, --test            test mode (without moving arms)
  -c {blue,red,yellow,green}, --color {blue,red,yellow,green}
```

### Object tracking settings

Define parameters in config.ini.
you might need to adjust some parameters in your environment.

```sh
[camera]
# deifne frame resolution and frame rate.
# (320 * 240  16fps : recommend setting)
frame_prop = (320, 240, 16)
# initial track area
track_area = (80, 80)
.
.
.
```

### Run app (example)

Color tracking

```sh
$ python3 app.py -c yellow
```

access to the streaming url with your browser

```txt
http://<your mearm ip addr>:5000/video_feed
```

colors are defined  in color.ini

```sh
# define hsv (hue, staturation, lightness)
[yellow]
lower = 20, 100, 100
upper = 40, 255, 255
.
.
```

## Misc

### Test Object traking with MeArm Pi in test mode.

At first, Run app.py with --test option to confirm if settings are fine.

```sh
python3 app.py --test -c yellow
```

### Test with only servos

I strongly recommend you to confirm if servo settings are correct with your MeArm Pi.

Run app.py with the arms of MeArmPi removed from servos.
You can see that servos move to the right direction.