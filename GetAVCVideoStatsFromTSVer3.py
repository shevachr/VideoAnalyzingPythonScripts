import sys
import os
import struct
import re
from optparse import OptionParser

"""
Copyright (c) 2017 Shevach Riabtsev, riabtsev@yahoo.com

Redistribution and use of source is permitted
provided that the above copyright notice and this paragraph are
duplicated in all such forms and that any documentation,
advertising materials, and other materials related to such
distribution and use acknowledge that the software was developed
by the Shevach Riabtsev, riabtsev@yahoo.com. The name of the
Shevach Riabtsev, riabtsev@yahoo.com may not be used to endorse or promote
products derived from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
"""
def print_progress(work_done_so_far, total_work):
    
    total_print_length = 80
    current_print_length = int((float(work_done_so_far) / float(total_work)) * float(total_print_length))
    
    display_string = "||"
    count = 0
    
    for count in range(0, current_print_length - 1):
        display_string = display_string + "="
    # End For
    
    display_string = display_string + ">"
    
    for count in range(current_print_length, total_print_length):
        display_string = display_string + " "
    # End For
    
    sys.stdout.write(display_string + "||\r")
    sys.stdout.flush()
    
    
def parse_options():

    parser = OptionParser()

    parser.add_option("-i",
                        dest = "tsfile",
                        help = "input h264 ts-file",
                        type = "string",
                        action = "store"
                        )
    parser.add_option("-v",
                        dest = "verbose",
                        help = "print pts, dts and sizes of each video frame (default false)",
                        action="store_true",
                        default=False)
    
    parser.add_option("-a",
                        dest = "ignoreAudError",
                        help = "ignore AUD absence which is required by Mpeg System (default false)",
                        action="store_true",
                        default=False)
                        
    parser.add_option("-p",
                        dest = "progress",
                        help = "print progress  (default false), disabled if verbose is ON",
                        action="store_true",
                        default=False)
                        
    (options, args) = parser.parse_args()
    if options.tsfile:
        return (options.tsfile,options.verbose,options.ignoreAudError,options.progress)
    parser.print_help()
    quit(-1)
    
