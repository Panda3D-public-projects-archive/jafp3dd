# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 19:06:16 2012

@author: shawn
"""
import random, time
import os
import cPickle as pickle

from panda3d.core import *
from direct.interval.IntervalGlobal import *

from ScalingGeoMipTerrain import ScalingGeoMipTerrain
from client import NetClient
from common.NPC import DynamicObject
from network import rencode as rencode
from server import SNAP_INTERVAL, _mapName,_terraScale


_Datapath = "resources"
_AVMODEL_ = os.path.join('models','MrStix.x')
_STARTPOS_ = (64,64)
#SERVER_IP = '192.168.1.188'
SERVER_IP = None
LERP_INTERVAL = 1

class MapTile(NodePath,NetClient):
    """ a Game Client mapTile object: a chunk of the world map and all associated NPCs"""
    # TileManager determines what tiles are in scope for rendering on the client

    # Some hacky global consts for now
    _block_size_ = 32    # for LOD chunking
    _lod_near = 96 # ideal = Fog min distance
    _lod_far = 150
    _brute = 1 # use brute force
    _tree_lod_far = 128
    
    def __init__(self, name, myNode, mapDefName=_mapName, focus=None):
        NetClient.__init__(self)
        NodePath.__init__(self,name)

         # local loop if address = None
        ok = self.connect(SERVER_IP)
        self.myNode = myNode
        self.staticObjs = dict() # {objectKey:objNode}. add remove like any other dictionary
         # objects like other PCs and dynObjs that move/change realtime
        self.dynObjs = dict()    # A dictionary of nodepaths representing the moving objects
        self.snapshot = dict()
        self.minSnap = -1
        
        self.avnp = DynamicObject('AVNP', os.path.join(_Datapath,_AVMODEL_),1)
        self.avnp.reparentTo(self)
        self.dynObjs.update({myNode:self.avnp})
        
#        self.avnp.setPos(_STARTPOS_[0],_STARTPOS_[1],0)  
    
        self.focusNode = focus or self.avnp
        self.terGeom = None #ScalingGeoMipTerrain("Tile Terrain")
#            self.texTex = Texture()

        taskMgr.add(self.updateTile,'DoTileUpdates')
 
        print 'loading map ', mapDefName,'...',
        tileInfo = pickle.load(open(os.path.join(_Datapath,mapDefName+'.mdf'),'rb'))
#TODO: Clean Up this section after map defs are cleaned
        tileID = (0,0)        
        HFname,texList,Objects = tileInfo[tileID][0:3]
        
        self.setGeom(HFname, _terraScale, position=(0,0,0))
        self.setTexture(texList)
        for obj in Objects:
            self.addStaticObject(obj) # takes a an individual object for this tile
       
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

    def updateSnap(self,snapNum):
        if snapNum >= 0 and snapNum in self.snapshot: # did we get a message yet?
            print "Rendering from Snapshot: ",snapNum            
            snap = self.snapshot[snapNum+1] # get NEXT snapshot to interp to
            for obj in snap: # update all objects in this snapshot
                ID,x,y,z,h,p,r = obj
                if ID == self.myNode: print "updating", ID
                z = self.terGeom.getElevation(x,y)
                if ID not in self.dynObjs:
                    self.dynObjs.update({ID: DynamicObject('guy','resources/models/cone.egg',.6,self)})
                    self.dynObjs[ID].setPos(x,y,z)
                else:
#                self.dynObjs[ID].setHpr(h,p,r)
                    i = LerpPosInterval(self.dynObjs[ID],SNAP_INTERVAL,(x,y,z))
                    i.start()
                    ih=self.dynObjs[ID].hprInterval(3*SNAP_INTERVAL,(h,p,r))
                    ih.start() # just trying both forms
#                self.dynObjs[ID].printPos()

        
    def updateTile(self,task):
        if not self._brute: self.terGeom.update()    # update LOD geometry
#        for iNpc in self.dynObjs:
#            x,y,z = iNpc.calcPos(time.time())
#            iNpc.setZ(self.terGeom.getElevation(x,y))
        return task.cont

    # NETWORK DATAGRAM PROCESSING
    def ProcessData(self,datagram):
        print time.ctime(),' <recv> '
        I = DatagramIterator(datagram)
        msgID = I.getInt32()
        data = rencode.loads(I.getString()) # data matching msgID
        if msgID == 0:
            for entry in data:
                snapNum = entry.pop(0) # snapshot tick count
                if self.minSnap < 0: self.minSnap = snapNum - LERP_INTERVAL
                self.snapshot.update({snapNum:entry})
        else:
            print msgID,'::',data

        print "</>"

            