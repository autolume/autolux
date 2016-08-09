#!/usr/bin/env python
# required utilities: imagemagick, xdotool, xbacklight

import time
import os
import shlex, subprocess
import math


# BRIGHTNESS LEVELS (should be between 1 and 100)
MIN_LEVEL=5
MAX_LEVEL=20

# interpolate over our threshold (should be between 1 and 65K)
MAX_BRIGHT=50000
MIN_BRIGHT=5000

# interval between screenshots
SLEEP_TIME=67
SCREENSHOT_TIME=1200
TRANSITION_MS=800
RECALIBRATE_MS=60 * 1000

LUMA_BUCKET=500
LUMA_SPREAD=5000
# for a luma map, what we hold is:
# time of day -> luma -> [p1,p2,p3]
LUMA_MAP = {}

import os
LUMA_FILE=None
LUMA_FILE_DEFAULT = os.path.expanduser("~/.config/autolux.luma_map")


# EXAMPLE: 100x200+300+400
# 100 width, 200 height, 300 offset from left, 400 offset from top
CROP_SCREEN="10x100%+400+0"
HORIZ_CROP_SCREEN="90%x10+200+400"

SCREENSHOT_CMD='import -colorspace gray -screen -w root -quality 20'
BRIGHTNESS_CMD='-format "%[mean]" info:'

# change brightness when PID changes or
# change brightness when window changes
CHECK_PID=False
CHECK_PID_CMD='xdotool getwindowfocus getwindowpid'
# change brightness when window name changes
CHECK_TITLE_CMD='xdotool getwindowfocus getwindowname'

# default to True, now that we can skip using xbacklight
LEARN_MODE=True
VIZ_LUMA_MAP=False

VERBOSE=False
def load_options():
  global MIN_LEVEL, MAX_LEVEL, MAX_BRIGHT, MIN_BRIGHT, CROP_SCREEN
  global SLEEP_TIME, TRANSITION_MS, RECALIBRATE_MS, SCREENSHOT_TIME
  global VERBOSE, CHECK_PID, LEARN_MODE,VIZ_LUMA_MAP
  global LUMA_FILE

  from optparse import OptionParser
  parser = OptionParser()
  parser.add_option("--min", "--min-level", dest="min_level", type="int", default=MIN_LEVEL,
    help="min brightness level (from 1 to 100, default is %s)" % MIN_LEVEL)
  parser.add_option("--max", "--max-level", dest="max_level", type="int", default=MAX_LEVEL,
    help="max brightness level (from 1 to 100, default is %s)" % MAX_LEVEL)
  parser.add_option("--interval", dest="interval", type="int", default=SCREENSHOT_TIME,
    help="take screen snapshot every INTERVAL ms and readjust the screen brightness, default is %s" % SCREENSHOT_TIME)
  parser.add_option("--lower", "--lower-threshold", dest="min_bright", type="int", default=MIN_BRIGHT,
    help="upper brightness threshold before setting screen to lowest brightness (45K to 65K, default is %s)" % MIN_BRIGHT)
  parser.add_option("--upper", "--upper-threshold", dest="max_bright", type="int", default=MAX_BRIGHT,
  help="lower brightness threshold before setting screen to highest brightness (1K to 15K, default is %s)" % MIN_BRIGHT)
  parser.add_option("--recalibrate-time", dest="recalibrate", type="int",
    default=RECALIBRATE_MS, help="ms before recalibrating even if the window hasn't changed. set to 0 to disable, default is 60K")
  parser.add_option("--fade-time", dest="fade_time", type="int", default=TRANSITION_MS,
    help="time to fade backlight in ms, default is %s" % TRANSITION_MS)
  parser.add_option("--crop", dest="crop_screen", type='str', default=CROP_SCREEN,
    help="area to inspect, use imagemagick geometry style string (f.e. 50%x20%+400+100 means 50% width, 20% height at offset 400x and 100y)")
  parser.add_option("--verbose", dest="verbose", action="store_true", help="turn on verbose output, including screenshot timing info")
  parser.add_option("--pid", dest="check_pid", action="store_true", help="check screen brightness when PID changes")
  parser.add_option("--title", dest="check_pid", action="store_false", help="check screen brightness when window changes")
  parser.add_option("--no-learn", dest="learn", action="store_false", help="disable learning", default=LEARN_MODE)
  parser.add_option("--file", dest="luma_file", help="luma file to load", default=LUMA_FILE_DEFAULT)
  parser.add_option("--vis", dest="visualize", action="store_true", help="visualize your brightness model", default=VIZ_LUMA_MAP)
  parser.add_option("--horizontal", dest="horizontal", action="store_true", help="take a horizontal screenshot instead of vertical")


  options, args = parser.parse_args()
  MIN_LEVEL = options.min_level
  MAX_LEVEL = options.max_level
  SCREENSHOT_TIME = options.interval
  MAX_LEVEL = options.max_level
  TRANSITION_MS = options.fade_time
  CROP_SCREEN = options.crop_screen
  VERBOSE = options.verbose
  RECALIBRATE_MS = options.recalibrate
  CHECK_PID = options.check_pid
  LEARN_MODE=options.learn
  VIZ_LUMA_MAP=options.visualize
  LUMA_FILE=options.luma_file

  if options.horizontal:
    CROP_SCREEN = HORIZ_CROP_SCREEN

  global SCREENSHOT_CMD
  if CROP_SCREEN is not None:
    SCREENSHOT_CMD += ' -crop %s' % CROP_SCREEN




