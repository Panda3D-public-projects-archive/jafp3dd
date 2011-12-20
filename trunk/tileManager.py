# -*- coding: utf-8 -*-
"""
Created on Thu Dec 01 15:38:44 2011

@author: us997259
"""
import os
from panda3d.core import *
import time, random

#_DATAPATH_ = "./resources"

_BLOCKSIZE_ = 32    # for LOD chunking
_LODNEAR_ = 64 # ideal = Fog min distance
_LODFAR_ = 192

# This should probably go in its own file  
class ScalingGeoMipTerrain(GeoMipTerrain):
    def __init__(self, name=None,x0=0,y0=0,z0=0):
        GeoMipTerrain.__init__(self,name)
        # these units are all in "Panda" space units. This class takes care of 
        # scaling GeoMipTerrain data in and out
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
#       

class tileManager:
    curIJ = (0,0)
    addTileQueue = []
    removeTileQueue = []
    lastAddTime = 0
    
    def __init__(self,parentNode,tileScale=(1,1,1), delay=1, **kwargs ):
        self.minAddDelay = delay
        self.tileScale = tileScale # easiest if this is left smae for all tiles
        self.parentNode = parentNode
        self.tileInfo = kwargs['infoDict']
        self.tiles = {}
        self.refreshTileList() # need to initialize the addlist
                
    def setupTile(self,**kwds):
        pass            
    
    def addTile(self, tileID):
        if self.addTileQueue.__contains__(tileID): # you are asking for a real add item            
            if not self.tiles.has_key(tileID) and self.tileInfo.has_key(tileID): # this is not already in the dictionary but is in the overall dictionary
                ter = self.setupTile(tileID)
                if ter:    # everything went OK creating the object
                    self.tiles.update({tileID:ter})
            self.addTileQueue.remove(tileID) # pull it out of the list even if not in the dict(bad list entry)        
        # REMOVE TILES FROM ADD LIST ONCE THEY ARE ADDED

    def removeTile(self,tileID):    # make this a background task eventually?
        if self.removeTileQueue.__contains__(tileID): # you are asking for a real remove item            
            if self.tiles.has_key(tileID): # this is really in the dictionary
                removed = self.tiles.pop(tileID)
                del removed # MAKE SURE THE REMOVED OBJECT CLEANS ITSELF UP WITH A del Call!!!
            self.removeTileQueue.remove(tileID) # pull it out of the list even if not in the dict(bad list entry)        
        
    def refreshTileList(self,radius=1):    # make this a background task ?
#       determine what the in range tile list should be and update it        
        newTileList = []
        for di in xrange(-radius,radius+1):
            for dj in xrange(-radius,radius+1):
                # GENERATING THE LIST FIRST ALLOW TO DO IN BACKGROUND TASK LATER
                # COMPARE CURRENT AAND NEW; CREATE AN "ADD" list and a REMOVE LIST
                # THE ADD/REMOVE TASKS CAN BE SET ON DIFFERENT PRIORITIES (remove low)
                # THIS WOULD ALSO ENABLE CACHING OF SOME SORT-don't remove until X
                newKey = ( max(0,self.curIJ[0]+di), max(0,self.curIJ[1]+dj) )
                if not self.tiles.has_key(newKey): # look for new key in current dict
                    if not self.addTileQueue.__contains__(newKey): # double check not in add list already
                        self.addTileQueue.append( newKey )    # add to the add list
#                        print "adding ", newKey
                if not newTileList.__contains__(newKey):
                    newTileList.append( newKey )        # build up the new list for later
        # Now check for removes from current
        for key in self.tiles.keys():
            if not newTileList.__contains__(key):    # compare newlist to current, 
                if not self.removeTileQueue.__contains__(key):    #double check again
                    self.removeTileQueue.append(key)        #remove currents not in newlist
                
    def ijTile(self,position):
        i = int(position[0] / self.Lx)
        j = int(position[1] / self.Ly)
        return i,j

    def updatePos(self,position): # of the focus
        self.curPos = position
        self.curIJ = self.ijTile(position)
        
    def updateTask(self,task):
        self.refreshTileList()
        if self.addTileQueue and time.time()-self.lastAddTime > self.minAddDelay:
            self.addTile(self.addTileQueue[0])
            self.lastAddTime = time.time()
        elif self.removeTileQueue:
#            print "removing tiles from dict"
            self.removeTile(self.removeTileQueue[0])

        return task.cont


class terrainManager(tileManager):
    
    def __init__(self,parentNode,tileScale=(1,1,1), delay=1, **kwargs ):
        tileManager.__init__(self,parentNode,tileScale,delay=1,**kwargs)        
        self.LODfocusNode = kwargs['focusNode']
        self.objectInfo = kwargs['objDict']
        # COULD just init the addlist and let the task do the loading        
#        for thisTile in tileInfo:    
        self.addTile(self.curIJ)            
    
    def addTile(self,tileID):
        tileManager.addTile(self,tileID)
        self.placeObjects(tileID)    # HAACK FOR NOW

    def defo(self,xp,yp):
        nf = PNMImage(xp,yp,1,65535)
        nerr = int(.05 * xp * yp)
        for i in range(nerr):
            x0 = random.randint(0,xp-1)
            y0 = random.randint(0,yp-1)
            nf.setGray(x0,y0,.8+.2*random.random())
        return nf
         
    def setupTile(self,tileID):
