import sys
import os
import struct
import bitstring
import re
from optparse import OptionParser

"""
Copyright (c) 2018 Shevach Riabtsev, slavah264@gmail.com

Redistribution and use of source is permitted
provided that the above copyright notice and this paragraph are
duplicated in all such forms and that any documentation,
advertising materials, and other materials related to such
distribution and use acknowledge that the software was developed
by the Shevach Riabtsev, slavah264@gmail.com. The name of the
Shevach Riabtsev, slavah264@gmail.com may not be used to endorse or promote
products derived from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
"""
g_frameCnt=0

def parse_options():
    parser = OptionParser(usage="%prog [-i] [-n] [-v]", version="%prog 1.1")

    parser.add_option("-i",
                        dest = "filename",
                        help = "input h264-file",
                        type = "string",
                        action = "store"
                        )
    parser.add_option("-n",
                        dest = "framesToProcess",
                        help = "number frames to process, if 0 then the whole stream processed",
                        type = "int",
                        action = "store",
                        default=0
                        )
                        
    parser.add_option("-v",
                        dest = "verbose",
                        help = "verbose mode, print SPS and PPS info  (default false)",
                        action="store_true",
                        default=False)
                        
                        
    (options, args) = parser.parse_args()
    
    if options.framesToProcess<0:
        print ("\nnegative number of frames to process - error\n", file=sys.stderr)
        parser.print_help()
        quit(-1)
        
   
    if options.filename:
        if os.path.isfile(options.filename)==False:
            print('Input file not exist or directory', file=sys.stderr)
            parser.print_help()
            quit(-1)
        
        return (options.filename, options.framesToProcess, options.verbose) 
        
    parser.print_help()
    quit(-1)


def ToRbsp(oldStr):
    newStr=oldStr
    iter = re.finditer('00000300|00000301|00000302', oldStr)
    ll = [m.start(0) for m in iter]
    if ll==[]:
        return newStr
        
    indices = [x for x in ll if x&1==0]
    if indices==[]:
        return newStr
    s=0
    for k in indices:
        tmpStr = newStr[0:k-s] +  oldStr[k:].replace('000003','0000',1)
        s+=2
        newStr = tmpStr
    return newStr



