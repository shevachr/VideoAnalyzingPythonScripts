# Video Analyzing Python  Scripts

**Python scripts to analyze video files**

**1) The script RemoveSeiInH264Stream.py**  

tailored to remove SEI messages specified by sei_type (e.g. sei_type=0 is buffering period SEI message).

**Note**: with ffmpeg you can remove all SEI NALUs regardless to sei_type:  *ffmpeg -i test.mp4 -c:v copy  -c:a copy   -bsf:v 'filter_units=remove_types=6'   test_nosei.mp4*


reminder: nal-type of SEI message is 6 in h264

The removal process of the python script  is not in-place therefore the output stream must be different from the input one.

If the input stream does not contain a specified sei_type then no output stream is generated. Notice that most of SEI messages carry auxiliary information and can be removed from the stream (although the appearence of video might be affected in some cases).

**Example [ removal of SEI messages with sei_type=5 ]**: *python RemoveSeiInH264Stream.py out.h264  5  out1.h264*

This script can be useful to adapt a video stream to be playable by Microsoft Media Player (since SEI bueffering period prior to SPS makes the stream not playable.
 
 <br>

 

**2) Get H264/AVC Video Statistics from Transport Stream**

The script **GetAVCVideoStatsFromTS.py** (adapted to Python 2.x) and **GetAVCVideoStatsFromTSVer3.py** (adapted to Python 3.x) are tailored to pick statistics (frame size, dts/pts. frame duration etc.) from video AVC/H.264 stream comprised in Mpeg System container ( Transport format files usually ending with '.ts'). It's worth mentioning that the frame start is detected if a video ts-packet contains the PES header with the timestamp DTS (to avoid counting of frame slices).

**Usage:**

 -i           input ts-file, a section of ts-stream can be provided (even without SPS/PPS, unlike to 'ffmpeg')
 
 -v          print pts, dts and sizes of each video frame (default false)
 
 -a          ignore AUD (Access Unit Delimiter) violations (AUD is mandatory in Transport Stream but sometimes AUDs are absent and most of players copes with that violation),   default  false
 
 -p          print progress  bar (the length is 80), default false. If verbose is ON then the progress bar disappears. 

**Example [Print Number of detected frames, if AUD is absent a corresponding error reported  ]**

python GetAVCVideoStatsFromTS.py -i test.ts

*Number of Frames        900*

*Video Size in bytes     17415224*


**Example [Print Frame Statistics ignoring AUD violations, verbose mode on  ]**


*python GetAVCVideoStatsFromTS.py -i test.ts -a -v*

*0   Size  50711, dts  126000,   pts  126000*

*1   Size  4517, dts  129600,   pts  129600, frame duration 40.00*

*2   Size  8079, dts  132600,   pts  132600, frame duration 33.33*

.....

*896   Size  19537, dts  2814573,   pts  2814573, frame duration 33.33*

*897   Size  23225, dts  2817573,   pts  2817573, frame duration 33.33*

*898   Size  1622, dts  2820573,   pts  2820573, frame duration 33.33*

*899   Size  28580, dts  2823573,   pts  2823573, frame duration 33.33*


*Minimal DTS diff (in ms)  33.32, attained at frame 17*

*Minimal PTS diff (in ms)  33.32, attained at frame 17*

*Maximal DTS diff (in ms)  40.00, attained at frame 0*


*Number of Frames        900*
*Video Size in bytes     17415224*


<br>
<br>


**3) Get Picture Statistics From HEVC/H.264 Elementary Stream**

**HEVC Case:**

The script **GetPictureStatsHevcVer3.py** (adapted to python 3.x) gathers and prints frame starts and offsets (in hex) as well as frame types.

Usage:

-i    input hevc file

-n    maximal number of frames to process, if 0 then the whole file processed, (default 0)


**Example [print 10 frames]**

       *python GetPictureStatsHevcVer3.py  -i test.h265 -n 10*

*idr                        0            f8*

*pb                        f8            3f*

*pb                       137            38*

