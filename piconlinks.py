#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import os, os.path
import re
import sys

class Channels(object):
    """ Holds all the information and routines related to
        linking VDR channels to picons via their respective
        servicerefs. """
        
    channels = []

    def __init__(self, channels_conf = '/etc/vdr/channels.conf', tvonly = False,
        provider_name = None):
        """ Initialize, read and store the channels from
            a given channels.conf. """

        self.tvonly = tvonly
        self.provider_name = provider_name

        try:
            # Open channels.conf
            channelsFile = open(channels_conf, 'r')
        except IOError:
            # Not found / not accessible
            sys.exit ('ERROR: Could open %s' % channels_conf)

        # Determine name and parameters for each channel and
        # place that info in the channels list.
        for channelLine in channelsFile:
            # Break down a line from channels.conf and remove
            # leading and trailing whitespace (if any)
            channelSplit = [x.strip() for x in channelLine.split(':')]

            # Add to channels list.
            # Skip '(null)' provider name (Data channels, ...)
            if ((channelSplit[0] is not None)
                and (len(channelSplit) == 13) and channelSplit[0]
                and (';' in channelSplit[0])
                and not (channelSplit[0].split(';')[1] == '(null)')):
                self.channels.append((channelSplit[0], channelSplit[1:],))

    def simplenames(self):
        """ Provides a dictionary of
              ('Channel name': 'simplechannelname')
            items, e.g.
              ('Das Erste HD;ARD': 'daserstehd') """
        simpleNames = dict()
        
        for (channelName, channelParams) in self.channels:
            # Skip channels with "empty" vpid (i.e. radio),
            # if 'self.tvonly' flag is set.
            if (channelParams[4] == '0' or channelParams[4] == '1') and self.tvonly:
                continue

            ## Now start simplifiying
            # Cut off provider names.
            (cname, provider) = channelName.rsplit(';', 1)

            # Simplify.
            cname = re.sub('\s', '', cname.lower())

            # Add to dictionary            
            simpleNames[channelName] = cname

        return simpleNames

    def servicerefs(self):
        """ Provides a dictionary of
              ('Channel name': 'serviceref')
            items, e.g.
              ('Das Erste HD;ARD': '1_0_19_2B5C_41B_A401_FFFF0000_0_0_0') """
 
        def _createserviceref(source, freq, vpid, sid, nid, tid):
            """ Subroutine for creating a single service reference.
                All credit to pipelka (https://github.com/pipelka). """

            # Analyze the 'vpid' as early as possible to skip unwanted
            # channels (e.g. set by 'self.tvonly' more quickly).
            type = 1

            if (vpid == '0') or (vpid == '1'):

                # Skip channels of type '2', if 'self.tvonly' is set.
                if self.tvonly:
                    return

                type = 2

            # usually (on Enigma) the frequency is part of the namespace
            # for picons this seems to be unused, so disable it by now
            freq = 0;

            if source.startswith('S'):
                negative = False

                source = source[1:]
                if source.endswith('E'):
                    negative = True
                source = source[:-1]
                if '.' in source:
                    (number, decimal) = source.split('.')
                position = 10 * int(number) + int(decimal)
                if negative:
                    position = -position

                if position > 0x00007FFF:
                    position |= 0xFFFF0000

                if position < 0:
                    position = -position
                else:
                    position = 1800 + position

                hash = position << 16 | ((freq / 1000) & 0xFFFF)

            elif source.startswith('C'):
                hash = 0xFFFF0000 | ((freq / 1000) & 0xFFFF)

            elif source.startswith('T'):
                hash = 0xEEEE0000 | ((freq / 1000000) & 0xFFFF)

            if '=' in vpid:
                (pid, streamtype) = [x.strip() for x in vpid.split('=')]

                if streamtype == '2':
                    type = 1
                if streamtype == '27':
                    type = 19

            return '1_0_%i_%X_%X_%X_%X_0_0_0' % (
                    type,
                    sid,
                    tid,
                    nid,
                    hash
                )

        serviceRefs = dict()

        for (channelName, channelParams) in self.channels:
            # Determine serviceref and fill dictionary.
            serviceRef = _createserviceref(
                channelParams[2],
                int(channelParams[0]),
                channelParams[4],
                int(channelParams[8]),
                int(channelParams[9]),
                int(channelParams[10]))

            # A skipped channel (e.g. with 'self.tvonly') would return
            # None for serviceref. Don't add those to the dictionary
            if serviceRef is not None:
                serviceRefs[channelName] = serviceRef

        return serviceRefs

