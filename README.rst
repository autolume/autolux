=======
autolux
=======

inspired by [lumen](https://github.com/anishathalye/lumen) but written for
\*nix machines. autolux takes a screenshot every few seconds, figures out the
'average value' of the resulting image and changes the screen brightness based
on screen's contents.

---
installation
---

  pip install autolux

---
dependencies
---

* imagemagick (for screenshots + determining average brightness)
* xdotool (finding focused window)
* xbacklight (for setting display brightness)

---
usage:
---

    autolux


---
how it works
---

autolux is a simple python script that takes a screenshot of a vertical strip
every few seconds and calculates the average pixel value. in order to save CPU,
a screenshot is only taken if the window has changed since the last time a
screenshot was taken
