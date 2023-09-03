import numpy as np
from sewar.full_ref import ssim
from optparse import OptionParser

"""
Copyright (c) 2023 Shevach Riabtsev, slavah264@gmail.com

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


def parse_options():
    parser = OptionParser(usage="%prog [-i]", version="%prog 1.0")

    parser.add_option("-f",
                        dest = "rfilename",
                        help = "reference yuv",
                        type = "string",
                        action = "store"
                        )
    parser.add_option("-d",
                        dest = "dfilename",
                        help = "decoded yuv",
                        type = "string",
                        action = "store"
                        )
    parser.add_option("-n",
                        dest = "numframes",
                        help = "number of frames to process, if 0 then all frames, default 0",
                        type = "int",
                        action = "store",
                        default = 0
                        )
                        
    parser.add_option("--width",
                        dest = "width",
                        help = "width",
                        type = "int",
                        action="store",
                        )
 
    parser.add_option("--height",
                        dest = "height",
                        help = "height",
                        type = "int",
                        action="store",
                        )
                        
    (options, args) = parser.parse_args()
    
        
    if options.rfilename and options.dfilename and options.width and options.height:
        return (options.rfilename,options.dfilename,options.numframes,options.width, options.height) 
        
    parser.print_help()
    quit(-1)


if __name__ == "__main__":
    

    rfilename,dfilename,numframes,width,height = parse_options()
    
    fr=open(rfilename,'rb')
    fd=open(dfilename,'rb')
    framelen = (width*height*3)>>1
    frameCnt=0
    sumSsim=0.0
    while True:
        if numframes:
            if frameCnt>=numframes:
                break
        yuvrImage=fr.read(framelen)
        if len(yuvrImage)<framelen:
            break
        yuvdImage=fd.read(framelen)
        if len(yuvdImage)<framelen:
            break
            
        yuvr = np.frombuffer(yuvrImage, dtype=np.uint8).reshape(height*3//2,width)
        yuvd = np.frombuffer(yuvdImage, dtype=np.uint8).reshape(height*3//2,width)
        
        ssimval,_=ssim(yuvr, yuvd, MAX=256)
        print('frame   %5d,  ssim    %.2f' %(frameCnt,ssimval))
        frameCnt+=1
        sumSsim+=ssimval
        
    print('\n')
    print('average ssim      %.2f' %(sumSsim/frameCnt))
    quit(0)
    

