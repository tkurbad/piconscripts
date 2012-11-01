#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import os, os.path
import re
import sys

from textwrap import dedent


class Channels(object):
    """ Holds all the information and methods for the processing of
        VDR style 'channels.conf' files. """

    channelsCurrent = []
    channelsNew = []
    channelParamsDiff = []
    channelNamesDiff = []
    channelsCurUntouched = dict()
    channelsNewUntouched = dict()

    def __init__(self, channels_conf_current = '/etc/vdr/channels.conf',
        channels_conf_new = './channels.conf', service_types = 1):
        """ Initialize, read and store the channels from
            a given channels.conf. """

        self.service_types = service_types

        try:
            # Open current channels.conf
            channelsFileCurrent = open(channels_conf_current, 'r')
        except IOError:
            # Not found / not accessible
            sys.exit ('ERROR: Could open %s' % channels_conf_current)

        try:
            # Open new channels.conf
            channelsFileNew = open(channels_conf_new, 'r')
        except IOError:
            # Not found / not accessible
            sys.exit ('ERROR: Could open %s' % channels_conf_new)

        # Save the channel.conf file names for later use
        self.channelsConfCurrent = channels_conf_current
        self.channelsConfNew = channels_conf_new

        # Will be needed later (for QAM value unification)
        qamRegex = re.compile('^.*(M[0-9]*).*$')

        # Determine name and parameters for each channel and
        # place that info in the appropriate channels list.
        for channelsFile in (channelsFileCurrent, channelsFileNew):
            lineNo = 0
            for channelLine in channelsFile:
                lineNo += 1
                # Break down a line from channels.conf and remove
                # leading and trailing whitespace (if any)
                channelSplit = [x.strip() for x in channelLine.split(':')]

                # Keep untouched channel information
                if channelsFile == channelsFileNew:
                    self.channelsNewUntouched[channelSplit[0]] = channelSplit[1:]
                if channelsFile == channelsFileCurrent:
                    self.channelsCurUntouched[channelSplit[0]] = channelSplit[1:]

                # Determine channel name and (simplified) parameters
                channelName = channelSplit[0]
                channelParams = [
                    x.split('=',1)[0].split(';',1)[0].strip() for x in channelSplit[1:]]

                # Frequencies should be in kHz
                if int(channelParams[0]) < 1000:
                    channelParams[0] = '%d' % (int(channelParams[0]) * 1000)

                # Unify QAM value (for DVB-C, this can be Mxx or C0Mxx)
                channelParams[1] = re.sub(qamRegex, '\g<1>', channelParams[1])

                # This should never happen, but anyway
                if channelName is None:
                    continue

                # Skip '(null)' provider name (Data channels, ...)
                if  ((';' in channelName) and
                    (channelName.split(';')[1].strip() == '(null)')):
                    continue

                # Add to channels list
                if len(channelParams) == 12:
                    # Don't add radio channels?
                    if (self.service_types & 2) == 0:
                        if (channelParams[4] == '0') or (channelParams[4] == '1'):
                            continue
                    # Don't add TV channels?
                    if (self.service_types & 1) == 0:
                        if (channelParams[4] > '1'):
                            continue

                    # Finally add to the appropriate list
                    if channelsFile == channelsFileCurrent:
                        self.channelsCurrent.append((lineNo, channelName, channelParams,))
                        continue
                    self.channelsNew.append((channelName, channelParams,))

        # Sort channelsNew
        self.channelsNew = sorted(self.channelsNew)

    def _compare(self):
        """ Compare both lists, channelsCurrent and channelsNew, and provide
            the difference between them. """

        # Eliminate all entries that are in both lists
        loopChannelsCur = self.channelsCurrent[:]
        for (lineNo, channelName, channelParams) in loopChannelsCur:
            entry = (channelName, channelParams,)
            if entry in self.channelsNew:
                self.channelsCurrent.remove(
                    (lineNo, channelName, channelParams,))
                self.channelsNew.remove(entry)
                continue

            # Find channels of same name (but different params) in both lists
            loopChannelsNew = self.channelsNew[:]
            for (channelNameTmp, channelParamsNew) in loopChannelsNew:
                if channelNameTmp == channelName:
                    self.channelParamsDiff.append(
                        (lineNo, channelName, channelParams, channelParamsNew))
                    self.channelsCurrent.remove((lineNo, channelName, channelParams,))
                    self.channelsNew.remove((channelNameTmp, channelParamsNew,))

            # Find channels of same parameters (but different names) in both lists
            loopChannelsNew = self.channelsNew[:]
            for (channelNameNew, channelParamsTmp) in loopChannelsNew:
                if channelParamsTmp == channelParams:
                    self.channelNamesDiff.append(
                        (lineNo, channelName, channelNameNew, channelParams))
                    self.channelsCurrent.remove((lineNo, channelName, channelParams,))
                    self.channelsNew.remove((channelNameNew, channelParamsTmp,))

    def showDiff(self):
        """ Display the differences current vs. new. """

        # Compare the channel lists
        self._compare()

        # Print header
        headLine = 'Comparison results (%s <-> %s)' % (
            self.channelsConfCurrent, self.channelsConfNew)
        underLine = ''
        for i in range(0, len(headLine)):
            underLine += '='

        print
        print headLine
        print underLine
        print

        # Evaluate, if there were differences
        if (self.channelsCurrent == []
            and self.channelsNew == []
            and self.channelsDiff == []):
            print 'There are no differences between the two files.'
            sys.exit(0)

        # Sort the remainder of self.channelsCurrent by channelName
        def _byName(x, y):
            (lx, nx, px) = x
            (ly, ny, py) = y
            return cmp(nx, ny)
        self.channelsCurrent = sorted(self.channelsCurrent, cmp=_byName)

        # Print changed channels
        print 'The following differences exist:'
        print '--------------------------------'
        print

        # Parameter changes
        print 'Channel PARAMETER changes'
        for (lineNo, channelName, channelParamsCur, channelParamsNew
            ) in self.channelParamsDiff:
            print '---'
            print 'Line %d - parameter change:' % lineNo
            print '- %s:%s' % (channelName, ':'.join(
                self.channelsCurUntouched[channelName]))
            print '+ %s:%s' % (channelName, ':'.join(
                self.channelsNewUntouched[channelName]))
        print

        # Name changes
        print 'Channel NAME changes'
        for (lineNo, channelNameCur, channelNameNew, channelParams
            ) in self.channelNamesDiff:
            print '---'
            print 'Line %d - name change:' % lineNo
            print '- %s:%s' % (channelNameCur, ':'.join(
                self.channelsCurUntouched[channelNameCur]))
            print '+ %s:%s' % (channelNameNew, ':'.join(
                self.channelsNewUntouched[channelNameNew]))
        
        print

        # Obsolete channels
        print 'Channels that are NO LONGER found'
        for (lineNo, channelName, channelParams) in self.channelsCurrent:
            print '---'
            print 'Line %d - not found:' % lineNo
            print '- %s:%s' % (channelName, ':'.join(
                self.channelsCurUntouched[channelName]))
        print

        # New channels
        print 'NEW channels'
        for (channelName, channelParams) in self.channelsNew:
            print '---'
            print '+ %s:%s' % (channelName, ':'.join(
                self.channelsNewUntouched[channelName]))
        print


def main():
    # Define commandline arguments
    parser = argparse.ArgumentParser(
        description = 'Show differences between current and new channels.conf.',
        formatter_class = argparse.RawTextHelpFormatter,)
    parser.add_argument('-c', '--channels',
        metavar = 'old_channels.conf',
        default = '/etc/vdr/channels.conf',
        help = '''pathname of _current_ channels.conf
(default: /etc/vdr/channels.conf)
''')
    parser.add_argument('-t', '--types',
        type = int,
        choices = range(1, 4),
        metavar = 'service type(s)',
        default = 1,
        help = '''service types to consider:
    1 - TV,
    2 - radio,
    3 - TV+radio
(default: 1)
''')
    parser.add_argument('channels_new',
        metavar = 'new_channels.conf',
        default = './channels.conf',
        help = '''pathname of _new_ channels.conf
(default: ./channels.conf)
''')

    argsDict = vars(parser.parse_args())

    # Instantiate
    channels = Channels(
        channels_conf_current = argsDict['channels'],
        channels_conf_new = argsDict['channels_new'],
        service_types = argsDict['types'])

    # Print diff
    channels.showDiff()

if __name__ == '__main__':
    sys.exit(main())
