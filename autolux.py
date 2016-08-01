#!/usr/bin/env python
# required utilities: imagemagick, xdotool, xbacklight

import time
import os
import shlex, subprocess

# BRIGHTNESS LEVELS (should be between 1 and 100)
MIN=5
MAX=20

# interpolate over our threshold (should be between 1 and 65K)
MAX_BRIGHT=50000
LOW_BRIGHT=5000

# interval between screenshots
SLEEP_TIME=3

SCREENSHOT_CMD='import -screen -w root -colorspace gray ss.png'
BRIGHTNESS_CMD='convert ss.png -format "%[mean]" info:'

FOCUSED_CMD='xdotool getwindowfocus getwindowpid'
# use getwindowname if you dare
# FOCUSED_CMD='xdotool getwindowfocus getwindowname'

def run_cmd(cmd):
  args = shlex.split(cmd)
  return subprocess.check_output(args)

def monitor_luma():
  prev_brightness = None
  prev_window = None
  cur_range = MAX_BRIGHT - LOW_BRIGHT

  while True:
    time.sleep(SLEEP_TIME)

    window = run_cmd(FOCUSED_CMD)

    if prev_window == window:
      continue

    prev_window = window

    run_cmd(SCREENSHOT_CMD)
    brightness = run_cmd(BRIGHTNESS_CMD)

    try:
      cur_mean = float(brightness)
    except Exception, e:
      print "ERROR GETTING MEAN LUMA", e
      continue


    trimmed_mean = max(min(MAX_BRIGHT, cur_mean), LOW_BRIGHT) - LOW_BRIGHT
    trimmed_mean = int(trimmed_mean / 500) * 500
    range_is = float(trimmed_mean) / float(cur_range)

    new_gamma = 1 - range_is
    new_brightness =  (MAX - MIN) * new_gamma + MIN

    if prev_brightness != new_brightness:
      print "GAMMA: %.02f" % new_gamma, "AVG LUMA: %05i" % trimmed_mean, "NEW BRIGHTNESS:", int(new_brightness)
      run_cmd("xbacklight -set %s" % new_brightness)
    prev_brightness = new_brightness

if __name__ == "__main__":
  monitor_luma()