#    GENERATE THE WORLD. GENERATE THE CHEERLEADER                
        HFname = self.tileInfo[tileID][0]
        texList = self.tileInfo[tileID][1]

#        try:            
#            t0 = time.time()
#            print "Loading HF"
        tmp = GeoMipTerrain('tmp gmt') # This gets HF and ensures it is power of 2 +1
        tmp.setHeightfield(Filename(HFname))
        HF = tmp.heightfield()
#            t = [(time.time()-t0)*1e3]
#        if not self.Lx or not self.Ly:
        hfx = HF.getReadXSize()
        hfy = HF.getReadYSize()
        # Assuming HF are coming in +1,+1 to overlap neighbors.
        # remove that below when calc the tile locations (otherwise won't overlap)
        self.Lx = (hfx-1) * self.tileScale[0]
        self.Ly = (hfy-1) * self.tileScale[1] 
#            t.append((time.time()-t0)*1e3 )
        terrain = ScalingGeoMipTerrain("myHills",tileID[0]*self.Lx,tileID[1]*self.Ly,0)
#            terrain.setAutoFlatten(GeoMipTerrain.AFMStrong)
        terrain.setHeightfield(HF)
#            t.append((time.time()-t0)*1e3 )
        terrain.setScale(self.tileScale[0],self.tileScale[1],self.tileScale[2]) # for objects of my class        
        terrain.setBruteforce(0) # skip all that LOD stuff 
        terrain.setBorderStitching(0)   
        terrain.setNear(_LODNEAR_)
        terrain.setFar(_LODFAR_)
        terrain.setBlockSize(_BLOCKSIZE_)
    
#            teraMat = Material()
#            teraMat.setAmbient(VBase4(1,1,1,1))
#            teraMat.setDiffuse(VBase4(1,1,1,1))
#            teraMat.setShininess(0)
#    #        terrainRoot = terrain.getRoot()     
#            terrain.root.setMaterial(teraMat)
                    
    #        terrainRoot.setColor(1,0,1,1) 
    #        terrain.setColorMap(os.path.join(_DATAPATH_,_TEXNAME_[0]))
        if texList:
#                t.append((time.time()-t0)*1e3 )
#                print "Loading Tex"
            
            terraTex = Texture() # loader.loadTexture(os.path.join(_DATAPATH_,texList))
            tmpimg = PNMImage(texList)
            terraTex.load(tmpimg)
#                t.append((time.time()-t0)*1e3 )

        
        terraTex.setWrapU(Texture.WMClamp)
        terraTex.setWrapV(Texture.WMClamp)
        terrain.root.setTexture(terraTex)
    #            terrain.root.setTexScale(TextureStage.getDefault(),(hfx-1)/float(hfx), (hfy-1)/float(hfy))
            
    #        leaves = TextureStage('leaves')
    #        terrain.root.setTexture(leaves, loader.loadTexture(os.path.join(_DATAPATH_,_TEXNAME_[1])))
    #        leaves.setMode(TextureStage.MAdd) # Default mode is Multiply
    #        terrain.root.setTexScale(leaves, 100,100)
            
    #        flowerStage = TextureStage('flowers')
    #        flowerStage.setMode(TextureStage.MDecal)
    #        terrainRoot.setTexture(flowerStage,loader.loadTexture(os.path.join(_DATAPATH_,_TEXNAME_[2])))
    #        terrainRoot.setTexScale(flowerStage, 100, 100)
    #    
#            t.append((time.time()-t0)*1e3 )
#            print "Starting generate tile (%d,%d)" %(tileID[0],tileID[1])
        terrain.root.reparentTo(self.parentNode)
        terrain.setFocalPoint(self.LODfocusNode) 
        terrain.generate() 
#            t.append((time.time()-t0)*1e3 )
            
#            delta=[]
#            for i in range(1,len(t)):
#                delta.append( round(t[i]-t[i-1],2) )
#            print delta, int(t[-1])
        
        
        return terrain 
#        except:
#            print "  --> failed to setup terrain"
#            return []

# TRY TO ADD TREES HERE
    def placeObjects(self,tileID):
        for obj in self.objectInfo[tileID]:
            tmpModel = loader.loadModel(obj[2]) # name
            tmpModel.reparentTo(self.parentNode)
            obj_Z = self.getElevation(obj[0])
            tmpModel.setPos(obj[0][0],obj[0][1],obj_Z)
            tmpModel.setScale(obj[1])
            tmpModel.setH(random.randint(0,360))
               
    def getElevation(self,worldPos):
        ij = tileManager.ijTile(self,worldPos)
        if self.tiles.has_key(ij):
            return self.tiles[ij].getElevation(worldPos[0],worldPos[1])
        elif self.tileInfo.has_key(ij): # check if in dictionary at all
            self.addTileQueue.append(ij)
            self.addTile(ij)
            return self.tiles[ij].getElevation(worldPos[0],worldPos[1])
        else: 
            return [] # that tile just doesn't exist!
        
    def updateTask(self,task):
        tileManager.updateTask(self,task)
        for tile in self.tiles.values():
            # Deformation test below
#            nf = self.defo(129,129)  #.getReadXSize(),hf.getReadYSize())
#            tile.setHeightfield(tile.heightfield()*nf)
            tile.update()
        return task.cont