def ParseSPS(spsBytes, spsLen, spsInfo,verbose=False):
    """ Parse H.264 SPS without VUI 
        no start code, but nalheader present
    """

    c = bitstring.BitArray(bytes=spsBytes, length=spsLen*8)
    newStr = ToRbsp(c.hex) # to remove emulation-prevention bytes (if exist)
    
    s = bitstring.BitStream('0x'+newStr)
    

    profile_idc = s.read('uint:8')
    if verbose:
        print('\nSPS\nprofile_idc                                 %d' %profile_idc)
        
    spsInfo['profile_idc']= profile_idc
    constraint_flags = s.readlist('4*uint:1')
    reserved_zero_4bits = s.read('uint:4')
    if reserved_zero_4bits:
        print('warning: reserved_zero_4bits is not zero')
    
    level_idc = s.read('uint:8')
    if verbose:
        print('level_idc                                   %d' %level_idc)
    spsInfo['level']=level_idc
    
    seq_parameter_set_id = s.read('ue')
    spsInfo['sps_id']=seq_parameter_set_id
    if verbose:
        print('sps_id                                      %d' %seq_parameter_set_id)
        
    if profile_idc in [100, 110, 122, 244, 44, 83, 86]:
        chroma_format_idc = s.read('ue')
        if chroma_format_idc == 3:
            print('parsing of chroma_format_idc=3 not supported yet')
            return False
            
        bit_depth_luma = s.read('ue')+8
        bit_depth_chroma = s.read('ue')+8
        
        qpprime_y_zero_transform_bypass_flag = s.read('uint:1')
        
        seq_scaling_matrix_present_flag = s.read('uint:1')
        if seq_scaling_matrix_present_flag:
            print('scaling matrix parsing not supported yet')
            return False
            
    log2_max_frame_num = s.read('ue')+4
    spsInfo['log2_max_frame_num']=log2_max_frame_num
    if verbose:
        print('log2_max_frame_num                          %d' %log2_max_frame_num)
    pic_order_cnt_type = s.read('ue')
    spsInfo['pic_order_cnt_type']=pic_order_cnt_type
    if pic_order_cnt_type==1:
       print('parsing of pic_order_cnt_type=1 not supported yet')
       return False
       
    log2_max_pic_order_cnt_lsb=0
    if pic_order_cnt_type==0:
        log2_max_pic_order_cnt_lsb = s.read('ue')+4
    spsInfo['log2_max_pic_order_cnt_lsb']=log2_max_pic_order_cnt_lsb
    if verbose:
        print('log2_max_pic_order_cnt                      %d' %log2_max_pic_order_cnt_lsb)
    max_num_ref_frames = s.read('ue')
    spsInfo['max_num_ref_frames']=max_num_ref_frames
    if verbose:
        print('max_num_ref_frames                          %d' %max_num_ref_frames)
    gaps_in_frame_num_value_allowed_flag = s.read('uint:1')
    spsInfo['gaps_in_frame_num_value_allowed_flag']=gaps_in_frame_num_value_allowed_flag
    if verbose:
        print('gaps_in_frame_num_value_allowed_flag        %d' %gaps_in_frame_num_value_allowed_flag)
    pic_width_in_mbs = s.read('ue')+1
    spsInfo['pic_width_in_mbs']=pic_width_in_mbs
    if verbose:
        print('pic_width_in_mbs                            %d' %pic_width_in_mbs)
    pic_height_in_mbs = s.read('ue')+1
    spsInfo['pic_height_in_mbs']=pic_height_in_mbs
    if verbose:
        print('pic_height_in_mbs                           %d' %pic_height_in_mbs)
    frame_mbs_only_flag = s.read('uint:1')
    spsInfo['frame_mbs_only_flag']=frame_mbs_only_flag
    if verbose:
        print('frame_mbs_only_flag                         %d' %frame_mbs_only_flag)
    if frame_mbs_only_flag==0:
        mbaff = s.read('uint:1')
        
    direct_8x8_inference_flag = s.read('uint:1')
    spsInfo['direct_8x8_inference_flag']=direct_8x8_inference_flag
    if verbose:
        print('direct_8x8_inference_flag                   %d' %direct_8x8_inference_flag)
        print('\n')
    return True

