# -*- coding: utf-8 -*-
"""
Created on Fri Dec 02 12:58:39 2011

@author: us997259
"""

from PIL import Image
import sys

imageFile = sys.argv[1]
ndiv = int(sys.argv[2])
rootName = imageFile[:-3]

img = Image.open(imageFile)
img = img.transpose(Image.FLIP_TOP_BOTTOM)
(Lx,Ly) = img.size
divX = Lx / ndiv
divY = Ly / ndiv
print divX,divY

for nx in range(ndiv):
    for ny in range(ndiv):

        box = (nx*divX,ny*divY,(nx+1)*divX+1,(ny+1)*divY+1) # +1 on end points to overlap tiles
        subImg = img.crop(box).transpose(Image.FLIP_TOP_BOTTOM)
        print subImg.size
        subImg.save(rootName+"x%dy%d.jpg"%(nx,ny))


