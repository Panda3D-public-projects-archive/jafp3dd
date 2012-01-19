# -*- coding: utf-8 -*-
"""
Created on Thu Dec 01 15:38:44 2011

@author: us997259
"""
from panda3d.core import *
import time, random

from common import NPC
from ScalingGeoMipTerrain import ScalingGeoMipTerrain

class MapTile(NodePath):
    # A tile is a chunk of a map.
    # TileManager determines what tiles are in scope for rendering on the client

    # Some hacky global consts for now
    _block_size_ = 20    # for LOD chunking
    _lod_near = 96 # ideal = Fog min distance
    _lod_far = 150
    _brute = False # use brute force
    _tree_lod_far = 128

    def __init__(self, name='Tile',focus=None):
        NodePath.__init__(self,name)
        self.focusNode = focus
        self.terGeom = ScalingGeoMipTerrain("Tile Terrain")
        self.texTex = Texture()
        self.staticObjs = dict() # {objectKey:objNode}. add remove like any other dictionary
        self.npcs = [] # objects like other PCs and NPCs that move/change realtime

    def setGeom(self,HFname, geomScale=(1,1,1),position=(0,0,0)):
        # GENERATE THE WORLD. GENERATE THE CHEERLEADER
        # Make an GeoMip Instance in this tile
        tmp = GeoMipTerrain('tmp gmt') # This gets HF and ensures it is power of 2 +1
        tmp.setHeightfield(Filename(HFname))
        HF = tmp.heightfield()
        self.terGeom = ScalingGeoMipTerrain("myHills",position)
#            terrain.setAutoFlatten(GeoMipTerrain.AFMStrong)
        self.terGeom.setHeightfield(HF)
        self.terGeom.setScale(geomScale[0],geomScale[1],geomScale[2]) # for objects of my class
        self.terGeom.setBruteforce(self._brute) # skip all that LOD stuff
        self.terGeom.setBorderStitching(0)
        self.terGeom.setNear(self._lod_near)
        self.terGeom.setFar(self._lod_far)
        self.terGeom.setBlockSize(self._block_size_)

        teraMat = Material()
        teraMat.setAmbient(VBase4(1,1,1,1))
        teraMat.setDiffuse(VBase4(1,1,1,1))
        teraMat.setShininess(0)
#        terrainRoot = terrain.getRoot()
        self.terGeom.root.setMaterial(teraMat)

#        self.terGeom.root.setColor(_SKYCOLOR_) # skycolor may make loading blips on horz less obvious
#        self.terGeom.setColorMap(os.path.join(_DATAPATH_,_TEXNAME_[0]))
        self.terGeom.root.reparentTo(self)
        self.terGeom.setFocalPoint(self.focusNode)
        self.terGeom.generate()

    def setTexture(self,texList):
#        print 'disabling terrain textures...'
#        texList = []
        if texList:
            terraTex = Texture() # loader.loadTexture(os.path.join(_DATAPATH_,texList))
            tmpimg = PNMImage(texList)
            terraTex.load(tmpimg)
            terraTex.setWrapU(Texture.WMClamp)
            terraTex.setWrapV(Texture.WMClamp)
            self.terGeom.root.setTexture(terraTex)
#            terrain.root.setTexScale(TextureStage.getDefault(),(hfx-1)/float(hfx), (hfy-1)/float(hfy))

#        leaves = TextureStage('leaves')
#        terrain.root.setTexture(leaves, loader.loadTexture(os.path.join(_DATAPATH_,_TEXNAME_[1])))
#        leaves.setMode(TextureStage.MAdd) # Default mode is Multiply
#        terrain.root.setTexScale(leaves, 100,100)

#        flowerStage = TextureStage('flowers')
#        flowerStage.setMode(TextureStage.MDecal)
#        terrainRoot.setTexture(flowerStage,loader.loadTexture(os.path.join(_DATAPATH_,_TEXNAME_[2])))
#        terrainRoot.setTexScale(flowerStage, 100, 100)

    def addStaticObject(self, obj):
        # These are intended to be things like trees, rocks, minerals, etc
        # that get updated on a push from the server. They aren't changing quickly
        tileNode = self.attachNewNode('StaticObject')
        tileNode.reparentTo(self)
        tmpModel = loader.loadModel(obj[2]) # name
        obj_Z = self.terGeom.getElevation(obj[0][0],obj[0][1])
        np = self.attachLODobj([tmpModel],(obj[0][0],obj[0][1],obj_Z),obj[1])
        np.reparentTo(tileNode)

    def attachLODobj(self, modelList, pos,state=1):
        # attaches subsequent models in modelList at pos x,y
        # different models are to be LODs of the model
        lodNode = FadeLODNode('Tree LOD node')
        lodNP = NodePath(lodNode)
