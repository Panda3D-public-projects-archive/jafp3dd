# -*- coding: utf-8 -*-
"""
Created on Fri Dec 02 12:58:39 2011

@author: us997259
"""

from PIL import Image
import sys
from math import ceil

def splitToTiles(imageFile,Ltile):
    rootName = imageFile[:-3]
    sfx = imageFile[-3:]
    
    img = Image.open(imageFile)
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    (Lx,Ly) = img.size
#    divX = Lx / ndiv
    nXdiv = ceil(Lx/Ltile)
#    divY = Ly / ndiv
    nYdiv = ceil(Ly/Ltile)
#    print divX,divY
    
    for nx in range(nXdiv):
        for ny in range(nYdiv):    
#            box = (nx*divX,ny*divY,(nx+1)*divX+1,(ny+1)*divY+1) # +1 on end points to overlap tiles
            box = (nx*Ltile,ny*Ltile,(nx+1)*Ltile+1,(ny+1)*Ltile+1) # +1 on end points to overlap tiles
            subImg = img.crop(box).transpose(Image.FLIP_TOP_BOTTOM)
            print subImg.size
            subImg.save(rootName+"x%dy%d.%s"%(nx,ny,sfx))
    

if __name__ == '__main__':
    imageFile = sys.argv[1]
    Ltile = int(sys.argv[2])
    splitToTiles(imageFile,Ltile)
