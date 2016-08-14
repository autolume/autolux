import math
import time
import os
try: import cpickle as pickle
except: import pickle

import opts
import autolux


LUMA_BUCKET=500
LUMA_SPREAD=5000
# for a luma map, what we hold is:
# time of day -> luma -> [p1,p2,p3]
LUMA_MAP = {}
LUMA_OBS = []

LUMA_FILE=None
LUMA_DIR=os.path.expanduser("~/.config/autolux")
LUMA_FILE_DEFAULT = os.path.join(LUMA_DIR, "luma_map.p")
OLD_LUMA_FILE_DEFAULT = os.path.expanduser("~/.config/autolux.luma_map")


LUMA_FILE=None
CHANGES_FILE = os.path.join(LUMA_DIR, "brightness_changes.p")

try: os.makedirs(LUMA_DIR)
except: pass

if os.path.exists(OLD_LUMA_FILE_DEFAULT):
  os.rename(OLD_LUMA_FILE_DEFAULT, LUMA_FILE_DEFAULT)



def print_luma_completion():
  l = len(LUMA_MAP)
  num_minute_buckets = (24.0*(60/HOUR_SLICE))
  time_perc_str = "%i" % round(l / num_minute_buckets * 100)

  num_luma_buckets = int((opts.MAX_BRIGHT - opts.MIN_BRIGHT) / LUMA_BUCKET)
  expected_obs = num_minute_buckets * num_luma_buckets
  total_obs = 0.0
  for luma in LUMA_MAP:
    total_obs += len(LUMA_MAP[luma])

  luma_perc_str = "%i" % round(total_obs / expected_obs * 100)
  print "TIME MAP IS %s%% COMPLETE, LUMA MAP IS %s%% COMPLETE" % (time_perc_str, luma_perc_str)



def get_luma_file():
  return LUMA_FILE

def load_luma_observations():
  global LUMA_OBS
  if os.path.exists(CHANGES_FILE):
    try:
      with open(CHANGES_FILE) as f:
        LUMA_OBS = pickle.load(f)
        print "LOADED %s LUMA OBSERVATIONS" % len(LUMA_OBS)
    except Exception, e:
      print "EXCEPT", e


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
        LAST_SAVE = now
    except Exception, e:
      print "WARNING: NOT SAVING LUMA MAP", e

    try:
      with open(CHANGES_FILE, "wb") as f:
        pickle.dump(LUMA_OBS, f)
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

def record_luma_change(hour, luma, cur_bright):
  LUMA_OBS.append((hour, luma, cur_bright))
  while len(LUMA_OBS) > 1000:
    LUMA_OBS.pop(0)

MAX_LUMA_PTS=7
def add_luma_brightness(hour, luma, cur_bright, backfill=None):
  if luma < 0:
    return

  hour = int(hour)
  if backfill:
    backfill = int(backfill)

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
    print "LEARN|TS:%s, LUMA:%05i, HOUR: %s, PREV:%s, NEW:%s" % (now, luma, autolux.fmt_hour(hour), prev_bright_pred, new_pred)

HOUR_SLICE=10
HOUR_SPREAD=60


LAST_CALIBRATE=int(time.time())
NEXT_CALIBRATE=4
LAST_OBSERVATION = 0
def add_observation(prev_brightness, prev_mean):
    global NEXT_CALIBRATE, LAST_CALIBRATE
    global LAST_OBSERVATION

    now = int(time.time())
    hour = autolux.get_hour()
    cur_bright = autolux.get_brightness()
    pred_bright = get_mean_brightness(hour, prev_mean) or prev_brightness

    if abs(cur_bright - pred_bright) > 1 and now - LAST_CALIBRATE > NEXT_CALIBRATE:
      print "INPUT|TS:%s, LUMA:%05i, CUR:%.02f, EXP:%s" % (now, prev_mean, cur_bright, pred_bright)
      autolux.add_prev_level(autolux.get_window(), cur_bright)

      calib_factor = 1.5
      NEXT_CALIBRATE = max(min(calib_factor*NEXT_CALIBRATE, 60 * 60 * 1000), 1)
      if abs(LAST_OBSERVATION - cur_bright) > 4:
        NEXT_CALIBRATE = 1

      LAST_OBSERVATION = cur_bright
      # now we map the luma -> current brightness based on time of day
      LAST_CALIBRATE = now

      add_luma_brightness(hour, prev_mean, cur_bright)
      record_luma_change(hour, prev_mean, cur_bright)

      for i, h in enumerate(xrange(HOUR_SLICE, HOUR_SPREAD*3, HOUR_SLICE)):
        low_hour = (hour-h) % (24*60)
        high_hour = (hour+h) % (24*60)
        hour_dist = i+1
        add_luma_brightness(low_hour, prev_mean, cur_bright, backfill=math.sqrt(hour_dist))
        add_luma_brightness(high_hour, prev_mean, cur_bright, backfill=math.sqrt(hour_dist))
        for j, b in enumerate(xrange(LUMA_BUCKET, LUMA_SPREAD+LUMA_BUCKET, LUMA_BUCKET)):
          luma_dist = j+1
          total_dist = int(math.sqrt(hour_dist + luma_dist))
          add_luma_brightness(low_hour, prev_mean-b, cur_bright, backfill=total_dist)
          add_luma_brightness(low_hour, prev_mean+b, cur_bright, backfill=total_dist)
          add_luma_brightness(high_hour, prev_mean-b, cur_bright, backfill=total_dist)
          add_luma_brightness(high_hour, prev_mean+b, cur_bright, backfill=total_dist)

      save_luma_map()


