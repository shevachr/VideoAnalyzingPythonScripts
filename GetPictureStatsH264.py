import sys
import os
import re
import struct
import bitstring
from optparse import OptionParser

"""
Copyright (c) 2019 Shevach Riabtsev, riabtsev@yahoo.com

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

def parse_options():
    parser = OptionParser(usage="%prog [-i] [-n] [-v] [-p]", version="%prog 1.1")

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
                        help = "verbose mode  (default false)",
                        action="store_true",
                        default=False)
                        
 
    (options, args) = parser.parse_args()
    
    if options.framesToProcess<0:
        parser.print_help()
        quit(-1)
        
    if options.filename:
        if os.path.isfile(options.filename)==False:
            print('Input file not exist or directory')
            parser.print_help()
            quit(-1)
        
        return (options.filename, options.framesToProcess, options.verbose) 
        
    parser.print_help()
    quit(-1)
        
if __name__ == "__main__":
# gather picture statistics: picture offset and type

    filename, numFrames, verbose = parse_options()
    
    if verbose:
        progress=False
    
    fp=open(filename,'rb')

    # get the input file size
    statinfo = os.stat(filename)
    fileSize=statinfo.st_size

    scp=re.compile('000001|00000001', re.IGNORECASE)
    frameCnt=0
    curOffs=0
    nalOffs = 0
    frameStart=0
    prevFrameOffs=0
    newFrame=False
    liOffs=[]
    liType=[]
    liSize=[]
    buf=''
    
    while curOffs+4 < fileSize:
    
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
                scPos = idx>>1
                nalOffs = curOffs+scPos
                #if scPos==0 and curOffs>0:
                #    fp.seek(curOffs-1,0)
                #    ch=fp.read(1)
                #    if ord(ch)==0:
                #        # start code =4 
                #        nalOffs -= 1
                #elif scPos>0:
                #    if ord(buf[scPos-1])==0:
                        # start code =4 
                #        nalOffs -= 1
                
                curOffs=curOffs+scPos+3
                if buf[scPos+2]==0: # start code len = 4
                    curOffs+=1
                # determine NAL start
                #print '%d  %d  %x' %(idx,idx/2,curOffs)
                break

        if startCodeFound==False:
            fp.seek(-3,1)
            curOffs=fp.tell()
            continue
            
        if curOffs>fileSize-3:
            break # eof
            
        fp.seek(curOffs,0)
        buf=fp.read(2)           
        nalHdr=struct.unpack("!H", buf)[0]
        nalType=nalHdr>>8
        nalType=nalType&0x1f  # to eliminate nal_ref_dic and forbidden_zero_bit
        #print '%x %d %x' %(nalHdr,nalType,curOffs)
        
        if nalType==9:  # AUD
            frameStart=nalOffs
            frameCnt+=1
            if verbose:
                sys.stderr.write('Frame %10d\r' %frameCnt) 
            newFrame=True
 
        elif nalType==7 and newFrame==False: # NAL_UNIT_SPS
            frameStart=nalOffs
            frameCnt+=1
            if verbose:
                sys.stderr.write('Frame %10d\r' %frameCnt) 
            newFrame=True


        elif nalType==8 and newFrame==False: # NAL_UNIT_PPS
            frameStart=nalOffs
            frameCnt+=1
            if verbose:
                sys.stderr.write('Frame %10d\r' %frameCnt) 
            newFrame=True

        elif nalType==6 and newFrame==False: # SEI
            frameStart=nalOffs
            frameCnt+=1
            if verbose:
                sys.stderr.write('Frame %10d\r' %frameCnt) 
            newFrame=True

        elif (nalType==1 or nalType==5) and newFrame==False: # frame
            # check that the first slice first_mb_in_slice=0
            firstMb=(nalHdr>>7)&1
            if firstMb==1:
                frameStart=nalOffs
                frameCnt+=1
                if verbose:
                    sys.stderr.write('Frame %10d\r' %frameCnt) 
                newFrame=True

        if (nalType==1 or nalType==5) and newFrame==True:
            firstMb=(nalHdr>>7)&1
            newFrame=False
            if firstMb==1 and nalType==1:
                liOffs.append(frameStart)
                liType.append('pb')
                frameSize=frameStart-prevFrameOffs
                liSize.append(frameSize)
                prevFrameOffs=frameStart
                
            if firstMb==1 and nalType==5:
                liOffs.append(frameStart)
                liType.append('idr')
                frameSize=frameStart-prevFrameOffs
                liSize.append(frameSize)
                prevFrameOffs=frameStart
                
        if numFrames!=0 and frameCnt>=numFrames:
            break
            
        curOffs=fp.tell()


    # remove the first element in liSize
    liSize.pop(0)
    # add size of the last frame
    liSize.append(fileSize-frameStart)
    # print list and get stats
    for frameType, frameStart, frameSize in zip(liType, liOffs, liSize):
        #print frameType, frameStart
        print("%s    %x    %x" %(frameType, frameStart, frameSize))
    #print '\nIDR frames  %d' %(liType.count('idr')) 
    fp.close()
    

