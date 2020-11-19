#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Raw parsing of a dash mpd to display human readable timing info
The script does not go into xml and loading data, it is sequential

$ python3 mpdtimeline.py -f filename.mpd

pip install python-dateutil
pip install isodate


"""
import os
import sys
import re
import urllib.request
import datetime
from dateutil import parser,relativedelta
import isodate

def cleanmystring(s):
    """Return the string received in parameter with some leading and finishing characters deleted"""
    s = re.sub("^[ \n\t|]*","",s)
    s = re.sub("[ \n\t|]*$","",s)
    return s

def getAttrValue(attrName,line):
    return re.search('%s="([^\"]*)"' % attrName,line)[1]

def parseMPDFile(mpdFilename):
    """
    Parse MPD data from a file
    File must be indented
    """
    print("mpdtimeline.py::main - Parse '%s'" % (mpdFilename))
    mpdLines = []
    f = open(mpdFilename)
    l = f.readline()
    while l:
        l = cleanmystring(l)
        if l != "":
            mpdLines.append(l)
        l = f.readline() 
    f.close()

    parseMPDData(mpdLines)

def parseMPDData(mpdLines):
    """
    Parse MPD Data receive in an array, one line per item
    """
    availabilityStartTime = None
    periodIndex = -1
    adaptationSetIndex = -1
    for mpdLine in mpdLines: 
        try:
            #print("mpdtimeline.py::main - '%s'" % (mpdLine))
            if 'availabilityStartTime' in mpdLine : 
                availabilityStartTime =  parser.parse(getAttrValue("availabilityStartTime",mpdLine))
                print("G - Availibility start time - Zero point wall clock time : %s"  % (availabilityStartTime))
            if "<Period" in mpdLine: 
                periodIndex = periodIndex + 1
                adaptationSetIndex = -1 
                if "start" in mpdLine: 
                    period_start = isodate.parse_duration(getAttrValue("start",mpdLine))
                    print("G - Period %s Start: %s - Wall: %s" % (periodIndex,period_start,availabilityStartTime+period_start))  
                else: 
                    period_start = datetime.timedelta(0) # Should be the end of the previous period
                    print("Period Start: %s - Wall: %s" % ("Not set",availabilityStartTime+period_start))  
            if "<AdaptationSet" in mpdLine: 
                adaptationSetIndex = adaptationSetIndex + 1
            if "<SegmentTemplate" in mpdLine: 
                timescale = int(getAttrValue("timescale",mpdLine))   
                presentationTimeOffset =  int(getAttrValue("presentationTimeOffset",mpdLine))
                last_t = presentationTimeOffset
                print("P%02d - AS%02d - SegmentTemplate: timescale:%s presentationTimeOffset:%s - %s (Wall:%s)" % (
                    periodIndex,
                    adaptationSetIndex,
                    timescale,
                    presentationTimeOffset, datetime.timedelta(seconds=presentationTimeOffset/timescale),
                    availabilityStartTime+datetime.timedelta(seconds=presentationTimeOffset/timescale)+period_start)) # This wall time doesn't mean something
            if "<S " in mpdLine:
                t = 0
                d = -1
                r = 1
                if ' t="' in mpdLine: 
                    t = int(getAttrValue("t",mpdLine))
                else:
                    t = last_t
                if ' d="' in mpdLine: 
                    d = int(getAttrValue("d",mpdLine))
                if ' r="' in mpdLine:  
                    r = int(getAttrValue("r",mpdLine))
                print("P%02d - AS%02d - Segment: t:%s - %s d:%s - %s r:%d Wall:%s" % (
                    periodIndex,
                    adaptationSetIndex,
                    t,datetime.timedelta(seconds=t/timescale),
                    d,datetime.timedelta(seconds=d/timescale),
                    r,
                    availabilityStartTime+datetime.timedelta(seconds=((t-presentationTimeOffset)/timescale))+period_start,
                    ))
                last_t = t + d
        except Exception as ex:
            raise Exception("Failed to parse line '%s'.l.%s - %s" % (mpdLine, sys.exc_info()[2].tb_lineno, ex))


def main():
    """
    Main function to be called when the module is executed
    """
    print("mpdtimeline.py::main - Begin.")

    if '-f' in sys.argv:
        mpdFilename = sys.argv[sys.argv.index('-f')+1]
        parseMPDFile(mpdFilename)
 
    print("mpdtimeline.py::main - End.")
    return

if __name__ == "__main__":
    # execute only if run as a script
    main()