def print_config():
  print "CROPPING:", not not CROP_SCREEN
  print "FADE TIME:", TRANSITION_MS
  print "SLEEP TIME:", SCREENSHOT_TIME
  print "DISPLAY RANGE:", MIN_LEVEL, MAX_LEVEL
  print "LEARNING MODE:", LEARN_MODE
  print "BRIGHTNESS RANGE:", MIN_BRIGHT, MAX_BRIGHT
  print "RECALIBRATE EVERY:", RECALIBRATE_MS
  print "FOLLOW WINDOW PID:", not not CHECK_PID
  print "FOLLOW WINDOW TITLE:", not CHECK_PID
  print "SCREENSHOT CMD", SCREENSHOT_CMD


def run_cmd(cmd, bg=False):
  args = shlex.split(cmd)
  start = int(round(time.time() * 1000))
  ret = ""
  if not bg:
    ret = subprocess.check_output(args)
  else:
    subprocess.Popen(args)

  end = int(round(time.time() * 1000))
  if VERBOSE and end - start > 50:
    print "TIME:", end - start, "CMD", cmd.split()[0]
  return ret


def get_brightness():
  import xbacklight
  if not xbacklight.can_use():
    ret = float(run_cmd("xbacklight -get"))
    return ret
  else:
    ctrls = xbacklight.get_controllers()
    ctrl = xbacklight.Controller(ctrls[0])
    ret = float(ctrl.brightness())
    return ret



try: import cpickle as pickle
except: import pickle

def print_luma_completion():
  l = len(LUMA_MAP)
  num_minute_buckets = (24.0*(60/HOUR_SLICE))
  time_perc_str = "%i" % round(l / num_minute_buckets * 100)

  num_luma_buckets = int((MAX_BRIGHT - MIN_BRIGHT) / LUMA_BUCKET)
  expected_obs = len(LUMA_MAP) * num_luma_buckets
  total_obs = 0.0
  for luma in LUMA_MAP:
    total_obs += len(LUMA_MAP[luma])

  luma_perc_str = "%i" % round(total_obs / expected_obs * 100)
  print "TIME MAP IS %s%% COMPLETE, LUMA MAP IS %s%% COMPLETE" % (time_perc_str, luma_perc_str)



def get_luma_file():
  return LUMA_FILE

def load_luma_map(luma_file=LUMA_FILE):
  print "LOADING LUMA MAP", luma_file
  try:
    with open(luma_file) as f:
      global LUMA_MAP
      LUMA_MAP = pickle.load(f)
      print_luma_completion()
  except Exception, e:
    print "WARNING: NOT LOADING LUMA MAP", e

