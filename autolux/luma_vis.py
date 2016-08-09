import urllib2
import pickle
import matplotlib.pyplot as plt
import os
import random

import autolux

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
            time_hour = (((time / 60)) % 24)
            time_jitter = time_hour + (time % 60) / 60.0
            luma_jitter = luma + random.randint(-500, 500)
            bright_jitter = brightness + random.randint(-2, 2)

            x.append(time_jitter)
            y.append(bright_jitter)
            sz.append(obs*100)
            colors.append(luma_jitter)


    max_y = max(y or [10])
    now_mark = autolux.get_hour()
    plt.text((now_mark / 60) % 24, 1, "NOW")
    plt.text((now_mark / 60) % 24, max_y-1, "NOW")
    plt.yticks([0, max_y], ['Low Brightness\n(predicted by model)', 'High Brightness\n(predicted by model)'])
    plt.xticks([0,3,6,9,12,15,18,21,24])
    sc = plt.scatter(x, y, s=sz, c=colors, alpha=0.1, cmap=cm, edgecolor='none',marker="s")

    cbar = plt.colorbar(sc, ticks=[0000, autolux.MAX_BRIGHT])
    cbar.ax.set_yticklabels(['Low Luminence \n(Dark Screen Content)',
        'High Luminence \n(Bright Screen Content)'])
    cbar.ax.invert_yaxis()
    plt.axis([0, 24, 0, max_y])
    plt.show()

if __name__ == '__main__':
    visualize()
