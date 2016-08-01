#!/usr/bin/env python
# required utilities: imagemagick, xdotool, xbacklight

import time
import os
import shlex, subprocess

# BRIGHTNESS LEVELS (should be between 1 and 100)
MIN_LEVEL=5
MAX_LEVEL=20

# interpolate over our threshold (should be between 1 and 65K)
MAX_BRIGHT=50000
MIN_BRIGHT=5000

# interval between screenshots
SLEEP_TIME=3000

TRANSITION_MS=400

SCREENSHOT_CMD='import -screen -w root -colorspace gray ss.png'
BRIGHTNESS_CMD='convert ss.png -format "%[mean]" info:'

FOCUSED_CMD='xdotool getwindowfocus getwindowpid'
# use getwindowname if you dare
# FOCUSED_CMD='xdotool getwindowfocus getwindowname'



def load_options():
  global MIN_LEVEL, MAX_LEVEL, MAX_BRIGHT, MIN_BRIGHT, SLEEP_TIME, TRANSITION_MS

  from optparse import OptionParser
  parser = OptionParser()
  parser.add_option("--min-level", dest="min_level", type="int", default=MIN_LEVEL)
  parser.add_option("--max-level", dest="max_level", type="int", default=MAX_LEVEL)
  parser.add_option("--interval", dest="interval", type="int", default=SLEEP_TIME)
  parser.add_option("--min-bright", dest="min_bright", type="int", default=MIN_BRIGHT)
  parser.add_option("--max-bright", dest="max_bright", type="int", default=MAX_BRIGHT)
  parser.add_option("--fade-time", dest="fade_time", type="int", default=TRANSITION_MS)


  options, args = parser.parse_args()
  MIN_LEVEL = options.min_level
  MAX_LEVEL = options.max_level
  SLEEP_TIME = options.interval
  MAX_LEVEL = options.max_level
  TRANSITION_MS = options.fade_time



def print_config():
  print "FADE TIME:", TRANSITION_MS
  print "SLEEP TIME:", SLEEP_TIME
  print "DISPLAY RANGE:", MIN_LEVEL, MAX_LEVEL
  print "BRIGHTNESS RANGE:", MIN_BRIGHT, MAX_BRIGHT

def run_cmd(cmd):
  args = shlex.split(cmd)
  return subprocess.check_output(args)

def monitor_luma():
  prev_brightness = None
  prev_window = None
  cur_range = MAX_BRIGHT - MIN_BRIGHT

  while True:
    time.sleep(SLEEP_TIME / 1000.0)

    try:
        window = run_cmd(FOCUSED_CMD)
    except:
        window = None

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


    trimmed_mean = max(min(MAX_BRIGHT, cur_mean), MIN_BRIGHT) - MIN_BRIGHT
    trimmed_mean = int(trimmed_mean / 500) * 500
    range_is = float(trimmed_mean) / float(cur_range)

    new_gamma = 1 - range_is
    new_level =  (MAX_LEVEL - MIN_LEVEL) * new_gamma + MIN_LEVEL

    if prev_brightness != new_level:
      print "AVG LUMA: %05i," % trimmed_mean, "NEW GAMMA: %.02f," % new_gamma, "NEW BRIGHTNESS:", "%s/%s" % (int(new_level), MAX_LEVEL)
      run_cmd("xbacklight -set %s -time %s" % (new_level, TRANSITION_MS))
    prev_brightness = new_level

if __name__ == "__main__":
  load_options()
  print_config()
  monitor_luma()