class PIcons(Channels):
    """ Find all available picons in a given path and determine
        the channels that can be linked automatically. """

    picons = []

    def __init__(self, channels_conf = '/etc/vdr/channels.conf', tvonly = False,
        provider_name = None, picons_dir = './picons'):
        # Initialize superclass
        super(PIcons, self).__init__(channels_conf = channels_conf,
            tvonly = tvonly, provider_name = provider_name)

        try:
            # List directory containing picons.
            piconDirList = os.listdir(picons_dir)
        except OSError:
            # Not found / not accessible.
            sys.exit ('ERROR: Could open %s' % picons_dir)

        # Filter for '.png' files.
        def png(x):
           return x.endswith('.png')
        piconDirList = filter(png, piconDirList)

        # Eliminate existing symlinks.
        def nosymlink(x):
            return not os.path.islink(os.path.join(picons_dir, x))
        piconDirList = filter(nosymlink, piconDirList)

        if piconDirList == []:
            # Empty directory or no '.png' files
            sys.exit ('ERROR: The directory %s does not contain any picons.' % picons_dir)

        # Fill class variable
        self.picons = [x[:-4] for x in piconDirList]

    def lnscript(self):
        """ Finally, create mapping between picon and serviceref.
            Return the result in form of a shell script. """
        
        links = dict()
        unmatched = []

        simpleNames = self.simplenames()
        serviceRefs = self.servicerefs()

        # Find matches (sorted by simplenames)
        for (channelName, simpleName) in (
            sorted(simpleNames.iteritems(), key=lambda (k,v): (v,k))):
            if simpleName in self.picons:
                links[simpleName] = (channelName, serviceRefs[channelName])
                continue
            unmatched.append(channelName)

        # Print out shell script
        if self.provider_name is not None:
            print '# %s\n' % self.provider_name

        for (src, dst) in sorted(links.iteritems()):
            (channelName, serviceRef) = dst
            print '# %s' % channelName
            print 'ln -s %s.png %s.png' % (src, serviceRef)
        
        # Print unmatched
        if unmatched != []:
            print '# unmatched channels:'

        for channelName in unmatched:
            print '# ln -s [%s] %s.png' % (
                channelName, serviceRefs[channelName])


def main():
    # Define commandline arguments
    parser = argparse.ArgumentParser(description="Automatically provide shell scripts for linking ocram's picons.")
    parser.add_argument('-c', '--channels',
        metavar = 'channels.conf',
        default = '/etc/vdr/channels.conf',
        help = 'pathname of channels.conf')
    parser.add_argument('-n', '--providername',
        metavar = 'MyProvider',
        default = None,
        help = "name of service provider (e.g. Sky)")
    parser.add_argument('-p', '--picondir',
        metavar = 'picons dir',
        default = './picons',
        help = "directory containing ocram's picons")
    parser.add_argument('-t', '--tvonly',
        action = 'store_true',
        default = False,
        help = "process TV channels only (i.e. no Radio)")
    
    argsDict = vars(parser.parse_args())

    # Instantiate
    picons = PIcons(channels_conf = argsDict['channels'],
        tvonly = argsDict['tvonly'],
        provider_name = argsDict['providername'],
        picons_dir = argsDict['picondir'])
    # Print script snippet
    picons.lnscript()

if __name__ == '__main__':
    sys.exit(main())
