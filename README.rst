=======
autolux
=======

inspired by `lumen <https://github.com/anishathalye/lumen>` but written for
\*nix machines. autolux takes a screenshot every few seconds, figures out the
'average value' of the resulting image (the **luminence**) and changes the
screen brightness based on your screen's contents.

installation
------------

  pip install autolux

dependencies
------------

* python2 (not python3)
* imagemagick (for screenshots + determining average brightness)
* xdotool (finding focused window)
* xbacklight (for setting display brightness)

usage
-----


::

    # runs autolux
    autolux

    # show luminence prediction model
    # requires matplotlib
    autolux --vis

.. image:: https://cloud.githubusercontent.com/assets/98617/17468285/621913e2-5cdb-11e6-94b3-a9f3e9154413.png
   :width: 600


::

    # color is the input luminence. (5K - 65K, lower is darker)
    # x axis is hour (0 - 24, with UTC offset applied)
    # y axis is predicted brightness level from the model (0 - 100%)

    # the red regions represent low luminence screen content and therefore
    # have a higher predicted brightness. the blue regions are high luminence
    # content with a lower predicted brightness

