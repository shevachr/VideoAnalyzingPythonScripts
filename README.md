# VideoAnalyzingPythonScripts

Python scripts to analyze video files

1) The script RemoveSeiInH264Stream.py  tailored to remove SEI messages specified by sei_type (e.g. sei_type=0 is buffering period SEI message).

Note: with ffmpeg you can remove all SEI NALUs regardless to sei_type:

ffmpeg -i test.mp4 -c:v copy  -c:a copy   -bsf:v 'filter_units=remove_types=6'   test_nosei.mp4


reminder: nal-type of SEI message is 6 in h264

The removal process of the python script  is not in-place therefore the output stream must be different from the input one.

If the input stream does not contain a specified sei_type then no output stream is generated. Notice that most of SEI messages carry auxiliary information and can be removed from the stream (although the appearence of video might be affected in some cases).

Example [ removal of SEI messages with sei_type=5 ]: python RemoveSeiInH264Stream.py out.h264  5  out1.h264

This script can be useful to adapt a video stream to be playable by Microsoft Media Player (since SEI bueffering period prior to SPS makes the stream not playable.
 
 

 

2) Get H264/AVC Video Statistics from Transport Stream

The script   GetAVCVideoStatsFromTS.py (adapted to Python 2.x) and GetAVCVideoStatsFromTSVer3.py (adapted to Python 3.x) are tailored to pick statistics (frame size, dts/pts. frame duration etc.) from video AVC/H.264 stream comprised in Mpeg System container ( Transport format files usually ending with '.ts'). It's worth mentioning that the frame start is detected if a video ts-packet contains the PES header with the timestamp DTS (to avoid counting of frame slices).

Usage:

 -i           input ts-file, a section of ts-stream can be provided (even without SPS/PPS, unlike to 'ffmpeg')
 
 -v          print pts, dts and sizes of each video frame (default false)
 
 -a          ignore AUD (Access Unit Delimiter) violations (AUD is mandatory in Transport Stream but sometimes AUDs are absent and most of players copes with that violation),   default  false
 
  -p          print progress  bar (the length is 80), default false. If verbose is ON then the progress bar disappears. 

Example [Print Number of detected frames, if AUD is absent a corresponding error reported  ]

python GetAVCVideoStatsFromTS.py -i test.ts
Number of Frames        900
Video Size in bytes     17415224


Example [Print Frame Statistics ignoring AUD violations, verbose mode on  ]


python GetAVCVideoStatsFromTS.py -i test.ts -a -v

0   Size  50711, dts  126000,   pts  126000

1   Size  4517, dts  129600,   pts  129600, frame duration 40.00

2   Size  8079, dts  132600,   pts  132600, frame duration 33.33

.....

896   Size  19537, dts  2814573,   pts  2814573, frame duration 33.33

897   Size  23225, dts  2817573,   pts  2817573, frame duration 33.33

898   Size  1622, dts  2820573,   pts  2820573, frame duration 33.33

899   Size  28580, dts  2823573,   pts  2823573, frame duration 33.33


Minimal DTS diff (in ms)  33.32, attained at frame 17

Minimal PTS diff (in ms)  33.32, attained at frame 17

Maximal DTS diff (in ms)  40.00, attained at frame 0


Number of Frames        900
Video Size in bytes     17415224






3) Get Picture Statistics From HEVC/H.264 Elementary Stream

HEVC Case:

The script GetPictureStatsHevcVer3.py (adapted to python 3.x) gathers and prints frame starts and offsets (in hex) as well as frame types.

Usage:

-i    input hevc file

-n    maximal number of frames to process, if 0 then the whole file processed, (default 0)


Example [print 10 frames]

       python GetPictureStatsHevcVer3.py  -i test.h265 -n 10

idr                        0            f8

pb                        f8            3f

pb                       137            38

pb                       16f            38

pb                       1a7           4b0

pb                       657           28d

pb                       8e4           18c

pb                       a70           201

pb                       c71           dd2

pb                      1a43             0


Notes: 

the first column is frame type: IDR, BLA, RASL, RADL or 'pb' (meaning regular frame of type TRAIL).

the second column is frame start offset in hex.

the third column is frame size (in hex). An attentive reader might notice that the size of the last frame is 0. It's not a bug, in order to get the size of the 10th frame we need process 11 frames but we constraint the script to proceed only 10 frames.



H264 Case:

The script GetPictureStatsH264.py gathers and prints frame starts and offsets (in hex) as well as frame types of h264 elementary stream.

Usage:

-i    input h264 file

-n    maximal number of frames to process, if 0 then the whole file processed, (default 0)

Example [print 10 frames]

python GetPictureStatsH264.py -i crowd_qsv.h264 -n 10

idr 0                8e1ad

pb 8e1ad        53618

pb e17c5        1a2d4

pb fba99        eb02

pb 10a59b     e82d

pb 118dc8     2e4bd

pb 147285    d33e

pb 1545c3    69b3

pb 15af76     7015

pb 161f8b      // if '-n' is applied then the last frame size is omitted

Notes: 
the first column is frame type: 'idr' or 'pb' (meaning P, B or non-IDR  I-frames).
the second column is frame start offset in hex.
the third column is frame size (in hex).
