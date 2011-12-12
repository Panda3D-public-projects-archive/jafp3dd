# -*- coding: utf-8 -*-
"""
Created on Fri Dec 02 12:58:39 2011

@author: us997259
"""

from PIL import Image
import sys
import platform
if platform.system() == 'Windows':
    sys.path.append('c:\Panda3D-1.7.2')
    sys.path.append('c:\Panda3D-1.7.2\\bin')
    _DATAPATH_ = "./resources"
else:
    sys.path.append('/usr/lib/panda3d')
    sys.path.append('/usr/share/panda3d')
    _DATAPATH_ = "/home/shawn/Documents/project0/resources"


from pandac.PandaModules import CardMaker
from panda3d.core import NodePath, PNMImage, Texture

card = CardMaker('tempCard')
cardNP = NodePath(card.generate())

imageFile = sys.argv[1]
ndiv = int(sys.argv[2])
rootName = imageFile[:-3]

#img = Image.open(imageFile)
#img = img.transpose(Image.FLIP_TOP_BOTTOM)
#(Lx,Ly) = img.size

img = PNMImage(imageFile)

Lx = img.getReadXSize()
Ly = img.getReadYSize()
divX = Lx / ndiv
divY = Ly / ndiv
print divX,divY

subImg = PNMImage(divX+1,divY+1,3)
for nx in range(ndiv):
    for ny in range(ndiv):

        box = (nx*divX,ny*divY,(nx+1)*divX+1,(ny+1)*divY+1) # +1 on end points to overlap tiles
#        subImg = img.crop(box)
        subImg.copySubImage(img,0,0,0,0)
#        subImg = subImg.transpose(Image.FLIP_TOP_BOTTOM)
#        print subImg.size
#        subImg.save(rootName+"x%dy%d.jpg"%(nx,ny))
        tex = Texture()
        tex.load(subImg)
        cardNP.setTexture(tex)
        cardNP.writeBamFile(rootName+"x%dy%d.bam"%(nx,ny))

