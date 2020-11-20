# dashtools
Some tools around the DASH OTT format

## mpdtimeline.py ## 
A python script that reads line per line a DASH MPD input and tries to compute the wall clock time of each of them. It doesn't mean something every time but in some cases it is very useful. The script does not go into xml and loading data, it is linear sequential. An option allows to build the urls of the segments once some input parameters are provided, or with some sed replacement on the output of the script.

### Usage example ###

`$ GET http://livesim.dashif.org/livesim/segtimeline_1/testpic_2s/Manifest.mpd | python3 mpdtimeline.py -o inline -url A48 | head -n 100 
mpdtimeline.py::main - Begin.
2020-11-20 T 18:59:39.702367; <?xml version="1.0" encoding="utf-8"?>
1970-01-01 T 00:00:00.000000; <MPD xmlns="urn:mpeg:dash:schema:mpd:2011" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" availabilityStartTime="1970-01-01T00:00:00Z" id="Config part of url maybe?" minBufferTime="PT2S" minimumUpdatePeriod="PT0S" profiles="urn:mpeg:dash:profile:isoff-live:2011,http://dashif.org/guidelines/dash-if-simple" publishTime="2020-11-20T17:59:39Z" timeShiftBufferDepth="PT5M" type="dynamic" xsi:schemaLocation="urn:mpeg:dash:schema:mpd:2011 DASH-MPD.xsd">
1970-01-01 T 00:00:00.000000;    <ProgramInformation>
1970-01-01 T 00:00:00.000000;       <Title>Media Presentation Description from DASH-IF live simulator</Title>
1970-01-01 T 00:00:00.000000;    </ProgramInformation>
1970-01-01 T 00:00:00.000000;    <BaseURL>http://livesim.dashif.org/livesim/sts_1605895179/sid_6923a2a0/segtimeline_1/testpic_2s/</BaseURL>
1970-01-01 T 00:00:00.000000; <Period id="p0" start="PT0S">
1970-01-01 T 00:00:00.000000;       <AdaptationSet contentType="audio" lang="en" mimeType="audio/mp4" segmentAlignment="true" startWithSAP="1">
1970-01-01 T 00:00:00.000000;          <Role schemeIdUri="urn:mpeg:dash:role:2011" value="main" />
1970-01-01 T 00:00:00.000000;          <SegmentTemplate initialization="$RepresentationID$/init.mp4" media="$RepresentationID$/t$Time$.m4s" timescale="48000">
1970-01-01 T 00:00:00.000000; <SegmentTimeline>
2020-11-20 T 17:54:38.016000; <S d="95232" t="77082954144768" />
<!-- Segment url : http://livesim.dashif.org/livesim/sts_1605895179/sid_6923a2a0/segtimeline_1/testpic_2s/A48/t77082954144768.m4s  -->
2020-11-20 T 17:54:40.000000; <S d="96256"  /> <!-- r="2" removed -->
<!-- Segment url : http://livesim.dashif.org/livesim/sts_1605895179/sid_6923a2a0/segtimeline_1/testpic_2s/A48/t77082954240000.m4s  -->
2020-11-20 T 17:54:42.005333; <S d="96256"  /> <!--simulate segment r 1 -->
<!-- Segment url : http://livesim.dashif.org/livesim/sts_1605895179/sid_6923a2a0/segtimeline_1/testpic_2s/A48/t77082954336256.m4s  -->
2020-11-20 T 17:54:44.010667; <S d="96256"  /> <!--simulate segment r 2 -->
<!-- Segment url : http://livesim.dashif.org/livesim/sts_1605895179/sid_6923a2a0/segtimeline_1/testpic_2s/A48/t77082954432512.m4s  -->
2020-11-20 T 17:54:46.016000; <S d="95232" />
<!-- Segment url : http://livesim.dashif.org/livesim/sts_1605895179/sid_6923a2a0/segtimeline_1/testpic_2s/A48/t77082954528768.m4s  -->
2020-11-20 T 17:54:48.000000; <S d="96256"  /> <!-- r="2" removed -->
<!-- Segment url : http://livesim.dashif.org/livesim/sts_1605895179/sid_6923a2a0/segtimeline_1/testpic_2s/A48/t77082954624000.m4s  -->
2020-11-20 T 17:54:50.005333; <S d="96256"  /> <!--simulate segment r 1 -->
<!-- Segment url : http://livesim.dashif.org/livesim/sts_1605895179/sid_6923a2a0/segtimeline_1/testpic_2s/A48/t77082954720256.m4s  -->
2020-11-20 T 17:54:52.010667; <S d="96256"  /> <!--simulate segment r 2 -->
<!-- Segment url : http://livesim.dashif.org/livesim/sts_1605895179/sid_6923a2a0/segtimeline_1/testpic_2s/A48/t77082954816512.m4s  -->`

