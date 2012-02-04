# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 19:06:16 2012

@author: shawn
"""
import random
import os
import cPickle as pickle

from panda3d.core import *
from direct.showbase import Loader
from direct.showbase.DirectObject import DirectObject

from ScalingGeoMipTerrain import ScalingGeoMipTerrain

_Datapath = "resources"
_terraScale = (4,4,64) # xy scaling not working right as of 12-10-11. prob the LOD impacts

class MapTile(DirectObject):
    """ a Game Client mapTile object: a chunk of the world map and all associated NPCs"""
    # TileManager determines what tiles are in scope for rendering on the client

    # Some hacky global consts for now
    _block_size_ = 32    # for LOD chunking
    _lod_near = 96 # ideal = Fog min distance
    _lod_far = 150
    _brute = 1 # use brute force
    _tree_lod_far = 128
    
    def __init__(self, name, mapDefName,parentNode, focus=None):
        self.root = parentNode #NodePath(PandaNode(name))
        self.np = NodePath(self.root)
        self.loader = Loader.Loader(self)
        
         # local loop if address = None
        self.staticObjs = list() # a list of node paths
    
        if focus:
            self.focusNode = focus 
            self._brute = False
        else:
            self._brute = True
            self.focusNode = None
            
        self.terGeom = None #ScalingGeoMipTerrain("Tile Terrain")
#            self.texTex = Texture()

#        taskMgr.add(self.updateTerra,'DoTileUpdates')
 
#        print 'loading map ', mapDefName,'...',
        tileInfo = pickle.load(open(os.path.join(_Datapath,mapDefName+'.mdf'),'rb'))
#TODO: Clean Up this section after map defs are cleaned
        tileID = (0,0)        
        HFname,texList,Objects = tileInfo[tileID][0:3]
        
        self.setGeom(HFname, _terraScale, position=(0,0,0))
        self.setTexture(texList)
        for obj in Objects:
            tmp = self.addStaticObject(obj)
            self.staticObjs.append( tmp ) # takes a an individual object for this tile
            if obj[0][0] > 200 or obj[0][1] > 200:
                tmp.detachNode()
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
        self.terGeom.root.reparentTo(NodePath(self.root))
        if self.focusNode:
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

    def addStaticObject(self, obj, collide=False):
        # These are intended to be things like trees, rocks, minerals, etc
        # that get updated on a push from the server. They aren't changing quickly
#        print "debug::addStaticObject >> overriding model name"
#        obj[2] = 'resources\models\simpleTree2.x'
        tmpModel = self.loader.loadModel(obj[2]) # name        
        obj_Z = self.terGeom.getElevation(obj[0][0],obj[0][1])
        np = self.attachLODobj([tmpModel],(obj[0][0],obj[0][1],obj_Z),obj[1])
        return np
        
    def attachLODobj(self, modelList, pos,state=1):
        # attaches subsequent models in modelList at pos x,y
        # different models are to be LODs of the model
        lodNP = self.np.attachNewNode(FadeLODNode('Tree LOD node'))
        lodNP.setPos(pos)
        lodNP.setH(random.randint(0,360))
        lodNP.setScale(state)
        for i,model in enumerate(modelList):
            near = i*self._tree_lod_far
            far = near + self._tree_lod_far
#                print near,far,model
            lodNP.node().addSwitch(far,near)
#                if i==1: lodNP.setBillboardAxis()     # try billboard effect
            model.instanceTo(lodNP)
        return lodNP

    def updateTerra(self,task):
        if not self._brute: self.terGeom.update()    # update LOD geometry
        return task.cont
          