def ParsePPS(ppsBytes, ppsLen,ppsInfo,verbose=False):
    """ Parse H.264 PPS 
    """
    c = bitstring.BitArray(bytes=ppsBytes, length=ppsLen*8)
    newStr = ToRbsp(c.hex) # to remove emulation-prevention bytes (if exist)
        
    s = bitstring.BitStream('0x'+newStr)
    # skip nal header
    #s.read('uint:8')
    
    pic_parameter_set_id = s.read('ue')
    if verbose:
        print('\nPPS\npps_id                                      %d' %pic_parameter_set_id)
    ppsInfo['pic_parameter_set_id']=pic_parameter_set_id
    seq_parameter_set_id = s.read('ue')
    if verbose:
        print('sps_id                                      %d' %seq_parameter_set_id)
    ppsInfo['seq_parameter_set_id']=seq_parameter_set_id
    entropy_coding_mode_flag = s.read('uint:1')
    if entropy_coding_mode_flag==0:
        print('Entropy Mode   CAVLC')
        return False
    
    bottom_field_pic_order = s.read('uint:1')
    ppsInfo['bottom_field_pic_order_in_frame_present_flag']=bottom_field_pic_order
    if verbose:
        print('bottom_field_pic_order_in_frame_present_flag    %d' %bottom_field_pic_order)
   
    num_slice_groups_minus1 = s.read('ue')
    if num_slice_groups_minus1>0:
        print('num_slice_groups %d > 1, parsing stopped' %(num_slice_groups_minus1+1))
        return False
    
    num_ref_idx_l0_default_active = s.read('ue')+1
    ppsInfo['num_ref_idx_l0']=num_ref_idx_l0_default_active
    num_ref_idx_l1_default_active = s.read('ue')+1
    ppsInfo['num_ref_idx_l1']=num_ref_idx_l1_default_active
    if verbose:
        print('num_ref_idx_l0                              %d' %num_ref_idx_l0_default_active)
        print('num_ref_idx_l1                              %d' %num_ref_idx_l1_default_active)
    weighted_pred_flag = s.read('uint:1')
    ppsInfo['weighted_pred_flag']=weighted_pred_flag
    if verbose:
        print('weighted_pred_flag                          %d' %weighted_pred_flag)
        
    weighted_bipred_idc = s.read('uint:2')
    ppsInfo['weighted_bipred_idc']=weighted_bipred_idc
    if weighted_bipred_idc==1:
        print('Explicit B-prediction is not supported')
        return False
    if verbose:
        print('weighted_bipred_idc                         %d' %weighted_bipred_idc)
    pic_init_qp = s.read('se')+26
    ppsInfo['pic_init_qp']=pic_init_qp
    if verbose:
        print('pic_init_qp                                 %d' %pic_init_qp)
    # ignore pic_init_qs
    s.read('se')
    
    chroma_qp_index_offset = s.read('se')
    ppsInfo['chroma_qp_index_offset']=chroma_qp_index_offset
    if verbose:
        print('chroma_qp_index_offset                      %d' %chroma_qp_index_offset)
    deblocking_filter_control_present_flag = s.read('uint:1')
    ppsInfo['deblocking_filter_control_present_flag']=deblocking_filter_control_present_flag
    if verbose:
        print('deblocking_filter_control_present_flag      %d' %deblocking_filter_control_present_flag)
        
    constrained_intra_pred_flag = s.read('uint:1')
    ppsInfo['constrained_intra_pred_flag']=constrained_intra_pred_flag
    if verbose:
        print('constrained_intra_pred_flag                 %d' %constrained_intra_pred_flag)
    redundant_pic_cnt_present_flag = s.read('uint:1')
    if redundant_pic_cnt_present_flag:
        return False
        
    return True    
    
