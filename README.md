piconscripts
============

A collection of scripts related to @ocram's picons

* piconlinks.py is a Python 2.x script that takes 
  your particular VDR-style channels.conf and a
  directory with picons to create a shell script for
  Enigma2 style service reference symlinks.
  It tries a simple matching algorithm from channel
  name to picon name, and leaves everything else
  commented out for manual correction/addition.

  For usage instructions, see:
	python2 piconlinks.py -h

* kabelbw.sh creates the same symlinks as picons.sh
  from ocram's repo does, but only for the German DVB-C
  provider Kabel BW.
  Look at the "unmatched channels" section, if you care
  to conribute missing icons to
  https://github.com/ocram/picons.

