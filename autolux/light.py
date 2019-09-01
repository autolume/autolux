# A small compatibility layer for `light`
# https://github.com/haikarainen/light

import opts
from run_cmd import run_cmd

def set_brightness(new_level, time):
    run_cmd("light -S {:f}".format(new_level))

def get_brightness():
    out = run_cmd("light -G")
    return float(out.strip())
