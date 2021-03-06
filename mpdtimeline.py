#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Raw parsing of a dash mpd to display human readable timing info
The script does not go into xml and loading data, it is sequential

$ python3 mpdtimeline.py [-f filename.mpd] [-o (inline/log)] [-url RepresentationID]

pip install python-dateutil
pip install isodate

Essential info about mpd timing model :
https://github.com/google/shaka-player/blob/master/docs/design/dash-manifests.md
https://dashif-documents.azurewebsites.net/Guidelines-TimingModel/master/Guidelines-TimingModel.html

MPD to test : https://github.com/Dash-Industry-Forum/dash-live-source-simulator/wiki/Test-URLs

$ GET http://livesim.dashif.org/livesim/testpic_2s/Manifest.mpd | python3 mpdtimeline.py -o inline


TODO: support of suggestedPresentationDelay ? 

"""
import os
import sys
import re
import datetime
from dateutil import parser,relativedelta
import isodate
import requests
from urllib.parse import urljoin

def cleanmystring(s):
    """Return the string received in parameter with some leading and finishing characters deleted"""
    #s = re.sub("^[ \n\t|]*","",s)
    #s = re.sub("[ \n\t|]*$","",s)
    s = re.sub("^[\n]*","",s)
    s = re.sub("[\n]*$","",s)    
    return s

def getAttrValue(attrName,line):
    return re.search('%s="([^\"]*)"' % attrName,line)[1]

def parseMPDFile(mpdFilename,outputMode="log"):
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
        #if l != "":
        #    mpdLines.append(l)
        mpdLines.append(l)
        l = f.readline() 
    f.close()

    parseMPDData(mpdLines,outputMode)

def parseMpdUrl(mpdUrl,outputMode="log"):
    """
    Parse MPD data from an HTTP end point
    manifest must be indented
    """
    print("mpdtimeline.py::main - Get '%s'" % (mpdUrl))

    r = requests.get(mpdUrl,
        verify=False)
    if r.status_code != 200:
        raise Exception("Failed to download manifest. %s - %s" % (path,r.status_code,r.text))
    mpdLines = [str(k,'utf-8') for k in r.iter_lines() if k]

    parseMPDData(mpdLines,outputMode)

def getInlineOutput(dt,s):
    #return "%s; %s" % (dt.isoformat(timespec='microseconds'),s)
    return "%s; %s" % (dt.strftime('%Y-%m-%d T %H:%M:%S.%f'),s)

def expandRepetition(mpdLines):
    """
    Return a new array of mpd line with segment repetition expanded in
    """
    mpdLinesExpanded = []
    for mpdLine in mpdLines:
        if "<S " in mpdLine and ' r="' in mpdLine:
            r = int(getAttrValue("r",mpdLine))
            if r > 1:
                # Segment repetition S@r=5 means 6 segments, 1 + 5 repetitions
                mpdLinesExpanded.append('%s <!-- r="%d" removed -->' % (re.sub(r'r="\d+\"',"",mpdLine),r))
                newSegmentBaseLine = re.sub(r'r="\d+\"',"",mpdLine) # remove repetition
                newSegmentBaseLine = re.sub(r't="\d+\"',"",newSegmentBaseLine)    
                for segment_count in range(1,r+1):
                    mpdLinesExpanded.append("%s <!--simulate segment r %d -->" % (re.sub(r'r="\d+\"',"",newSegmentBaseLine),segment_count))
        else:
            mpdLinesExpanded.append(mpdLine)
    return mpdLinesExpanded

def parseMPDData(mpdLines,outputMode="log",hostUrl=""):
    """
    Parse MPD Data receive in an array, one line per item

        mpdLines - Array of lines from the mpd
        outputMode - Outmode mode. log (default) or inline to add wall clock label to the mpd
        hostUrl - string. To build full URL of segment 

    """
    availabilityStartTime = datetime.datetime.now() # Ok ? 
    periodIndex = -1
    adaptationSetIndex = -1
    currentWallTime = datetime.datetime.now()    
    timescale = 1 # Missing timescale should not happen on a real stream, so possibly let the error if not found ? 
    segment_url = None
    baseUrl = ""
    # object to print the summary at the end 
    periods = {} # Key: Period start line number
    lineIndex = 0
    init_url_pattern = None 
    currentPeriodKey = None
    currentSegmentTimelineKey = None
    for mpdLine in expandRepetition(mpdLines): 
        try:
            #print("mpdtimeline.py::main - '%s'" % (mpdLine))
            log = None
            inline = None
            lineIndex = lineIndex + 1
            if 'availabilityStartTime' in mpdLine : 
                availabilityStartTime =  parser.parse(getAttrValue("availabilityStartTime",mpdLine))
                log = "G - Availibility start time - Zero point wall clock time : %s"  % (availabilityStartTime)
                inline = getInlineOutput(availabilityStartTime,mpdLine)
                currentWallTime = availabilityStartTime
            if "<Period" in mpdLine: 
                periodIndex = periodIndex + 1
                adaptationSetIndex = -1 
                if "start" in mpdLine: 
                    period_start = isodate.parse_duration(getAttrValue("start",mpdLine))
                    log = "G - Period %s Start: %s - Wall: %s" % (periodIndex,period_start,availabilityStartTime+period_start) 
                else: 
                    period_start = datetime.timedelta(0) # Should be the end of the previous period
                    log = "Period Start: %s - Wall: %s" % ("Not set",availabilityStartTime+period_start)
                inline = getInlineOutput(availabilityStartTime+period_start,mpdLine)
                currentWallTime = availabilityStartTime+period_start
                currentPeriodKey = lineIndex
                periods[currentPeriodKey] = {"start":currentWallTime,"segmentTimelines":{}}
            if "<AdaptationSet" in mpdLine: 
                adaptationSetIndex = adaptationSetIndex + 1
            if "<BaseURL" in mpdLine:
                baseUrl = re.search (r"<BaseURL>(.*)<\/BaseURL",mpdLine)[1]

            if "<SegmentTemplate" in mpdLine: 
                # TODO : Build initialization segment url
                if 'initialization' in mpdLine:
                    init_url_pattern = getAttrValue("initialization",mpdLine)
                if 'media' in mpdLine:
                    media_url_pattern = getAttrValue("media",mpdLine)
                if 'startNumber' in mpdLine:
                    segNumber = int(getAttrValue("startNumber",mpdLine))
                else:
                    segNumber = 1
                if "timescale" in mpdLine:
                    timescale = int(getAttrValue("timescale",mpdLine))
                else:
                    # should raise an exception here, timescale of 1 second is not possible
                    pass
                if "presentationTimeOffset" in mpdLine:
                    presentationTimeOffset =  int(getAttrValue("presentationTimeOffset",mpdLine))
                else:
                    #Shouldn't we raise an exception here ? 
                    presentationTimeOffset = 0
                last_t = presentationTimeOffset
                log = "P%02d - AS%02d - SegmentTemplate: timescale:%s presentationTimeOffset:%s - %s (Wall:%s)" % (
                    periodIndex,
                    adaptationSetIndex,
                    timescale,
                    presentationTimeOffset, datetime.timedelta(seconds=presentationTimeOffset/timescale),
                    availabilityStartTime+datetime.timedelta(seconds=presentationTimeOffset/timescale)) 
                currentWallTime = availabilityStartTime+datetime.timedelta(seconds=presentationTimeOffset/timescale)
                inline = getInlineOutput(currentWallTime,mpdLine)
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
                    #if r > 1:
                    #    raise Exception("Segment repetition should be expanded")
                log = "P%02d - AS%02d - Segment: t:%s - %s d:%s - %s r:%d Wall:%s" % (
                    periodIndex,
                    adaptationSetIndex,
                    t,datetime.timedelta(seconds=t/timescale),
                    d,datetime.timedelta(seconds=d/timescale),
                    r,
                    availabilityStartTime+datetime.timedelta(seconds=((t-presentationTimeOffset)/timescale))+period_start,
                    )
                
                segment_url = media_url_pattern.replace("$Time$",str(t))
                segment_url = segment_url.replace("$Number$",str(segNumber))
                segment_url = os.path.join(baseUrl,segment_url)
                periods[currentPeriodKey]["segmentTimelines"][currentSegmentTimelineKey]["segments"].append(segment_url)
                segment_url = "<!-- Segment url : %s  -->" % (segment_url) 
                
                currentWallTime = availabilityStartTime+datetime.timedelta(seconds=((t-presentationTimeOffset)/timescale))+period_start
                if currentSegmentTimelineKey:
                    if not "start" in periods[currentPeriodKey]["segmentTimelines"][currentSegmentTimelineKey].keys():
                        periods[currentPeriodKey]["segmentTimelines"][currentSegmentTimelineKey] ["start"] = currentWallTime    
                    periods[currentPeriodKey]["segmentTimelines"][currentSegmentTimelineKey] ["stop"] = currentWallTime + datetime.timedelta(seconds=d/timescale)
                inline = getInlineOutput(currentWallTime,mpdLine)
                last_t = t + d
                segNumber = segNumber + 1
            if '<SegmentTimeline' in mpdLine:
                currentSegmentTimelineKey = lineIndex
                periods[currentPeriodKey]["segmentTimelines"][currentSegmentTimelineKey] = {}
                periods[currentPeriodKey]["segmentTimelines"][currentSegmentTimelineKey]["segments"] = []
            if "<Representation" in mpdLine: 
                reprId = getAttrValue("id",mpdLine)
                print("New representation: '%s'" % (reprId))
                big_wget = ""
                if init_url_pattern:
                    init_url = init_url_pattern.replace("$RepresentationID$",reprId)
                    print("Init - %s - %s" % (reprId,urljoin(hostUrl,init_url)))
                for sUrl in periods[currentPeriodKey]["segmentTimelines"][currentSegmentTimelineKey]["segments"]:
                    print("Segment - %s - %s" % (reprId,urljoin(hostUrl,sUrl.replace("$RepresentationID$",reprId))))
            if outputMode == "log" and log: 
                print(log)
            if outputMode == "inline":
                if not inline:
                    inline = getInlineOutput(currentWallTime,mpdLine)
                print(inline)
                if segment_url:
                    print(segment_url)
                    segment_url = None
        except Exception as ex:
            raise Exception("Failed to parse line '%s'.l.%s - %s" % (mpdLine, sys.exc_info()[2].tb_lineno, ex))
    if True: 
        # Print sumary 
        print("##\n## Summary ##\n##")
        for (period_line,period) in periods.items():
            print("l:%d - Period starting at %s" % (period_line,period["start"]))
            for (segmentTimeline_line,segmentTimeline) in period["segmentTimelines"].items():
                print("    l.%d - SegmentTimeline from %s to %s" % (segmentTimeline_line,
                                                                segmentTimeline["start"],
                                                                segmentTimeline["stop"]))

def main():
    """
    Main function to be called when the module is executed
    """
    print("mpdtimeline.py::main - Begin.")

    outputMode = "log"
    hostUrl = None

    if '-o' in sys.argv:
        outputMode = sys.argv[sys.argv.index('-o')+1]

    if '-host' in sys.argv:
        hostUrl = sys.argv[sys.argv.index('-host')+1]

    if '-f' in sys.argv:
        mpdFilename = sys.argv[sys.argv.index('-f')+1]
        parseMPDFile(mpdFilename,outputMode)
    elif '-http' in sys.argv:
        mpdUrl = sys.argv[sys.argv.index('-http')+1]
        parseMpdUrl(mpdUrl,outputMode)
    else:
        parseMPDData([cleanmystring(k) for k in sys.stdin],outputMode,hostUrl)
 
    print("mpdtimeline.py::main - End.")
    return

if __name__ == "__main__":
    # execute only if run as a script
    main()