*pb                       16f            38*

*pb                       1a7           4b0*

*pb                       657           28d*

*pb                       8e4           18c*

*pb                       a70           201*

*pb                       c71           dd2*

*pb                      1a43             0*


**Notes:** 

the first column is frame type: IDR, BLA, RASL, RADL or 'pb' (meaning regular frame of type TRAIL).

the second column is frame start offset in hex.

the third column is frame size (in hex). An attentive reader might notice that the size of the last frame is 0. It's not a bug, in order to get the size of the 10th frame we need process 11 frames but we constraint the script to proceed only 10 frames.



**H264 Case:**

The script **GetPictureStatsH264.py** gathers and prints frame starts and offsets (in hex) as well as frame types of h264 elementary stream.

Usage:

-i    input h264 file

-n    maximal number of frames to process, if 0 then the whole file processed, (default 0)

**Example [print 10 frames]**

*python GetPictureStatsH264.py -i crowd_qsv.h264 -n 10

*idr 0            8e1ad*

*pb 8e1ad        53618*

*pb e17c5        1a2d4*

*pb fba99        eb02*

*pb 10a59b     e82d*

*pb 118dc8     2e4bd*

*pb 147285    d33e*

*pb 1545c3    69b3*

*pb 15af76     7015*

*pb 161f8b*      // if '-n' is applied then the last frame size is omitted

**Notes:**

the first column is frame type: 'idr' or 'pb' (meaning P, B or non-IDR  I-frames).

the second column is frame start offset in hex.

the third column is frame size (in hex).

<br>

**4) Get PSNR, SSIM and VIFP (Visual Information Fidelity) with 'sewar' python module**

The **‘sewar’** python package contains different image and video quality metrics (PSNR,SSIM,MS-SSIM,VIFP etc.).

To install ‘sewar’ type: pip install sewar

The scripts **GetPsnr.py** , **GetSSIM.py** and **GetVifp.py** take as input reference and deformed yuv420p@8bpp video sequences and computes PSNR, SSIM and VIFP (Visual Information Fidelity) score per picture.

Usage:

-f                reference yuv-sequence (yuv420p@8bpp)

-d               deformed yuv-sequence (yuv420p@8bpp) 

-n               number of frames to process, if 0 then all frames, default 0

--width      width in pixels

--height     height in pixels

 

**Example [ compute psnr values of first 10 frames]**

*python GetPsnr.py --width 1920 --height 1080 -f Fifa17_1920x1080.yuv -d fifa_hp_cbr16_10M.yuv -n 10*


*frame 0, psnr 30.53*

*frame 1, psnr 32.48*

*frame 2, psnr 33.20*

*frame 3, psnr 34.46*

*frame 4, psnr 33.86*

*frame 5, psnr 33.63*

*frame 6, psnr 33.35*

*frame 7, psnr 33.09*

*frame 8, psnr 32.88*

*frame 9, psnr 32.60*

*average psnr 33.01*

 

**Example [ compute SSIM values of first 10 frames]**

*python GetSsim.py --width 1920 --height 1080 -f Fifa17_1920x1080.yuv -d fifa_hp_cbr16_10M.yuv -n 10

*frame 0, ssim 0.84*

*frame 1, ssim 0.87*

*frame 2, ssim 0.89*

*frame 3, ssim 0.91*

*frame 4, ssim 0.90*

*frame 5, ssim 0.90*

*frame 6, ssim 0.90*

*frame 7, ssim 0.90*

*frame 8, ssim 0.89*

*frame 9, ssim 0.89*

*average ssim 0.89*

 

**Example [ compute VIFP scores of first 10 frames]**

*python GetVifp.py --width 1920 --height 1080 -f Fifa17_1920x1080.yuv -d fifa_hp_cbr16_10M.yuv -n 10*

*frame 0, vifp 0.29*

*frame 1, vifp 0.36*

*frame 2, vifp 0.40*

*frame 3, vifp 0.44*

*frame 4, vifp 0.43*

*frame 5, vifp 0.43*