LAST_SAVE = None
SAVE_INTERVAL=1000
def save_luma_map(force=False):
  now = int(time.time())
  global LAST_SAVE
  if force or not LAST_SAVE or now - LAST_SAVE > SAVE_INTERVAL:
    try:
      with open(LUMA_FILE, "wb") as f:
        pickle.dump(LUMA_MAP, f)
        last_save = now
    except Exception, e:
      print "WARNING: NOT SAVING LUMA MAP", e


def get_predicted_brightness(vals):
  total = 0
  weight = 0
  for i,k in enumerate(vals):
    wt = (i+1)**2
    total += wt * k
    weight += wt

  pred = int(total / weight)
  return pred

# TODO: nearest neighbors search here, instead of only looking for the current
# hour and current luma
def get_mean_brightness(hour, luma):
  hour = int(hour)
  if not hour in LUMA_MAP or not luma in LUMA_MAP[hour]:
    return None

  vals = LUMA_MAP[hour][luma]

  if not vals:
    return None

  return get_predicted_brightness(vals)

MAX_LUMA_PTS=7
def add_luma_brightness(hour, luma, cur_bright, backfill=None):
  if luma < 0:
    return

  hour = int(hour)

  prev_bright_pred = get_mean_brightness(hour, luma)
  if not hour in LUMA_MAP:
    LUMA_MAP[hour] = {}

  if not luma in LUMA_MAP[hour]:
    LUMA_MAP[hour][luma] = []

  if backfill is not None:
    LUMA_MAP[hour][luma].insert(max(MAX_LUMA_PTS - backfill, 0), round(cur_bright))
  else:
    LUMA_MAP[hour][luma].append(round(cur_bright))

  while len(LUMA_MAP[hour][luma]) > MAX_LUMA_PTS:
    LUMA_MAP[hour][luma].pop(0)

  new_pred = get_mean_brightness(hour, luma)
  now = int(time.time())

  if not backfill:
    print "LEARN|TS:%s, LUMA:%05i, HOUR: %s, PREV:%s, NEW:%s" % (now, luma, fmt_hour(hour), prev_bright_pred, new_pred)

HOUR_SLICE=10
HOUR_SPREAD=60


def get_hour():
  hour = int(time.strftime("%H")) * 60
  hour_slice = round(int(time.strftime("%M")) / HOUR_SLICE) * HOUR_SLICE
  hour = hour + hour_slice
  return hour

def fmt_hour(minutes):
  hour = minutes / 60
  mnt = int((minutes % 60) / HOUR_SLICE) * HOUR_SLICE

  return "%02i:%02i" % (hour, mnt)


PREV_LEVELS={}
PREV_WINDOWS = []
MAX_WINDOWS=100

def add_prev_level(window, new_level):
  global PREV_LEVELS
  PREV_LEVELS = {}
  PREV_WINDOWS.append((window, new_level))
  while len(PREV_WINDOWS) > MAX_WINDOWS:
    PREV_WINDOWS.pop(0)

  for datum in PREV_WINDOWS:
    win, level = datum
    PREV_LEVELS[win] = level

def get_window():
  focused_cmd = CHECK_TITLE_CMD
  if CHECK_PID:
    focused_cmd = CHECK_PID_CMD

  try: window = run_cmd(focused_cmd).strip()
  except: window = None

  return window