def  GetVideoPid(fn):

    patFound=False
    pmtid = 13
    eof = False
    vpid = 0
    pktPos = 0
    
    with open(fn, "rb") as f:
    
        while True:  # pkt loop to find PSI
            b = f.read(1)
            if not b:
                eof = True
                break  # eof
            
            syncByte=struct.unpack("B", b)[0]
            if syncByte!=0x47:
                print('Error: not sync found at 0x%x' %pktPos)
                return (0,False)
              
            bb=f.read(2)
            if not bb:
                eof = True
                break  # eof
            
            val=struct.unpack("!H", bb)[0]
            
            # extract pid
            payloadStart=(val&0x4000)>>14 # payload_unit_start_indicator
            pid=val&0x1FFF
                
            if  pid==0 and payloadStart:  # PAT, payload_start=1 indicates that this is the start of PAT

                val=struct.unpack("B", f.read(1))[0]
                adaptCtrl=(val&0x30)>>4
                if adaptCtrl==0:
                    print('adaptation ctrl illegal, found at PAT. position 0x%x' %pktPos)
                    return (0,False)
                    
                if adaptCtrl==2:
                    print('no payload, found at PAT, position 0x%x' %pktPos)
                    return (0,False)
                    
                if adaptCtrl==3:
                    adaptLen=struct.unpack("B", f.read(1))[0]
                    if adaptLen>183:
                        print('Adaptation header in PMT exceeds ts-packet, position 0x%x' %pktPos)
                        return (0,False)
                    f.seek(adaptLen,1) 
                ptrfld = struct.unpack("B", f.read(1))[0]
                if ptrfld:
                    f.seek(ptrfld,1)
                
                tblid = struct.unpack("B", f.read(1))[0]  # table_id
                if tblid!=0:
                    print('Illegal PAT table_id, position  0x%x' %pktPos)
                    return (0,False)
                
                val=struct.unpack("!H", f.read(2))[0]
                sectLen = val&0xfff
                if sectLen<10:
                    print('Illegal PAT, position  0x%x' %pktPos)
                    return (0,False)
                
                sectLen-=9  # count CRC32, transport_id, version ...
                f.seek(5,1)
                
                #print 'Pat section length  %d, pos %ld' %(sectLen,f.tell())
                while True:
                    if sectLen<=0:
                        break
                    
                    progNum = struct.unpack("!H", f.read(2))[0]    
                    val = struct.unpack("!H", f.read(2))[0]
                    pmtid=val&0x1fff
    
                    sectLen-=4
                    if progNum:
                        break
                
                patFound=True

            elif  pid==pmtid and patFound==True and payloadStart:
                
                val=struct.unpack("B", f.read(1))[0]
                adaptCtrl=(val&0x30)>>4
                if adaptCtrl==0:
                    print('adaptation ctrl illegal, found at PMT, pos  0x%x' %pktPos)
                    return (0,False)
                    
                if adaptCtrl==2:
                    print('no payload, found at PMT, pos 0x%x' %pktPos)
                    return (0,False)
                    
                if adaptCtrl==3:
                    adaptLen=struct.unpack("B", f.read(1))[0]
                    if adaptLen>183:
                        print('Adaptation header in PMT exceeds ts-packet, pos  0x%x' %pktPos)
                        return (0,False)
                    f.seek(adaptLen,1)              
                ptrfld = struct.unpack("B", f.read(1))[0]
                if ptrfld:
                    f.seek(ptrfld,1)
                
                tblid = struct.unpack("B", f.read(1))[0]  # table_id
                if tblid!=2:
                    print('Illegal PMT table_id, position 0x%x' %pktPos)
                    return (0,False)
                
                val=struct.unpack("!H", f.read(2))[0]
                sectLen = val&0xfff
                sectLen-=4  # crc32
                
                val=struct.unpack("!H", f.read(2))[0]
                sectLen-=2
                
                f.seek(3,1)   # skip over version, section_num and etc.         
                sectLen-=3
                
                val=struct.unpack("!H", f.read(2))[0]
                pcrpid = val&0x1fff
                sectLen-=2
                
                val = struct.unpack("!H", f.read(2))[0] # program_info_length
                sectLen-=2
                progLen = val &0xfff
                sectLen-=progLen
            
                if sectLen<0:
                    print('Illegal PMT table_id, pos  0x%x' %pktPos)
                    return (0,False)
                    
                # ******** read out-loop descriptors *********
                while True:
                    if progLen<2:
                        break
                    # read new descriptor
                    descrTag = struct.unpack("B", f.read(1))[0]
                    descrLen = struct.unpack("B", f.read(1))[0]
                    progLen-=2
                    if progLen==0:
                        break
             
                    f.seek(descrLen,1)
                    progLen-=descrLen
                # ******** End out-loop descriptors *********
                
                while True:
                    if sectLen<5:
                        return (0,False)
                        
                    streamType = struct.unpack("B", f.read(1))[0]
                    streamPid  = struct.unpack("!H", f.read(2))[0]
                    streamPid = streamPid&0x1fff
                    if streamType==0x1b:
                        vpid = streamPid
                        f.close()
                        return (vpid,True)
                    if streamType==0x24 or streamType==0x25:
                        vpid = streamPid
                        f.close()
                        return (vpid,False)  # HEVC
                    infoLen  = struct.unpack("!H", f.read(2))[0]
                    infoLen = infoLen &0xfff
                    sectLen-=infoLen
                    if infoLen:
                        #   ****  in-loop descriptors ********
                        while True:
                            if infoLen<2:
                                break
                            # read new descriptor
                            descrTag = struct.unpack("B", f.read(1))[0]
                            descrLen = struct.unpack("B", f.read(1))[0]
                            infoLen-=2
                            if infoLen==0:
                                break
                            
                            f.seek(descrLen,1)
                            infoLen-=descrLen
                        
                        # ****  in-loop descriptors ********
                    
                    sectLen-=5
                
                f.seek(pos,0)
                return (0,False)

            pktPos+=188
            f.seek(pktPos,0)
            
        
        f.close()
        return (0,False)