def ParseSliceHeader(sliceHdr,sliceHdrLen,spsInfo,ppsInfo,verbose=True):

    global g_frameCnt
    
    c = bitstring.BitArray(bytes=sliceHdr, length=sliceHdrLen*8)
    newStr = ToRbsp(c.hex) # to remove emulation-prevention bytes (if exist)
        
    s = bitstring.BitStream('0x'+newStr)
   
    firstMB = s.read('ue')
    
    if verbose:
        print('\nFrame    %d' %g_frameCnt)
        print('Slice')
        print('first_mb                                    %d' %firstMB)
        
    if firstMB==0:
        g_frameCnt+=1
    
    sliceType = s.read('ue')
    if verbose:
        if sliceType==0 or sliceType==5:
            print('slice type                                  P')
        elif sliceType==1 or sliceType==6:
            print('slice type                                  B')
        elif sliceType==2 or sliceType==7:
            print('slice type                                  I')
    if sliceType not in [0,1,2,5,6,7]:
        print('unsupported or corrupted slice type     %d' %sliceType)
        quit(1)
        
    pps_id = s.read('ue')
    assert( ppsInfo['pic_parameter_set_id']==pps_id)
    if verbose:
        print('pps_id                                      %d' %pps_id)
    
    pattern='uint:%d' %(spsInfo['log2_max_frame_num'])
    frameNum = s.read(pattern)
    if verbose:
        print('frame_num                                   %d' %frameNum)
    
    fldFlag=0
    if spsInfo['frame_mbs_only_flag']==0:
        fldFlag = s.read('uint:1')
        if verbose:
            print('field_flag                                  %d' %fldFlag)
        
        if fldFlag:
            bottomFld = s.read('uint:1')
            if verbose:
                print('bottom_field                                %d' %bottomFld)
    
    if nalType==5:  # IDR
        idrId = s.read('ue')
        if verbose:
            print('idr_idx                                     %d' %idrId)
    
    if spsInfo['pic_order_cnt_type']==0:
        pattern='uint:%d' %(spsInfo['log2_max_pic_order_cnt_lsb'])
        poc = s.read(pattern)
        if verbose:
            print('POC                                         %d' %poc)
            
        if ppsInfo['bottom_field_pic_order_in_frame_present_flag'] and fldFlag==0:
            deltaPoc = s.read('se')
            if verbose:
                print('delta_poc                                   %d' %deltaPoc)
    
    # pic_order_cnt_type=1 not supported
    
    if sliceType==1 or sliceType==6: # B slice
        directFlag = s.read('uint:1')
        
        
    num_ref_idx_l0 = ppsInfo['num_ref_idx_l0']
    if sliceType in [0,5,1,6]: # P or B 
        overrideFlag = s.read('uint:1')
        if verbose:
            print('override flag                               %d' %overrideFlag)
        
        if overrideFlag:
            num_ref_idx_l0 = s.read('ue')            
            num_ref_idx_l0+=1 # since actually num_ref_idx_l0_active_minus1 is coded
            if verbose:
                print('num_ref_idx_l0                              %d' %num_ref_idx_l0)
            if sliceType==1 or sliceType==6:
                num_ref_idx_l1 = s.read('ue')
                if verbose:
                    print('num_ref_idx_l1                              %d' %num_ref_idx_l1)
                
    # ref_pic_list_modification
    if sliceType in [0,5,1,6]: # P or B 
        ref_pic_list_modification_flag_l0 = s.read('uint:1')
        if verbose:
            print('ref_pic_list_modification_flag_l0           %d' %ref_pic_list_modification_flag_l0)
        if ref_pic_list_modification_flag_l0:
            modification_of_pic_nums_idc = 0
            while modification_of_pic_nums_idc!=3:
                modification_of_pic_nums_idc = s.read('ue')
                if modification_of_pic_nums_idc==0 or modification_of_pic_nums_idc==1:
                    abs_diff_pic_num = s.read('ue')
                elif modification_of_pic_nums_idc==2:
                    long_term_pic_num = s.read('ue')
            
        if sliceType==1 or sliceType==6: # B slice
            ref_pic_list_modification_flag_l1 = s.read('uint:1')
            if verbose:
                print('ref_pic_list_modification_flag_l1           %d' %ref_pic_list_modification_flag_l1)
            if ref_pic_list_modification_flag_l1:
                modification_of_pic_nums_idc = 0
                while modification_of_pic_nums_idc!=3:
                    modification_of_pic_nums_idc = s.read('ue')
                    if modification_of_pic_nums_idc==0 or modification_of_pic_nums_idc==1:
                        abs_diff_pic_num = s.read('ue')
                    elif modification_of_pic_nums_idc==2:
                        long_term_pic_num = s.read('ue')

    # end ref_pic_list_modification
    
    # explicit weighted prediction for B-slice is not supported
    if ppsInfo['weighted_pred_flag'] and sliceType in [0,5]: # explicit weights for P
        
        luma_log2_weight_denom = s.read('ue')
        if verbose:
            print('luma_log2_weight_denom                      %d' %luma_log2_weight_denom)
        
        chroma_log2_weight_denom = s.read('ue')
        if verbose:
            print('chroma_log2_weight_denom                    %d' %chroma_log2_weight_denom)
        for k in range(num_ref_idx_l0):
            luma_weight_l0_flag = s.read('uint:1')
            if verbose:
                print('luma_weight_l0_flag                         %d' %luma_weight_l0_flag)
            if luma_weight_l0_flag:
                luma_weight_l0 = s.read('se')
                if verbose:
                    print('luma_weight_l0                              %d' %luma_weight_l0)
                luma_offset_l0 = s.read('se')
                if verbose:
                    print('luma_offset_l0                              %d' %luma_offset_l0)
                
        chroma_weight_l0_flag = s.read('uint:1')
        if verbose:
            print('chroma_weight_l0_flag                       %d' %chroma_weight_l0_flag)
        
        if chroma_weight_l0_flag:
            # Cb
            chroma_weight_cb = s.read('se')
            if verbose:
                print('chroma_weight_cb                            %d' %chroma_weight_cb)
            chroma_offset_cb = s.read('se')
            if verbose:
                print('chroma_offset_cb                            %d' %chroma_offset_cb)
            chroma_weight_cr = s.read('se')
            if verbose:
                print('chroma_weight_cr                            %d' %chroma_weight_cr)
            chroma_offset_cr = s.read('se')
            if verbose:
                print('chroma_offset_cr                            %d' %chroma_offset_cr)

        
