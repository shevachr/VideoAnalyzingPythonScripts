import sys
import os
import struct

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

def FindStartCode(fp):
    """
    not optimal function
    traverse stream to find the start code 00 00 01 or 00 00 00 01
    if the whole stream checked and no start code found returns False
    """
    scState=1
    while True:
        c=fp.read(1)
        if c == '':
            break  # eof

        if ord(c)==0 and scState==1:
            scState=2
        elif ord(c)==0 and scState==2:
            scState=3
        elif ord(c)!=0 and scState==2:
            scState=1
        elif ord(c)!=0 and ord(c)!=1 and scState==3:
            scState=1
        elif ord(c)==1 and scState==3:
            # start code found
            return True
    return False

def CopyFile(inf,outf,size,chunkSize):
    """
    Copy data of the size 'size' by chunks of the length 'chunkSize' (optimization)
    """
    if size<chunkSize:
        buf=inf.read(size)
        outf.write(buf)
        return
    # copy chain
    while size>=chunkSize:
        buf=inf.read(chunkSize)
        outf.write(buf)
        size=size-chunkSize

    if size>0:
        buf=inf.read(size)
        outf.write(buf)

    return

def printProgressBar(processedLen, totalLen):

    curLength = int((float(processedLen) / float(totalLen)) * 80.0) # 80 is the progress bar size
    displayStr = "||"

    
    if curLength>80: # potential rounding-errors can make curLength to be 81
        curLength=80
        
    for _ in range(0, curLength-1):
        displayStr = displayStr + "="

    displayStr = displayStr + ">"
    
    for _ in range(curLength, 80):
        displayStr = displayStr + " "
        
    sys.stdout.write(displayStr + "||\r")
    sys.stdout.flush()

    
    
if __name__ == "__main__":
# Remove specified SEI messages from H264 elementary stream, not in-place operation

    if len(sys.argv) < 4:
        print 'Usage: in.h264 <sei-type> out.h264'
        quit(0)
    
    fp=open(sys.argv[1],'rb')
    sei = int(sys.argv[2])
    
    # get the input file size
    statinfo = os.stat(sys.argv[1])
    fileSize=statinfo.st_size
    print 'Analyzing ...'

    curOffs=0
    prevOffs=0
    liOffs=[]
    liType=[]
    liSize=[]
    seiRem = 0
    progressBarUpdateFreq = 150 # each 150 NALs the progress bar is updated
    scCnt = 0
    printProgressBar(0,fileSize)
    
    while curOffs+4 < fileSize:

        if FindStartCode(fp)==False:
            break  # eof

        # StartCode found
        curOffs=fp.tell()
        scCnt+=1
        if curOffs>3:
            fp.seek(-4,1) # rewind
            c=fp.read(1)
            if len(c)==0:
                break  # eof
                
            if ord(c)==0:  # four-byte start code
                curOffs=curOffs-4
            else:
                curOffs=curOffs-3
            fp.seek(3,1) # go back
        else:
            curOffs=0

        sz = curOffs-prevOffs
        prevOffs=curOffs
        
        buf1=fp.read(1)
        if len(buf1)==0:
            break   # eof
        
        buf2=fp.read(1)
        if len(buf2)==0:
            break   # eof
            
        liOffs.append(curOffs)
        liSize.append(sz)

        nalHdr=struct.unpack("B", buf1)[0]
        payloadByte=struct.unpack("B", buf2)[0]
        nalType=nalHdr&0x1f # to eliminate nal_ref_dic and forbidden_zero_bit

        if nalType==6 and payloadByte==sei: # SEI
            liType.append(1)
            seiRem+=1
        else:
            liType.append(0)
            
        if scCnt>=progressBarUpdateFreq:
            printProgressBar(curOffs,fileSize)
            scCnt=0
    # end of while
    
    if seiRem==0:
        print '\nNo SEI with sei_type %d  found, output stream is not generated' %sei
        quit(0)
    print
    fpout=open(sys.argv[3],'wb')
    print 'SEIs to remove %d' %seiRem
    
    # remove the first element in liSize
    liSize.pop(0)
    # add size of the last frame
    liSize.append(fileSize-curOffs)
    
    print 'Copying without SEI %d....' %sei
    for nalType, nalStart, nalSize in zip(liType, liOffs, liSize):
        if nalType==0: # neither SPS nor PPS, copy this nalu
            fp.seek(nalStart,0)
            CopyFile(fp,fpout,nalSize,64000)

    fp.close()
    fpout.close()
    

