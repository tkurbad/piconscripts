#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os, os.path
import re
import sys

piconsRaw = open(sys.argv[1], 'r')
comparisonRaw = open(sys.argv[2], 'r')

picons = []
comparison = []

for line in piconsRaw:
    if not line.startswith('\n'):
        picons.append(line.strip('\n'))

for line in comparisonRaw:
    line = line.strip('\n')
    if 'FFFF0000' in line:
        included = False
        serviceRef = '1_0_1%s' % line.split('1_0_1')[1]
        for piconsLine in picons[:]:
            if serviceRef in piconsLine:
                included = True
        if not included:
            comparison.append(line)

print '\n'.join(comparison)
