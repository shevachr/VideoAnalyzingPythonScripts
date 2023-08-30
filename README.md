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