if __name__ == "__main__":

    filename, framesToProcess, verbose = parse_options()

    fp=open(filename,'rb')


    # get the input file size
    statinfo = os.stat(filename)
    fileSize=statinfo.st_size
    scp=re.compile('000001|00000001', re.IGNORECASE)
    buf=''
    sps=''
    pps=''
    slicehdr=''
    curOffs=0
    cnt =0 
    spsInfo={}
    ppsInfo={}
    while curOffs+4 < fileSize:
        
        if framesToProcess>0 and g_frameCnt>=framesToProcess:
            break
        # search for start code
        buf=fp.read(2048)
        curBufSize = len(buf)
        if curBufSize<4:
            break # eof
                
        c = bitstring.BitArray(bytes=buf, length=curBufSize*8) 
        hexbuf=c.hex
        startCodeFound=False
        for match in scp.finditer(hexbuf):
            idx=int(match.start())
            if (idx&1)==0:
                startCodeFound=True                
                scPos = int(idx/2)
                nalOffs = curOffs+scPos                
                curOffs=curOffs+scPos+3
                if buf[scPos+2]==0: # start code len = 4
                    curOffs+=1
                break  # start code found

        if startCodeFound==False:
            fp.seek(-3,1)
            curOffs=fp.tell()
            continue
            
        if curOffs>fileSize-3:
            break # eof
            
        fp.seek(curOffs,0)       
        nalHdr=struct.unpack("B", fp.read(1))[0]       
        nalType=nalHdr&0x1f  # to eliminate nal_ref_dic and forbidden_zero_bit
        if nalType==7: # SPS
            spsInfo={}
            oldOffs=fp.tell()+1
            sps=fp.read(200) # assumed the maximal size of SPS is 200 bytes
            if ParseSPS(sps, len(sps),spsInfo,verbose)==False:
                break
            fp.seek(oldOffs,0)
            curOffs=oldOffs
            continue
            
        if nalType==8: # PPS
            ppsInfo={}            
            oldOffs=fp.tell()+1
            pps=fp.read(200) # assumed the maximal size of PPS is 200 bytes
            if ParsePPS(pps, len(pps),ppsInfo,verbose)==False:
                break
            fp.seek(oldOffs,0)
            curOffs=oldOffs
            continue
        
        if nalType==1 or nalType==5:
            # slice header
            oldOffs=fp.tell()+1
            slicehdr=fp.read(200)
            ParseSliceHeader(slicehdr,len(slicehdr),spsInfo,ppsInfo,True)
            fp.seek(oldOffs,0)
            curOffs=oldOffs
            continue
            
        curOffs=fp.tell()

    fp.close()
    quit(0)
    

