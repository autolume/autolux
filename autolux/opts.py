import os
import time

import models

# BRIGHTNESS LEVELS (should be between 1 and 100)
MIN_LEVEL=5
MAX_LEVEL=100

# interpolate over our threshold (should be between 1 and 65K)
MAX_BRIGHT=60000
MIN_BRIGHT=5000

# interval between screenshots
SLEEP_TIME=67
SCREENSHOT_TIME=1200
TRANSITION_MS=800
RECALIBRATE_MS=60 * 1000

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

PLOT_LUMA=True
PLOT_BRIGHT=False

RUN_AS_DAEMON=False

# do we use software dimming or not
XRANDR_OUTPUT = None
ADJUSTMENT = None
RESET = False

VERBOSE=False
def load_options():
  global MIN_LEVEL, MAX_LEVEL, MAX_BRIGHT, MIN_BRIGHT, CROP_SCREEN
  global SLEEP_TIME, TRANSITION_MS, RECALIBRATE_MS, SCREENSHOT_TIME
  global VERBOSE, CHECK_PID, LEARN_MODE,VIZ_LUMA_MAP
  global PLOT_LUMA, PLOT_BRIGHT
  global RUN_AS_DAEMON, XRANDR_OUTPUT
  global ADJUSTMENT, RESET

  from optparse import OptionParser
  parser = OptionParser()
  parser.add_option("--daemon", dest="run_as_daemon", help="run autolux as a daemon",
    default=RUN_AS_DAEMON, action="store_true")
  parser.add_option("--file", dest="luma_file", help="luma file to load", default=models.LUMA_FILE_DEFAULT)
  parser.add_option("--sleep-interval", dest="sleep_interval", type="int", default=SLEEP_TIME,
    help="check for window change ever SLEEP_INTERVAL ms, default is %s" % SLEEP_TIME)
  parser.add_option("--interval", dest="interval", type="int", default=SCREENSHOT_TIME,
    help="take screen snapshot every INTERVAL ms and readjust the screen brightness, default is %s" % SCREENSHOT_TIME)
  parser.add_option("--min", "--min-level", dest="min_level", type="int", default=MIN_LEVEL,
    help="min brightness level (from 1 to 100, default is %s)" % MIN_LEVEL)
  parser.add_option("--max", "--max-level", dest="max_level", type="int", default=MAX_LEVEL,
    help="max brightness level (from 1 to 100, default is %s)" % MAX_LEVEL)
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
  parser.add_option("--pid", dest="check_pid", action="store_true", help="check screen brightness when PID changes")
  parser.add_option("--title", dest="check_pid", action="store_false", help="check screen brightness when window changes")
  parser.add_option("--horizontal", dest="horizontal", action="store_true", help="take a horizontal screenshot instead of vertical")
  parser.add_option("--no-learn", dest="learn", action="store_false", help="disable learning", default=LEARN_MODE)
  parser.add_option("--verbose", dest="verbose", action="store_true", help="turn on verbose output, including screenshot timing info")
  parser.add_option("--visualize", dest="visualize", action="store_true", help="visualize your brightness model", default=VIZ_LUMA_MAP)
  parser.add_option("--plot-luma", dest="plot_luma", action="store_true", help="plot screen luminence on y axis and predicted brightness as color, good for observing prefered brightness by time of day", default=PLOT_LUMA)
  parser.add_option("--plot-brightness", dest="plot_luma", action="store_false", help="plot predicted brightness on y axis and input luminence as color, good for observing eye strain", default=not PLOT_LUMA)

  parser.add_option("--xrandr", dest="xrandr_output", type="str", default=None)

  parser.add_option("--adjust", dest="adjustment", type="float", default=None)
  parser.add_option("--reset", dest="reset", action="store_true", default=None)



  options, args = parser.parse_args()
  MIN_LEVEL = options.min_level
  MAX_LEVEL = options.max_level
  RUN_AS_DAEMON = options.run_as_daemon
  SCREENSHOT_TIME = options.interval
  SLEEP_TIME = options.sleep_interval
  MAX_LEVEL = options.max_level
  TRANSITION_MS = options.fade_time
  CROP_SCREEN = options.crop_screen
  VERBOSE = options.verbose
  RECALIBRATE_MS = options.recalibrate
  CHECK_PID = options.check_pid
  LEARN_MODE=options.learn
  VIZ_LUMA_MAP=options.visualize
  models.LUMA_FILE=options.luma_file
  PLOT_BRIGHT=not options.plot_luma
  PLOT_LUMA=options.plot_luma
  XRANDR_OUTPUT=options.xrandr_output
  ADJUSTMENT=options.adjustment
  RESET=options.reset

  MIN_BRIGHT = options.min_bright
  MAX_BRIGHT = options.max_bright


  if options.horizontal:
    CROP_SCREEN = HORIZ_CROP_SCREEN

  global SCREENSHOT_CMD
  if CROP_SCREEN is not None:
    SCREENSHOT_CMD += ' -crop %s' % CROP_SCREEN




def print_config():
  print "DAEMON MODE:", not not RUN_AS_DAEMON
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


