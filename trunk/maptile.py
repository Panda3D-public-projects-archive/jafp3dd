# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 19:06:16 2012

@author: shawn
"""
import random, time

from panda3d.core import *

from ScalingGeoMipTerrain import ScalingGeoMipTerrain
from client import NetClient
from common.NPC import DynamicObject
from common import rencode as rencode

class MapTile(NodePath,NetClient):
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
        NetClient.__init__(self)
        self.connect() # local loop if no address

        self.focusNode = focus
        self.terGeom = ScalingGeoMipTerrain("Tile Terrain")
        self.texTex = Texture()
        self.staticObjs = dict() # {objectKey:objNode}. add remove like any other dictionary
         # objects like other PCs and dynObjs that move/change realtime
        self.dynObjs=[]
        for n in range(6):
            self.dynObjs.append( DynamicObject('guy','resources/models/cone.egg',.6,self) )
        taskMgr.add(self.updateTile,'DoTileUpdates')
        
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

#    def updatedynObjs(self,task):
#        for iNpc in self.dynObjs:
#            if task.time > iNpc.nextUpdate:         # change direction and heading every so often
#                iNpc.makeChange(task.time)
#                self.write('time')
#            x,y,z = iNpc.calcPos(task.time)
#            iNpc.setZ(self.ttMgr.tiles[self.ttMgr.curIJ].terGeom.getElevation(x,y))
#        return task.cont


    def updateTile(self,task):
        if not self._brute: self.terGeom.update()    # update LOD geometry
        for iNpc in self.dynObjs:
            x,y,z = iNpc.calcPos(time.time())
            iNpc.setZ(self.terGeom.getElevation(x,y))
        return task.cont

    # NETWORK DATAGRAM PROCESSING
    def ProcessData(self,datagram):
        print time.ctime(),' <recv> '
        I = DatagramIterator(datagram)
        msgID = I.getInt32()
        data = rencode.loads(I.getString()) # data matching msgID
        if msgID == 0:
            for update in data:
                print update
                [utime,ID,x,y,z,h,p,r,speed] = update
                Q = Quat()
                Q.setHpr((h,0,0))
                self.dynObjs[ID].updateCommandsBuffer(utime,[Vec3(x,y,z),Q.getForward()*speed,Vec3(0,0,0)])           
        else:
            print msgID,'::',data

        print "</>"

            