*frame 6, vifp 0.43*

*frame 7, vifp 0.42*

*frame 8, vifp 0.42*

*frame 9, vifp 0.41*

*average vifp 0.40*

**Note:** to get (or to extract) yuv-sequence from encoded stream i use ffmpeg tool:

*ffmpeg -i fifa_hp_cbr16_15M.h264 -pixel_format yuv420p -frames 100 -y fifa_hp_cbr16_15M.yuv*

<br>

**5) Parse Slice Header and Print Weighted Prediction Parameters, H.264**

The weighted prediction was adopted by H.264/AVC. In some video sequences, in particular those containg fading between scenes, the current picture  is more strongly correlated to a reference picture scaled by a weighting factor.

The python script **PrintWeightsH264**  gets as input H.264/AVC stream and parses SPS, PPS and slice headers. The script prints the weghted prediction information if it’s present in the slice header.

Usage:

-i         input h264-file

-n        number frames to process, if 0 then the whole stream processed, default 0

-v        verbose mode, print SPS and PPS info (default false)
<br>
**Example [encode 4 frames in verbose mode (i.e. printing SPS and PPS)]:**

*python PrintWeightsH264.py    -i test.h264    -n 3     -v*

***SPS***

*profile_idc 100*

*level_idc    50*

*sps_id          0*

*log2_max_frame_num 4*

*log2_max_pic_order_cnt 10*

*max_num_ref_frames 1*

*gaps_in_frame_num_value_allowed_flag 0*

*pic_width_in_mbs 120*

*pic_width_in_mbs 68*

*frame_mbs_only_flag 1*

*direct_8x8_inference_flag 1*

***PPS***

*pps_id 0*

*sps_id 0*

*bottom_field_pic_order_in_frame_present_flag 0*

*num_ref_idx_l0 1*

*num_ref_idx_l1 1*

*weighted_pred_flag 1*

*weighted_bipred_idc 0*

*pic_init_qp 26*

*chroma_qp_index_offset 0*

*deblocking_filter_control_present_flag 0*

*constrained_intra_pred_flag 0*

***Frame 0***


*Slice*

*first_mb 0*

*slice type I*

*pps_id 0*

*frame_num 0*

*idr_idx 0*

*POC 0*

***Frame 1***


*Slice*

*first_mb 0*

*slice type P*

*pps_id 0*

*frame_num 1*

*POC 2*

*override flag 0*

*ref_pic_list_modification_flag_l0 0*

***luma_log2_weight_denom 5***

***chroma_log2_weight_denom 5***

***luma_weight_l0_flag 1***

***luma_weight_l0 33***

***luma_offset_l0 -2***

***chroma_weight_l0_flag 0***


**6) Count Short Start Codes (H264)**

The H264/AVC spec. contains two types of start-codes:  long (32 bits, 00 00 00 01) and short (24 bits, 00 00 01)

During my career, once I was faced with a peculiar h264 decoder which ignored short start-codes (and respected long start codes). This decoder could not find the slice start if the start code was short.

I share the python script **CountShortStartCodesInH264.py** which detects and count short start codes in h264 file. In addtion this script counts the number of frames.


Usage:

-i          input h264 file

-v         verbose mode, print offset of short start code (default false)

-n         number frames to process, if 0 then the whole stream processed




**Example:**

*python CountShortStartCodesInH264.py -i  battlefield_hp_cbr16_10M.h264*

*number of detected frames 557*

*number of short start codes 1672*

Note:  why number of start codes is greater than the number of frames? In the given stream each frame is divided into four slices. Thus each frame contains four start codes.




**Example (process two frames in verbose mode)**


*python CountShortStartCodesInH264.py -i battlefield_hp_cbr16_10M.h264 -n 2 -v*

*short start code at offset 4467 (0x1173)*

*short start code at offset 8600 (0x2198)*

*short start code at offset 15524 (0x3ca4)*

*short start code at offset 20005 (0x4e25)*

*number of detected frames 2*

*number of short start codes 4*



