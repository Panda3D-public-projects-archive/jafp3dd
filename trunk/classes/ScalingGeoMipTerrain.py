# -*- coding: utf-8 -*-
"""
A subclass of panda3d GeoMipTerrain Class that returns elevations as if in real world
units; not scaled 0-1 like GMP

Created on Mon Jan 16 18:13:17 2012

@author: shawn
"""
from panda3d.core import GeoMipTerrain

# This should probably go in its own file  
class ScalingGeoMipTerrain(GeoMipTerrain):      
    def __init__(self, name="ScalingGeoMipTerrain",position=(0,0,0)):
        GeoMipTerrain.__init__(self,name)
        # these units are all in "Panda" space units. This class takes care of 
        # scaling GeoMipTerrain data in and out
        (x0,y0,z0)=position
        self.root = self.getRoot()
        self.root.setPos(x0,y0,z0)
        self.Sx = 1
        self.Sy = 1
        self.Sz = 1
#        self.Xoffset = 0.0
#        self.Yoffset = 0.0
#        self.Zoffset = 0.0

    def __del__(self):
#        removed.getRoot().detachNode()
        self.root.removeNode() # frees up memory Vs just detach
        
    def getElevation(self,scaledX, scaledY):
        (x0,y0,z0) = self.root.getPos()
        rawX = (scaledX-x0) / self.Sx 
        rawY = (scaledY-y0) / self.Sy
        rawZ = GeoMipTerrain.getElevation(self,rawX,rawY)
        return self.Sz*rawZ + z0
    def setSx(self,val):
        self.Sx = val
        self.getRoot().setSx(val)
    def setSy(self,val):
        self.Sy = val    
        self.getRoot().setSy(val)
    def setSz(self,val):
        self.Sz = val
        self.getRoot().setSz(val)
    def setScale(self,valX,valY,valZ):
        self.Sx = valX
        self.Sy = valY
        self.Sz = valZ
        self.getRoot().setScale(valX, valY, valZ)
        # need to recalc setZ if change scale...
        
#    def setPos(self,valX,valY,valZ):
#        self.Xoffset = valX
#        self.Yoffset = valY
#    def setZ(self,val): # input expected to be in normal panda space units
#        self.Zoffset = val
#        self.getRoot().setZ(self.Zoffset/self.Sz)