# autolux

inspired by [lumen](https://github.com/anishathalye/lumen) but written for
\*nix machines. autolux takes a screenshot every few seconds, figures out the
'average value' of the resulting image and changes the screen brightness based
on screen's contents.

## dependencies

* imagemagick (for screenshots + determining average brightness)
* xdotool (finding focused window)
* xbacklight (for setting display brightness)

## usage:

    autolux --help

    # check screen every 5 seconds, takes 500ms to fade brightness to next state
    autolux --interval 5000 --fade-time 500