def ReadPesHeader(f):
   
    sc=struct.unpack("!I", f.read(4))[0]
    pesPktLen = struct.unpack("!H", f.read(2))[0] # PES_packet_length
    f.seek(1,1) # skip over flags
    peshdrSize=7  # minimal pes header size
    streamId = sc&0xF0
    if streamId!=0xE0:  # not video
        return (0,0,False,0,0,streamId)
                
    # read pts_dts flag
    val=struct.unpack("B", f.read(1))[0]
    ptsdts = val>>6
    peshdrLen = struct.unpack("B", f.read(1))[0] # PES_header_data_length
    peshdrSize+=2
    peshdrSize+=peshdrLen
    pts = 0
    dts = 0
    ptsFlag = False
    
    if ptsdts==2:
    
        ptsFlag = True
        msb = struct.unpack("B", f.read(1))[0]
        lsb = struct.unpack("!I", f.read(4))[0]
        pts = (lsb & 0xffff)>>1
        pts = pts |((lsb>>17)<<15)
        pts = pts |((( msb&0xE )>>1)<<30)
        dts = pts
        peshdrLen -= 5
        
    elif ptsdts==3:
    
        ptsFlag = True
        msb = struct.unpack("B", f.read(1))[0]
        lsb = struct.unpack("!I", f.read(4))[0]
        pts = (lsb & 0xffff)>>1
        pts = pts |((lsb>>17)<<15)
        pts = pts |((( msb&0xE )>>1)<<30)
        
        msb = struct.unpack("B", f.read(1))[0]
        lsb = struct.unpack("!I", f.read(4))[0]
        dts = (lsb & 0xffff)>>1
        dts = dts |((lsb>>17)<<15)
        dts = dts |((( msb&0xE )>>1)<<30)
        peshdrLen -= 10
        
    f.seek(peshdrLen,1)
    
    return (peshdrSize, pesPktLen, ptsFlag, pts, dts, streamId )

