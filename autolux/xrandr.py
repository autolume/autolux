# a compatibility layer for xrandr meant to set brightness
import opts
from run_cmd import run_cmd

def set_brightness(new_level, time):
    output = opts.XRANDR_OUTPUT

    # calibrating to xbacklight 1 - 100 by dividing by 100
    new_level /= 100.0

    new_level = min(new_level, 1.0)
    new_level = max(new_level, 0.3)

    run_cmd("xrandr --output %s --brightness %s" % (output, new_level))

def get_brightness():
    out = run_cmd("xrandr --current --verbose")
    for line in out.split("\n"):
        if line.find("Brightness") != -1:
            brt = line.split(":")[1]
            brt = float(brt)
    # calibrating to xbacklight 1 - 100 by multiplying by 100
    return brt * 100
