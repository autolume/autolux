# xbacklight: control backlight brightness on linux using the sys filesystem
#             with a backward-compatibile user interface
# Copyright(c) 2016 by wave++ "Yuri D'Elia" <wavexx@thregr.org>
# -*- coding: utf-8 -*-
# FROM: https://github.com/wavexx/acpilight/blob/master/xbacklight
# LICENSE: GPLv3+
from __future__ import print_function, division

APP_DESC = "control backlight brightness"
SYS_PATH = "/sys/class/backlight"

import argparse
import os, sys
import time


def error(msg):
    print(sys.argv[0] + ": " + msg)

def get_controllers():
    return os.listdir(SYS_PATH)

def list_controllers(ctrls):
    for ctrl in ctrls:
        print(ctrl)

def can_use():
    return os.path.exists(SYS_PATH)

class Controller(object):
    def __init__(self, ctrl):
        self._brightness_path = os.path.join(SYS_PATH, ctrl, "brightness")
        self._max_brightness = int(open(os.path.join(
            SYS_PATH, ctrl, "max_brightness")).read())

    def raw_brightness(self):
        return int(open(self._brightness_path).read())

    def brightness(self):
        return self.raw_brightness() * 100 // self._max_brightness

#################################
from run_cmd import run_cmd

def set_brightness(new_level, time):
    run_cmd("xbacklight -set %s -time %s" % (new_level, time))


def get_brightness():
    if not can_use():
      ret = float(run_cmd("xbacklight -get"))
      return ret
    else:
      ctrls = get_controllers()
      ctrl = Controller(ctrls[0])
      ret = float(ctrl.brightness())
      return ret
