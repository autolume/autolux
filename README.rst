=======
autolux
=======

inspired by `lumen <https://github.com/anishathalye/lumen>` but written for
\*nix machines. autolux takes a screenshot every few seconds, figures out the
'average value' of the resulting image (the **luminence**) and changes the
screen brightness based on the screen's contents.


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


model
-----

initially, autolux uses linear interpolation to figure out the brightness to
map to different luminence inputs. as the brightness is manually adjusted away
from its predicted value, autolux records the time of day and luminence values
that prompted you to change the brightness level and integrates the new
information into its model.

autolux assumes that time of day and screen content are the sole predictors of
one's preferred brightness, but the model could further be improved by adding
in several factors, such as **ambient light** or **user active time** (as a
stand-in for eye strain). because of these and other unknown confounding
variables, autolux has an emphasis on quick learning of new preferences and not
burning in old ones.


visuals
-------

::

    autolux --vis --plot-bright
    # show brightness prediction model
    # requires matplotlib

.. image:: https://cloud.githubusercontent.com/assets/98617/17515134/813b76f0-5deb-11e6-9f27-cb91d3442c45.png
   :width: 800


::

    # color is the input luminence. (5K - 65K, lower value is darker screen content)
    # x axis is hour (0 - 24, with UTC offset applied)
    # y axis is predicted brightness level from the model (0 - 100%)


    autolux --vis --plot-luma
    # --plot-luma will swap the luma and brightness on the Y axis and colorbar

.. image:: https://cloud.githubusercontent.com/assets/98617/17578997/f570188c-5f44-11e6-9387-d5e9f08b7cd6.png
   :width: 800

