import urllib2
import pickle
import matplotlib.pyplot as plt
import os
import random

import autolux

# UTC offset
import time
UTC_OFFSET = int(-time.timezone / 60 / 60)

def visualize(luma_file):
    if not autolux.LUMA_MAP or len(autolux.LUMA_MAP) == 0:
        autolux.load_luma_map(luma_file)

    build_all_scatterplot(autolux.LUMA_MAP)

def build_all_scatterplot(lumas):
    colors = []
    x = []
    y = []
    sz = []
    dict_all_lumas = {}

    cm = plt.cm.get_cmap('gist_rainbow')

    for time in lumas:
        for luma in lumas[time]:
            obs = lumas[time][luma]
            pred = autolux.get_predicted_brightness(obs)
            if not luma in dict_all_lumas:
                dict_all_lumas[luma] = []

            dict_all_lumas[luma].append((pred,time, len(obs)))

    for luma in reversed(sorted(dict_all_lumas)):
        for brightness,time,obs in dict_all_lumas[luma]:
            time_hour = (((time / 60) + UTC_OFFSET) % 24)
            time_jitter = time_hour + (time % 60) / 60.0
            luma_jitter = luma + random.randint(-500, 500)
            bright_jitter = brightness + random.randint(-2, 2)

            x.append(time_jitter)
            y.append(bright_jitter)
            sz.append(obs*100)
            colors.append(luma_jitter)


    sc = plt.scatter(x, y, s=sz, c=colors, alpha=0.1, cmap=cm, edgecolor='none',marker="s")
    plt.colorbar(sc)
    plt.axis([0, 24, 0, max(y)])
    plt.show()

if __name__ == '__main__':
    visualize()
