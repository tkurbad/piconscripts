piconscripts
============

A collection of scripts related to @ocram's picons

* `piconlinks.py` is a Python 2.x script that takes 
  your particular VDR-style `channels.conf` and a
  directory with picons to create a shell script for
  Enigma2 style service reference symlinks.
  It tries a simple matching algorithm from channel
  name to picon name, and leaves everything else
  commented out for manual correction/addition.

  For usage instructions, see:

  ```python2 piconlinks.py -h```

  **Important note:** Your `channels.conf` should be created
  by the [w_scan](http://wirbel.htpc-forum.de/w_scan/index2.html)
  tool or the [vdr-wirbelscan plugin](http://wirbel.htpc-forum.de/wirbelscan/index2.html).
  Using a `channels.conf` created by the `scan` tool from the
  [dvb-apps](http://www.linuxtv.org/) will not work properly.

* `kabelbw.sh` creates the same symlinks as @ocram's
  [picons.sh](https://github.com/ocram/picons/blob/master/picons.sh),
  but only for the German DVB-C provider Kabel BW.
  Look at the `"# unmatched channels"` section, if you
  care to conribute missing picons to
  https://github.com/ocram/picons.