def monitor_luma():
  prev_brightness = None
  prev_window = None
  prev_mean = None
  faded = None

  cur_range = MAX_BRIGHT - MIN_BRIGHT
  suppressed_time = 0

  last_calibrate = int(time.time())
  last_screenshot = int(time.time())
  last_observation = 0


  while True:
    time.sleep(SLEEP_TIME / 1000.0)

    window = get_window()

    now = time.time()
    if prev_window != window:
      if not faded:
        if window in PREV_LEVELS:
          pred = PREV_LEVELS[window]
          fade = TRANSITION_MS / 2
          if VERBOSE:
            curtime = int(time.time())
            print "PRIOR|TS:%s," % curtime, "RECALLED BRIGHTNESS:", "%s/%s" % (int(pred), MAX_LEVEL), "FOR", window[:15]

          run_cmd("xbacklight -set %s -time %s" % (pred, fade))
          faded = True

    if now - last_screenshot < SCREENSHOT_TIME / 1000.0:
      continue

    last_screenshot = now
    faded = False



    if prev_window == window:
      suppressed_time += SCREENSHOT_TIME / 1000

      if LEARN_MODE:
        now = int(time.time())
        hour = get_hour()

        cur_bright = get_brightness()
        pred_bright = get_mean_brightness(hour, cur_bright) or cur_bright
        if abs(prev_brightness - pred_bright) > 1 and now - last_calibrate > next_calibrate:
          print "INPUT|TS:%s, LUMA:%05i, CUR:%.02f, EXP:%s" % (now, prev_mean, cur_bright, prev_brightness)
          add_prev_level(window, cur_bright)

          calib_factor = 1.5
          next_calibrate = max(min(calib_factor*next_calibrate, 60 * 60 * 1000), 1)
          if abs(last_observation - cur_bright) > 4:
            next_calibrate = 1

          last_observation = cur_bright
          # now we map the luma -> current brightness based on time of day
          last_calibrate = now

          add_luma_brightness(hour, prev_mean, cur_bright)
          for i, h in enumerate(xrange(HOUR_SLICE, HOUR_SPREAD*3, HOUR_SLICE)):
            low_hour = (hour-h) % (24*60)
            high_hour = (hour+h) % (24*60)
            hour_dist = i+1
            add_luma_brightness(low_hour, prev_mean, cur_bright, backfill=hour_dist)
            add_luma_brightness(high_hour, prev_mean, cur_bright, backfill=hour_dist)
            for j, b in enumerate(xrange(LUMA_BUCKET, LUMA_SPREAD+LUMA_BUCKET, LUMA_BUCKET)):
              luma_dist = j+1
              total_dist = int(math.sqrt(hour_dist + luma_dist))
              add_luma_brightness(low_hour, prev_mean-b, cur_bright, backfill=total_dist)
              add_luma_brightness(low_hour, prev_mean+b, cur_bright, backfill=total_dist)
              add_luma_brightness(high_hour, prev_mean-b, cur_bright, backfill=total_dist)
              add_luma_brightness(high_hour, prev_mean+b, cur_bright, backfill=total_dist)

          save_luma_map()


      if RECALIBRATE_MS > 0 and suppressed_time < RECALIBRATE_MS:
          continue
      print "RECALIBRATING BRIGHTNESS AFTER %S ms" % RECALIBRATE_MS

    suppressed_time = 0
    next_calibrate = 4

    window = get_window()
    prev_window = window

    brightness = run_cmd(SCREENSHOT_CMD + " " + BRIGHTNESS_CMD)


    try:
      cur_mean = float(brightness)
    except Exception, e:
      print "ERROR GETTING MEAN LUMA", e
      continue


    trimmed_mean = max(min(MAX_BRIGHT, cur_mean), MIN_BRIGHT) - MIN_BRIGHT
    trimmed_mean = int(trimmed_mean / LUMA_BUCKET) * LUMA_BUCKET
    range_is = float(trimmed_mean) / float(cur_range)

    new_gamma = 1 - range_is
    hour = get_hour()
    new_level =  (MAX_LEVEL - MIN_LEVEL) * new_gamma + MIN_LEVEL

    pred_level = get_mean_brightness(hour, trimmed_mean)
    if pred_level is not None:
      new_level = pred_level



    prev_mean = trimmed_mean

    new_level = max(round(new_level), 1)
    if prev_brightness != new_level:
      now = int(time.time())
      print "MODEL|TS:%s," % now, "LUMA:%05i," % trimmed_mean, "NEW GAMMA:%.02f," % new_gamma, "NEW BRIGHTNESS:", "%s/%s" % (int(new_level), MAX_LEVEL)
      run_cmd("xbacklight -set %s -time %s" % (new_level, TRANSITION_MS / 2))

      add_prev_level(window, new_level)
    prev_brightness = new_level

def run():
  load_options()

  if VIZ_LUMA_MAP:
    import luma_vis
    luma_vis.visualize(LUMA_FILE)
  else:
    print_config()
    load_luma_map(LUMA_FILE)
    monitor_luma()

if __name__ == "__main__":
  run()
