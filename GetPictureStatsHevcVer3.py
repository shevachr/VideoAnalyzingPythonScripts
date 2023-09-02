import sys
import os
import struct
import bitstring
from optparse import OptionParser

"""
Copyright (c) 2018 Shevach Riabtsev, riabtsev@yahoo.com

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
    parser = OptionParser(usage="%prog [-i] [-n]", version="%prog 1.0")

    parser.add_option("-i",
                        dest = "hevcfile",
                        help = "input hevc file",
                        type = "string",
                        action = "store"
                        )
                        
    parser.add_option( "-n",
                        dest = "nframes",
                        help = "number of frames to process, if 0 then all, (default 0)",
                        type = "int",
                        action = "store",
                        default = 0
                        )   
    (options, args) = parser.parse_args()
    
        
    if options.hevcfile:
        return (options.hevcfile, options.nframes) 

    parser.print_help()
    quit(-1)
    
    # *************************************************
    
def FindStartCode(fp):
        """
        Look for Start code 00 00 01 
        """
        while True:
            curOffs=fp.tell()
            buf=fp.read(512)
            curBufSize = len(buf)
            if curBufSize<6:
                return False # eof
        
            c = bitstring.BitArray(bytes=buf, length=curBufSize*8) 
            hexbuf=c.hex
            
            idx=hexbuf.find('000001')
            if idx>0 and (idx&1)==1:
                fp.seek(curOffs+(idx>>1)+2,0)
                continue
                
            if idx>=0:
                fp.seek(curOffs+(idx>>1)+3,0) # point to nal header
                return True
            
            fp.seek(-4,1)
            
        return False  # non-reachable


if __name__ == "__main__":
# gather picture statistics: picture offset and type

    filename,maxframes = parse_options()
    
    fp=open(filename,'rb')
   
    # get the input file size
    statinfo = os.stat(filename)
    fileSize=statinfo.st_size

    curOffs=0
    frameStart=0
    startCode=struct.pack("!I",1) # 00 00 00 01
    newFrame=False
    prevFrameOffs=0
    liOffs=[]
    liType=[]
    liSize=[]
    frameCnt=0
    print('gathering statistics ...')
    print('\n')
    while curOffs+4 < fileSize:
        if FindStartCode(fp)==False:
            break  # eof 
        # StartCode found
        curOffs=fp.tell()
        if curOffs>3:
            fp.seek(-4,1) # rewind
            c=fp.read(1)
            if ord(c)==0:  # four-byte start code
                curOffs=curOffs-4
            else:
                curOffs=curOffs-3
            fp.seek(3,1) # go back
        else:
            curOffs=0
            
        nalHdr=struct.unpack("!I", fp.read(4))[0]
        nalType=nalHdr>>25

        if nalType==35:  # AUD
            frameStart=curOffs
            newFrame=True
            #sys.stdout.write('Frame Count %12d\r' %frameCnt)
            #sys.stdout.flush()
            frameCnt+=1
        elif nalType==32 and newFrame==False: # NAL_UNIT_VPS
            frameStart=curOffs
            newFrame=True
            #sys.stdout.write('Frame Count %12d\r' %frameCnt)
            #sys.stdout.flush()
            frameCnt+=1
        elif nalType==33 and newFrame==False: # NAL_UNIT_SPS
            frameStart=curOffs
            newFrame=True
            #sys.stdout.write('Frame Count %12d\r' %frameCnt)
            #sys.stdout.flush()
            frameCnt+=1
        elif nalType==34 and newFrame==False: # NAL_UNIT_PPS
            frameStart=curOffs
            newFrame=True
            #sys.stdout.write('Frame Count %12d\r' %frameCnt)
            #sys.stdout.flush()
            frameCnt+=1
        elif (nalType==39 or nalType==40) and newFrame==False: # SEI
            frameStart=curOffs
            newFrame=True
            #sys.stdout.write('Frame Count %12d\r' %frameCnt)
            #sys.stdout.flush()
            frameCnt+=1
        elif (nalType==0 or nalType==1 or nalType==6 or nalType==7 or nalType==8 or nalType==9) and newFrame==False: # frame
            if (nalHdr & 0x8000)!=0: # first_slice_segment_in_pic_flag=1
                newFrame=True
                frameStart=curOffs
                #sys.stdout.write('Frame Count %12d\r' %frameCnt)
                #sys.stdout.flush()
                frameCnt+=1
        elif nalType>=16 and nalType<=21 and newFrame==False:
            if (nalHdr & 0x8000)!=0: # first_slice_segment_in_pic_flag=1
                newFrame=True
                frameStart=curOffs
                #sys.stdout.write('Frame Count %12d\r' %frameCnt)
                #sys.stdout.flush()
                frameCnt+=1
                
        if maxframes>0 and frameCnt>maxframes:
            break
            
        if (nalType==19 or nalType==20) and newFrame==True:
            liType.append('idr ')
            liOffs.append(frameStart)
            frameSize=frameStart-prevFrameOffs
            liSize.append(frameSize)
            prevFrameOffs=frameStart
            newFrame=False
        elif nalType==21 and newFrame==True:
            liType.append('cra ')
            liOffs.append(frameStart)
            frameSize=frameStart-prevFrameOffs
            liSize.append(frameSize)
            newFrame=False
            prevFrameOffs = frameStart
        elif (nalType==16 or nalType==17 or nalType==18) and newFrame==True:
            liType.append('bla ')
            liOffs.append(frameStart)
            frameSize=frameStart-prevFrameOffs
            liSize.append(frameSize)
            newFrame=False
            prevFrameOffs = frameStart
        elif (nalType==0 or nalType==1) and newFrame==True:
            liType.append('pb  ')
            liOffs.append(frameStart)
            frameSize=frameStart-prevFrameOffs
            liSize.append(frameSize)
            newFrame=False
            prevFrameOffs = frameStart
        elif (nalType==6 or nalType==7) and newFrame==True:
            liType.append('radl')
            liOffs.append(frameStart)
            frameSize=frameStart-prevFrameOffs
            liSize.append(frameSize)
            newFrame=False
            prevFrameOffs = frameStart
        elif (nalType==8 or nalType==9) and newFrame==True:
            liType.append('rasl')
            liOffs.append(frameStart)
            frameSize=frameStart-prevFrameOffs
            liSize.append(frameSize)
            newFrame=False
            prevFrameOffs = frameStart
    # remove the first element in liSize
    liSize.pop(0)
    # add size of the last frame
    if maxframes==0:
        liSize.append(fileSize-frameStart)
    else:
        liSize.append(0)
    # print list and get stats
    for frameType, frameStart, frameSize in zip(liType, liOffs, liSize):
        #print frameType, frameStart
        print("%4s    %20x    %10x" %(frameType, frameStart, frameSize))
    fp.close()
    

