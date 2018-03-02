#!/usr/bin/env python
# required utilities: imagemagick, xdotool, xbacklight

import time
import os
import math

try: import cpickle as pickle
except: import pickle

import opts
import models

from run_cmd import run_cmd
def set_brightness(new_level, time):
  if opts.XRANDR_OUTPUT:
    import xrandr
    xrandr.set_brightness(new_level, time)
  else:
    import xbacklight
    xbacklight.set_brightness(new_level, time)

def get_brightness():
  if opts.XRANDR_OUTPUT:
    import xrandr
    return xrandr.get_brightness()

  else:
    import xbacklight
    return xbacklight.get_brightness()

def get_hour():
  hour = int(time.strftime("%H")) * 60
  hour_slice = round(int(time.strftime("%M")) / models.HOUR_SLICE) * models.HOUR_SLICE
  hour = hour + hour_slice
  return hour

def fmt_hour(minutes):
  hour = minutes / 60
  mnt = int((minutes % 60) / models.HOUR_SLICE) * models.HOUR_SLICE

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
    PREV_LEVELS[win] = max(level, 1)

def get_window():
  focused_cmd = opts.CHECK_TITLE_CMD
  if opts.CHECK_PID:
    focused_cmd = opts.CHECK_PID_CMD

  try: window = run_cmd(focused_cmd).strip()
  except Exception, e: print e; window = None

  return window

def monitor_luma():
  prev_brightness = None
  prev_window = None
  prev_mean = None
  faded = None

  cur_range = opts.MAX_BRIGHT - opts.MIN_BRIGHT
  suppressed_time = 0

  last_screenshot = int(time.time())


  while True:
    time.sleep(opts.SLEEP_TIME / 1000.0)

    window = get_window()

    now = time.time()
    if prev_window != window:
      if not faded:
        if window in PREV_LEVELS:
          pred = PREV_LEVELS[window]
          fade = opts.TRANSITION_MS / 2
          if opts.VERBOSE:
            curtime = int(time.time())
            print "PRIOR|TS:%s," % curtime, "RECALLED BRIGHTNESS:", "%s/%s" % (int(pred), MAX_LEVEL), "FOR", window[:15]

          set_brightness(pred, fade)
          faded = True

          continue

    if now - last_screenshot < opts.SCREENSHOT_TIME / 1000.0:
      continue

    last_screenshot = now
    faded = False



    if prev_window == window:
      suppressed_time += opts.SCREENSHOT_TIME / 1000

      if opts.LEARN_MODE and prev_brightness:
        models.add_observation(prev_brightness, prev_mean)

      if opts.RECALIBRATE_MS > 0 and suppressed_time < opts.RECALIBRATE_MS:
          continue

      print "RECALIBRATING BRIGHTNESS AFTER %S ms" % opts.RECALIBRATE_MS

    suppressed_time = 0

    window = get_window()
    prev_window = window

    brightness = run_cmd(opts.SCREENSHOT_CMD + " " + opts.BRIGHTNESS_CMD)


    try:
      cur_mean = float(brightness)
    except Exception, e:
      print "ERROR GETTING MEAN LUMA", e
      continue


    trimmed_mean = max(min(opts.MAX_BRIGHT, cur_mean), opts.MIN_BRIGHT) - opts.MIN_BRIGHT
    trimmed_mean = int(trimmed_mean / models.LUMA_BUCKET) * models.LUMA_BUCKET
    range_is = float(trimmed_mean) / float(cur_range)

    new_gamma = 1 - range_is
    hour = get_hour()
    new_level =  (opts.MAX_LEVEL - opts.MIN_LEVEL) * new_gamma + opts.MIN_LEVEL

    pred_level = models.get_mean_brightness(hour, trimmed_mean)
    if pred_level is not None:
      new_level = pred_level



    prev_mean = trimmed_mean

    new_level = max(round(new_level), 1)
    if prev_brightness != new_level:
      now = int(time.time())
      print "MODEL|TS:%s," % now, "LUMA:%05i," % trimmed_mean, "NEW GAMMA:%.02f," % new_gamma, "NEW BRIGHTNESS:", "%s/%s" % (int(new_level), opts.MAX_LEVEL)

      set_brightness(new_level, opts.TRANSITION_MS / 2)

      add_prev_level(window, new_level)
    prev_brightness = new_level

def run():
  opts.load_options()

  if opts.RESET:
    set_brightness(100, 1)
  elif opts.ADJUSTMENT:
    b = get_brightness()
    nb = b + opts.ADJUSTMENT
    set_brightness(nb, 0)
  elif opts.VIZ_LUMA_MAP:
    import luma_vis
    luma_vis.visualize(models.LUMA_FILE)
  else:
    opts.print_config()
    models.load_luma_observations()
    models.load_luma_map(models.LUMA_FILE)

    if opts.RUN_AS_DAEMON:
        import os
        try:
            import daemon
            import daemon.pidfile
        except:
            print "MISSING DAEMON MODULE. PLEASE INSTALL PYTHON-DAEMON TO ENABLE DAEMON MODE"
            import sys
            sys.exit(1)

        uid = os.getuid()
        lock_file = os.path.join(os.path.sep, "tmp", "autolux.%s.pid" % uid)
        print "RUNNING IN DAEMON MODE"
        print "LOCKFILE", lock_file
        with daemon.DaemonContext(pidfile=daemon.pidfile.PIDLockFile(lock_file)):
            monitor_luma()
    else:
        monitor_luma()

if __name__ == "__main__":
  try:
    run()
  except:
    # we always reset brightness back to 100% for xrandr
    # if there was an error
    if opts.XRANDR_OUTPUT:
      set_brightness(100, 1)