#        lodNP.reparentTo(attachNode)
        lodNP.setPos(pos)
        lodNP.setH(random.randint(0,360))
        lodNP.setScale(state)
        for i,model in enumerate(modelList):
            near = i*self._tree_lod_far
            far = near + self._tree_lod_far
#                print near,far,model
            lodNode.addSwitch(far,near)
#                if i==1: lodNP.setBillboardAxis()     # try billboard effect
            model.instanceTo(lodNP)
        return lodNP

    def updateNPCs(self,task):
        for iNpc in self.npcs:
            if task.time > iNpc.nextUpdate:         # change direction and heading every so often
                iNpc.makeChange(task.time)
                self.write('time')
            x,y,z = iNpc.calcPos(task.time)
            iNpc.setZ(self.ttMgr.tiles[self.ttMgr.curIJ].terGeom.getElevation(x,y))
        return task.cont


    def updateTile(self,task):
        if not self._brute: self.terGeom.update()    # update LOD geometry
        for iNpc in self.npcs:
            x,y,z = iNpc.calcPos(task.time)
            iNpc.setZ(self.terGeom.getElevation(x,y))
        return task.done


class MapTileManager:
    curIJ = (0,0)
    inScopeTiles = [curIJ]
    Lx = Ly = []        # Size of a "Tile" in world units
    addTileQueue = []
    removeTileQueue = []
    lastAddTime = 0
    
    def __init__(self, infoDict, focus, size, delay=1, **kwargs ):
        (self.Lx,self.Ly) = size #
        self.minAddDelay = delay
        self.tileInfo = infoDict    # dictionary keyed by 2D tile indices (0,0) thru (N,M)
        self.tiles = {}        # this IS the list of tiles (dict object)
        self.refreshTileList() # need to initialize the addlist
        self.focusNode = focus
        taskMgr.setupTaskChain('TileUpdates',numThreads=4,threadPriority=1,frameBudget=0.02,frameSync=True)
        taskMgr.add(self.updateTask,'TileManagerUpdates',taskChain='TileUpdates')

    def setupTile(self,**kwds):
        pass

    def addTile(self, tileID):
        if self.addTileQueue.__contains__(tileID): # you are asking for a real add item
            if not self.tiles.has_key(tileID) and self.tileInfo.has_key(tileID): # this is not already in the dictionary but is in the overall dictionary
                til = self.setupTile(tileID)
                if til:    # everything went OK creating the object
                    self.tiles.update({tileID:til})
            if tileID not in self.addTileQueue:
                print "addtile error"
            else:
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
        inScopeTiles = []
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
                if not inScopeTiles.__contains__(newKey):
                    inScopeTiles.append( newKey )        # build up the new list for later
        # Now check for removes from current
        for key in self.tiles.keys():
            if not inScopeTiles.__contains__(key):    # compare newlist to current,
                if not self.removeTileQueue.__contains__(key):    #double check again
                    self.removeTileQueue.append(key)        #remove currents not in newlist

    def ijTile(self,position):
        i = int(position[0] / self.Lx)
        j = int(position[1] / self.Ly)
        return i,j

#    def updatePos(self,position): # of the focus
#        self.curPos = position
#        self.curIJ = self.ijTile(position)

    def updateTask(self,task):
        # Update the current tile based on where our focus node moved
        self.curIJ = self.ijTile(self.focusNode.getPos())
        # Manage the tile list; add remove, etc
        self.refreshTileList()
        if self.addTileQueue and time.time()-self.lastAddTime > self.minAddDelay:
            self.addTile(self.addTileQueue[0])
            self.lastAddTime = time.time()
        elif self.removeTileQueue:
#            print "removing tiles from dict"
            self.removeTile(self.removeTileQueue[0])
        for tile in self.tiles.values():
            tile.updateTile(task)

        return task.cont