if __name__ == "__main__":

    tsfile,verbose,ignoreAudError,progress = parse_options()
    
    vpid,avc = GetVideoPid(tsfile)
    if vpid==0:
        print('video pid not found')
        print('\n')
        quit(-1)
        
    vpkt=0
    pkt=0
    liDts=[]
    liPts=[] 
    liAus=[] # list of AU sizes
    videoFrames=0
    videoLen=0
    auSize = 0
    frameNum=0
    ptsdtsError=False
    pktPos=0
    statinfo = os.stat(tsfile)
    fileSize=statinfo.st_size

    with open(tsfile, "rb") as f:
        
        while True:
            if progress and pkt%5300==0: # ~ 1Mb read off, update progress bar
                print_progress(pktPos, fileSize)
            
            peshdr = 0
            b = f.read(1)
            if not b: break  # eof
            
            syncByte=struct.unpack("B", b)[0]
            if syncByte!=0x47:
                print('not sync found at 0x%x,  pkt  %d' %(pktPos,pkt))
                break
                
            bb=f.read(2)
            if not bb: break  # eof
            
            val=struct.unpack("!H", bb)[0]
            
            # extract pid
            payloadStart=(val&0x4000)>>14 # payload_unit_start_indicator
            pid=val&0x1FFF
            tshdr=3 # minimal length of ts-header
            
            if pid==vpid: # video
                val=struct.unpack("B", f.read(1))[0]
                tshdr+=1
                adaptCtrl=(val&0x30)>>4
                if adaptCtrl==0:
                    print('adaptation ctrl illegal, found at packet %d,  pos 0x%x' %(pkt,pktPos))
                    print('\n')
                    quit(-1)
                    
                if adaptCtrl==1: # no adaptation payload only
                    
                    if payloadStart:  # pes header is present
                        peshdr, pesPktLen, ptsFlag, pts, dts, streamId = ReadPesHeader(f)
                        if peshdr==0:
                            print('No h264 video stream_id  %x, found at packet %d,  pos 0x%x' %(streamId,pkt,pktPos))
                            print('\n')
                            quit(-1)
                        if pts<dts:
                            print('PTS (%d) is smaller than DTS (%d), found at ts-pkt %d, pos 0x%x' %(pts,dts,pkt, pktPos))
                            ptsdtsError=True
                            if verbose==False:
                                print('\n')
                                quit(1)
                        if peshdr>184:
                            print('Pes header exceeding ts-packet size (not supported yet), found at packet %d,  pos 0x%x' %(streamId,pkt,pktPos))
                            print('\n')
                            quit(-1)
                            
                        if ptsFlag:
                            videoFrames+=1
                            videoLen+=auSize
                            if verbose:
                                liAus.append(auSize)
                                liPts.append(pts)
                                liDts.append(dts)
                            auSize = 184 - peshdr
                            
                            # check AUD, new frame since PTS present
                            # the spec. says: if a PTS is present in the PES packet header, it shall refer to the first AVC access unit 
                            # that commences in this PES packet
                            if 184-peshdr<5:
                                print('AUD crosses ts-boundary (not supported yet), found at packet %d,  pos 0x%x' %(pkt,pktPos)) 
                                print('\n')
                                quit(-1)
                                
                            sc=struct.unpack("!I", f.read(4))[0]
                            sc3 = sc>>8 # check that start code is 0x000001
                            if sc==0x1: # start code 00 00 00 01
                                # read more byte to specify NAL type
                                nalType = struct.unpack("B", f.read(1))[0]
                                if avc:
                                    nalType = nalType&0x1f
                                    if nalType!=9 and ignoreAudError==False: # AUD not found
                                        print('AUD is absent at start of frame %d, nalType %d, found at pkt %d, pos  0x%x' %(frameNum,nalType,pkt,pktPos))
                                        print('\n')
                                        quit(2)
                                else: # HEVC
                                    nalType=nalType>>1
                                    nalType = nalType&0x3f
                                    if nalType!=35 and ignoreAudError==False: # HEVC AUD not found
                                        print('AUD is absent at start of frame %d, nalType %d, found at pkt %d, pos  0x%x' %(frameNum,nalType,pkt,pktPos))
                                        print('\n')
                                        quit(2)
                            elif sc3==0x1: # start code 00 00 01
                                if avc:
                                    nalType=sc&0x1f
                                    if nalType!=9 and ignoreAudError==False:
                                        print('AUD is absent at start of frame %d, nalType %d, found at pkt %d, pos  0x%x' %(frameNum,nalType,pkt,pktPos))
                                        print('\n')
                                        quit(2)
                                else: # HEVC
                                    nalType=sc&0xff
                                    nalType=nalType>>1
                                    nalType = nalType&0x3f
                                    if nalType!=35 and ignoreAudError==False: # HEVC AUD not found
                                        print('AUD is absent at start of frame %d, nalType %d, found at pkt %d, pos  0x%x' %(frameNum,nalType,pkt,pktPos))
                                        print('\n')
                                        quit(2)
                            else:
                                print('PTS present but no start code (frame %d) sensed, found at packet %d,  pos  0x%x' %(frameNum,pkt,pktPos))
                                print('\n')
                                quit(2)
                            frameNum+=1
                        else:  # no PTS
                            sc=struct.unpack("!I", f.read(4))[0]
                            sc3 = sc>>8 # check that start code is 0x000001
                            # check missing PTS/DTS
                            if sc==0x1: # start code 00 00 00 01
                                # read more byte to specify NAL type
                                nalType = struct.unpack("B", f.read(1))[0]
                                if avc:
                                    nalType = nalType&0x1f
                                    if nalType==9: # AUD found but no PTS present
                                        print('AUD is present (frame %d) but PTS not, found at pkt %d, pos  0x%x' %(frameNum,pkt,pktPos))
                                        print('\n')
                                        quit(2)
                                else: # HEVC
                                    nalType=nalType>>1
                                    nalType = nalType&0x3f
                                    if nalType!=35: # HEVC AUD not found
                                        print('AUD is present (frame %d) but PTS not, found at pkt %d, pos  0x%x' %(frameNum,pkt,pktPos))
                                        print('\n')
                                    quit(2)
                            elif s3==0x1:
                                if avc:
                                    nalType=sc&0x1f
                                    if nalType!=9:
                                        print('AUD is present (frame %d) but PTS not, found at pkt %d, pos  0x%x' %(frameNum,pkt,pktPos))
                                        print('\n')
                                        quit(2)
                                else: # HEVC
                                    nalType=sc&0xff
                                    nalType=nalType>>1
                                    nalType = nalType&0x3f
                                    if nalType!=35: # HEVC AUD not found
                                        print('AUD is present (frame %d) but PTS not, found at pkt %d, pos  0x%x' %(frameNum,pkt,pktPos))
                                        print('\n')
                                        quit(2)
                            
                            auSize = auSize + (184 - peshdr)
                    else:
                        auSize += 184
                    vpkt+=1
                    pkt+=1
                    pktPos+=188
                    f.seek(pktPos,0)
                    continue
                    
                if adaptCtrl==2:
                    payload=0
                    
                # adaptation + payload?
                adaptLen=struct.unpack("B", f.read(1))[0]
                tshdr+=1
                payload=184-adaptLen-1
                if payload<0:
                    print('adaptation header too long, found at packet %d,  pos  0x%x' %(pkt,pktPos))
                    print('\n')
                    quit(-1)
                
                pesPos = f.tell()+adaptLen
                tshdr+=adaptLen
                if tshdr>188:
                    print('ts header is too long, found at packet %d,  pos  0x%x' %(pkt,pktPos))
                    print('\n')
                    quit(-1)
                    
                vpkt+=1
                
                # process pes header
                if payloadStart:
                    f.seek(pesPos,0)
                    peshdr, pesPktLen, ptsFlag, pts, dts, streamId = ReadPesHeader(f)
                    if peshdr==0:
                        print('No h264 video stream_id  0x%x, found at packet %d,  pos  0x%x' %(streamId,pkt,pktPos))
                        print('\n')
                        quit(-1)
                    if pts<dts:
                        print('PTS (%d) is smaller than DTS (%d), found at ts-pkt %d, pos  0x%x' %(pts,dts,pkt, pktPos))
                        ptsdtsError=True
                        if verbose==False:
                            print('\n')
                            quit(1)
                    if ptsFlag:
                        # assumed: presense of pts means start of access unit
                        videoLen+=auSize
                        videoFrames+=1
                        if verbose:
                            liAus.append(auSize)
                            liPts.append(pts)
                            liDts.append(dts)
                        auSize = 188 - tshdr - peshdr
                        
                        # the spec. says: if a PTS is present in the PES packet header, it shall refer to the first AVC access unit 
                        # that commences in this PES packet
                        if 184-peshdr-tshdr<5:
                            print('AUD crosses ts-boundary (not supported yet), found at packet %d,  pos  0x%x' %(pkt,pktPos)) 
                            print('\n')
                            quit(-1)
                            
                        sc=struct.unpack("!I", f.read(4))[0]
                        sc3 = sc>>8 # check that start code is 0x000001
                        if sc==0x1: # start code 00 00 00 01
                            # read more byte to specify NAL type
                            nalType = struct.unpack("B", f.read(1))[0]
                            if avc:
                                nalType = nalType&0x1f
                                if nalType!=9 and ignoreAudError==False: # AUD not found
                                    print('AUD is absent at start of frame %d, nalType %d, found at pkt %d, pos  0x%x' %(frameNum,nalType,pkt,pktPos))
                                    print('\n')
                                    quit(2)
                            else: # HEVC
                                nalType=nalType>>1
                                nalType = nalType&0x3f
                                if nalType!=35 and ignoreAudError==False: # HEVC AUD not found
                                    print('AUD is absent at start of frame %d, nalType %d, found at pkt %d, pos  0x%x' %(frameNum,nalType,pkt,pktPos))
                                    print('\n')
                                    quit(2)
                        elif sc3==0x1: # start code 00 00 01
                            if avc:
                                nalType=sc&0x1f
                                if nalType!=9 and ignoreAudError==False:
                                    print('AUD is absent at start of frame %d, nalType %d, found at pkt %d, pos  0x%x' %(frameNum,nalType,pkt,pktPos))
                                    print('\n')
                                    quit(2)
                            else: # HEVC
                                nalType=sc&0xff
                                nalType=nalType>>1
                                nalType = nalType&0x3f
                                if nalType!=35 and ignoreAudError==False: # HEVC AUD not found
                                    print('AUD is absent at start of frame %d, nalType %d, found at pkt %d, pos  0x%x' %(frameNum,nalType,pkt,pktPos))
                                    print('\n')
                                    quit(2)
                        else:
                            print('PTS present but no start code (frame %d) sensed, found at packet %d,  pos  0x%x' %(frameNum,pkt,pktPos))
                            print('\n')
                            quit(2)
                        frameNum+=1
                        
                    else: # no PTS
                        sc=struct.unpack("!I", f.read(4))[0]
                        sc3 = sc>>8 # check that start code is 0x000001
                        # check missing PTS/DTS
                        if sc==0x1: # start code 00 00 00 01
                            # read more byte to specify NAL type
                            nalType = struct.unpack("B", f.read(1))[0]
                            if avc:
                                nalType = nalType&0x1f
                                if nalType==9: # AUD found but no PTS present
                                    print('AUD is present (frame %d) but PTS not, found at pkt %d, pos  0x%x' %(frameNum,pkt,pktPos))
                                    print('\n')
                                    quit(2)
                            else: # HEVC
                                nalType=nalType>>1
                                nalType = nalType&0x3f
                                if nalType!=35: # HEVC AUD not found
                                    print('AUD is present (frame %d) but PTS not, found at pkt %d, pos  0x%x' %(frameNum,pkt,pktPos))
                                    print('\n')
                                quit(2)
                        elif s3==0x1:
                            if avc:
                                nalType=sc&0x1f
                                if nalType!=9:
                                    print('AUD is present (frame %d) but PTS not, found at pkt %d, pos  0x%x' %(frameNum,pkt,pktPos))
                                    print('\n')
                                    quit(2)
                            else: # HEVC
                                nalType=sc&0xff
                                nalType=nalType>>1
                                nalType = nalType&0x3f
                                if nalType!=35: # HEVC AUD not found
                                    print('AUD is present (frame %d) but PTS not, found at pkt %d, pos  0x%x' %(frameNum,pkt,pktPos))
                                    print('\n')
                                    quit(2)
                        auSize = auSize + (188 - tshdr - peshdr)
                else:
                    auSize = auSize + (188 - tshdr)
                    
            #sys.stderr.write('Packet Count %20d\r' %pkt)    
            pkt+=1
            if peshdr+tshdr>188:
                print('pes header is too long, found at packet %d,  pos  0x%x' %(pkt,pktPos))
                print('\n')
                quit(-1)
                
            pktPos+=188
            f.seek(pktPos,0)
            
            
        if verbose:
            liAus.append(auSize)
            k = 0
            prevDTS = 0
            for auSize, dts, pts in zip(liAus[1:],liDts,liPts):
                if k==0:
                    print('%d   Size  %d, dts  %d,   pts  %d' %(k,auSize,dts,pts))
                else:
                    delta = ((dts - prevDTS)/90000.0)*1000.0
                    print('%d   Size  %d, dts  %d,   pts  %d, frame duration %.2f' %(k,auSize,dts,pts,delta))
                prevDTS = dts    
                k+=1

            diffDTS = [x1 - x2 for (x1, x2) in zip(liDts[1:], liDts[:-1])]
            maxDTS = max(diffDTS)
            maxIdx = diffDTS.index(maxDTS) 
            minDTS = min(diffDTS)
            minIdx = diffDTS.index(minDTS) 
            diffPTS = [ x1 - x2 for (x1, x2) in zip(liPts[1:], liPts[:-1]) if x1-x2>0]
            minPTS = min(diffPTS)
            minPtsIdx = diffPTS.index(minPTS)
            print('\n')
            print('Minimal DTS diff (in ms)  %.2f, attained at frame %d' %((minDTS/90000.0)*1000.0,minIdx))
            print('Minimal PTS diff (in ms)  %.2f, attained at frame %d' %((minPTS/90000.0)*1000.0,minPtsIdx))
            print('Maximal DTS diff (in ms)  %.2f, attained at frame %d' %((maxDTS/90000.0)*1000.0, maxIdx))
        print('\n')
        
        print('Number of Frames        %d' %videoFrames)
        print
        if ptsdtsError:
            quit(1)
        quit(0)
        
