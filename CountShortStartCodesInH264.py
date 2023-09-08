import os
import re
import struct
import bitstring
from optparse import OptionParser

"""
Copyright (c) 2023 Shevach Riabtsev, slavah264@gmail.com

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
    parser = OptionParser(usage="%prog [-i] [-v] [-p]", version="%prog 1.1")

    parser.add_option("-i",
                        dest = "filename",
                        help = "input h264 file",
                        type = "string",
                        action = "store"
                        )
                       
                        
    parser.add_option("-v",
                        dest = "verbose",
                        help = "verbose mode, print offset of short start code (default false)",
                        action="store_true",
                        default=False)
                        
    parser.add_option("-n",
                        dest = "framesToProcess",
                        help = "number frames to process, if 0 then the whole stream processed",
                        type = "int",
                        action = "store",
                        default=0
                        )
                        
    (options, args) = parser.parse_args()
    

    if options.filename:
        if os.path.isfile(options.filename)==False:
            print('Input file not exist or directory')
            parser.print_help()
            quit(-1)
        
        return (options.filename, options.verbose,options.framesToProcess) 
        
    parser.print_help()
    quit(-1)
    


if __name__ == "__main__":

    filename, verbose,framesToProcess = parse_options()
    
    fp=open(filename,'rb')
    
    
    # get the input file size
    statinfo = os.stat(filename)
    fileSize=statinfo.st_size
    print('\n')

    curOffs=0
    prevOffs=0
    nalType=0
    scp=re.compile('000001|00000001', re.IGNORECASE)
    frameCnt=0   # if verbose is on
    shortStartCodeCnt=0  # 24 bits 00 00 01
    shortStartCodeFound=False
    
    while curOffs+4 < fileSize:
        if framesToProcess>0 and frameCnt>=framesToProcess:
            break
        # search for start code
        buf=fp.read(2048)
        curBufSize = len(buf)
        if curBufSize<4:
            break # eof
                
        c = bitstring.BitArray(bytes=buf, length=curBufSize*8) 
        hexbuf=c.hex
        startCodeFound=False
        shortStartCodeFound=False
        for match in scp.finditer(hexbuf):
            idx=int(match.start())
            if (idx&1)==0:
                startCodeFound=True
                scPos = int(idx/2)
                nalOffs = curOffs+scPos
                curOffs=curOffs+scPos+3                
                if buf[scPos+2]==0: # start code len = 4
                    curOffs+=1
                else:  # short start code
                    shortStartCodeFound=True
                    shortStartCodeCnt+=1
                    if verbose:
                        print('short start code at offset %d (0x%x)' %(curOffs-3,curOffs-3))
                break
                

        if startCodeFound==False:
            fp.seek(-3,1)
            curOffs=fp.tell()
            continue
            
        if curOffs>fileSize-3:
            break # eof
            
        fp.seek(curOffs,0)

        # read nal header
        buf=fp.read(1)
        if len(buf)==0:
            break   # eof
        nalHdr=struct.unpack("B", buf)[0]
        nalType=nalHdr&0x1f # to eliminate nal_ref_dic and forbidden_zero_bit
        if nalType==1 or nalType==5:
            buf=fp.read(1)
            sliceHdr=struct.unpack("B", buf)[0]
            if (sliceHdr&0x80)==0x80: # first slice               
                frameCnt+=1
                
        curOffs=fp.tell()
    # end of while
    
    if verbose:
        print('\n')
    print('number of detected frames    %10d' %frameCnt)
    
    print('number of short start codes  %10d' %shortStartCodeCnt)
    fp.close()
    quit(0)
    

    