class TerrainManager(MapTileManager):

    def __init__(self,info, parentNode,tileScale=(1,1,1), **kwargs ):
        MapTileManager.__init__(self,info, **kwargs)
        self.parentNode = parentNode
        self.tileScale = tileScale
        self.focusNode = kwargs['focus']
        self.addTile(self.curIJ)


    def setupTile(self,tileID):
#TODO:        if self.tileInfo.has_key(tileID):
        HFname,texList,Objects = self.tileInfo[tileID][0:3]

        newTile = MapTile('mapTile',self.focusNode)
        newTile.setPos(tileID[0]*self.Lx,tileID[1]*self.Ly,0)
        newTile.reparentTo(self.parentNode)

        newTile.setGeom(HFname, self.tileScale, position=(0,0,0))
        newTile.setTexture(texList)
        for obj in Objects:
#            r = random.randint(0,9)
#            obj[2] = 'resources/models/sampleTree'+str(r)+'.bam'    # DEBUG OVERRIDE TO TEST MODEL
            newTile.addStaticObject(obj) # takes a an individual object for this tile

        for n in range(1):
            newTile.npcs.append( NPC('guy','resources/models/cone.egg',1,newTile) )
#TODO: HOW TO GET NPC INFO PER TILE FROM SERVER???

        return newTile

#    def getElevation(self,worldPos):
#        ij = MapTileManager.ijTile(self,worldPos)
#        if self.tiles.has_key(ij):
#            return self.tiles[ij].terGeom.getElevation(worldPos[0],worldPos[1])
#        elif self.tileInfo.has_key(ij): # check if in dictionary at all
#            self.addTileQueue.append(ij)
#            self.addTile(ij)
#            return self.tiles[ij].terGeom.getElevation(worldPos[0],worldPos[1])
#        else:
#            return [] # that tile just doesn't exist!

#    def updateTask(self,task):
#        MapTileManager.updateTask(self,task)
#        if not _Brute:
#            for tile in self.tiles.values():
#            # Deformation test below
##            nf = self.defo(129,129)  #.getReadXSize(),hf.getReadYSize())
##            tile.setHeightfield(tile.heightfield()*nf)
#                tile.terGeom.update()    # update LOD geometry
#        return task.cont

#class objectManager(MapTileManager):
#    def __init__(self,info, **kwargs):
#        MapTileManager.__init__(self,info,**kwargs)
#        self.parentNode = kwargs['parentNode']
#        self.zFunc = kwargs['zFunc']
#        self.addTile(self.curIJ)
#
#    def setupTile(self,tileID):
#        print "overriding tree models"
##        my_model.reparentTo(lod_np)
#        tileNode = self.parentNode.attachNewNode('tile'+str(tileID))
#        tileNode.reparentTo(self.parentNode)
#        if self.tileInfo.has_key(tileID):
#            for obj in self.tileInfo[tileID]:
#                r = random.randint(0,9)
#                obj[2] = 'resources/models/sampleTree'+str(r)+'.bam'    # DEBUG OVERRIDE TO TEST MODEL
##                obj[1] = 1.0
#                tmpModel = loader.loadModel(obj[2]) # name
#
#                obj_Z = self.zFunc(obj[0])
#        #TODO: MAKE CONDITIONAL HERE. obj_Z may not return valid if not tile
#        # only if valid obj_Z do the next part.
#                np = self.attachLODobj([tmpModel],(obj[0][0],obj[0][1],obj_Z),obj[1])
#                np.reparentTo(tileNode)
##                tmpModel.instanceTo(lod_np)
##                tmpModel.setPos(obj[0][0],obj[0][1],obj_Z)
##                tmpModel.setScale(obj[1])
##                tmpModel.setH(random.randint(0,360))
#        return tileNode
#
#    def attachLODobj(self, modelList, pos,state=1):
#        _tree_lof_far = 128
#        lodNode = FadeLODNode('Tree LOD node')
#        lodNP = NodePath(lodNode)
##        lodNP.reparentTo(attachNode)
#        lodNP.setPos(pos) #  offset of plane is -1/2 * Zscale
#        lodNP.setH(random.randint(0,360))
#        lodNP.setScale(state)
#        for i,model in enumerate(modelList):
#            near = i*_TreeLODfar
#            far = near + _TreeLODfar
##                print near,far,model
#            lodNode.addSwitch(far,near)
##                if i==1: lodNP.setBillboardAxis()     # try billboard effect
#            model.instanceTo(lodNP)
#        return lodNP