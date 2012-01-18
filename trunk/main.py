##!/usr/local/bin/python

# SETUP SOME PATH's
import sys

_Datapath = "resources"

import os.path
from math import *
from numpy import sign
import time
import cPickle as pickle
     
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
#from direct.showbase.DirectObject import DirectObject
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText

from panda3d.core import loadPrcFileData
loadPrcFileData( '', 'sync-video 0' ) 

from CelestialBody import CelestialBody
from tileManager import MapTile as MapTile
from NPC import NPC
from network.client import NetClient
from network import rencode as rencode

TILE_SIZE = (128,128)

# RENDERING OPTIONS #
_DoLights = 1
_DoFog = 0
_ShowSky = 0        # put up the sky dome
_ShowClouds = 0
_ShowOcean = 0

# COLORS
_DARKBLUE_ = VBase4(.0,.4,.7,1)
_LIGHTBLUE_ = VBase4(.3,.7,1,1)
_BLACK_ = VBase4(0,0,0,1)
_WHITE_= VBase4(1,1,1,1)


# SKY PARMS
#_SkyTex = ('textures/sky0.png',1,1)
_SkyTex = ('textures/skyTexPolar.png',1,1)
_SkyModel = 'textures/curved.png'
_SKYCOLOR_ = _DARKBLUE_

_OceanTex = ('textures/oceanTex2.png',1,1)
_Sealevel = 2

_Suntex = 'textures/blueSun.png'


fogPm = (96,150,45,250,500) # last 3 params for linfalloff - not used atm

# AVATAR SETTINGS
_AVMODEL_ = os.path.join('models','MrStix.x')
_STARTPOS_ = (64,64)
_TURNRATE_ = 120    # Degrees per second
_WALKRATE_ = 8
_MINCAMDIST_ = 1
_MaxCamDist = 20
 
# TERRAIN SETTINGS
_terraScale = (1,1,60) # xy scaling not working right as of 12-10-11. prob the LOD impacts
_mapName='map2'


PStatClient.connect()
#import pycallgraph
#pycallgraph.start_trace()
       
class TileClient(ShowBase,NetClient):
    Kturn = 0
    Kwalk = 0
    Kstrafe = 0
    Kzoom = 0
    Kpitch = 0
    Ktheta = 0
    mbState = [0,0,0,0] # 3 mouse buttons + wheel, 1 down, 0 on up

    ## DO SOME CAM STUFF
    camVector = [10,0,15]    # [distance, heading, pitch ]
    mousePos = [0,0]
    mousePos_old = mousePos
    
        
    def __init__(self):
        ShowBase.__init__(self)
        NetClient.__init__(self)
        self.setBackgroundColor(_SKYCOLOR_)
        self.setFrameRateMeter(1)
        #app.disableMouse()
        render.setAntialias(AntialiasAttrib.MAuto)
        render.setShaderAuto()

        self.terraNode = render.attachNewNode('Terrain Node') 
        self.terraNode.flattenStrong()
        self.avnp = render.attachNewNode("Avatar")
        self.skynp = render.attachNewNode("SkyDome")               
        self.floralNode = self.terraNode.attachNewNode('TreesAndFlowers') # child to inherit terrain fog
        self.camera.reparentTo(self.avnp)
        self.camera.setY(-10)
        self.camera.lookAt(self.avnp)
        self.textObject = OnscreenText(text = str(self.avnp.getPos()), pos = (-0.9, 0.9), scale = 0.07, fg = (1,1,1,1))       
        if _DoLights: self.setupLights()        
        if _ShowSky: self.setupSky() # must occur after setupAvatar    
        
        self.setupKeys()
        self.connect() # local loop if no address
        self.setupAvatar()     

        self.loadMap(_mapName)
     
        self.sun = CelestialBody(self.render, self.avnp, './resources/models/plane', \
        './resources/textures/blueSun.png',radius=4000,Fov=7,phase=pi/9)
        self.sun.period = 1800
        self.sun.declin = 0
        self.sun.aMin = VBase4(.1,.1,.1,1)
        self.sun.eColor=VBase4(1,1,1,1)
        self.sun.aColor = VBase4(.2,.2,.2,1)
        self.sun.dColor = VBase4(1,1,1,1)*0
        self.sun.dayColor = VBase4(_SKYCOLOR_)
        taskMgr.add(self.sun.updateTask,'sun task')
#        
#        self.moon = CelestialBody(self.render,self.avnp, './resources/models/plane', \
#        './resources/textures/copperMoon.png',radius=4000,Fov=12,phase=pi,eColor=VBase4(.5,1,1,1)) 
#        self.moon.period = 30
#        self.moon.declin = 20
#        self.moon.dColor = VBase4(.2,.2,.2,1)
#        self.moon.aMin = VBase4(.1,.15,.1,1)
#        taskMgr.add(self.moon.updateTask,'moon task')
#            

        if _ShowOcean:
            print "ocean in DEBUG MODE. NOT WORKING!"
            self.oceanNode = render.attachNewNode('ocean plane')        
#            oceanPlane = loader.loadModel(os.path.join(_Datapath,'models','plane')) #plane model -.5,.5 corners
#            oceanPlane.setPos(.5,.5,0)
#            oceanPlane.setP(-90) # -90 for plane otherwise setTwoSided(1)
            oceanPlane = loader.loadModel(os.path.join(_Datapath,'models','flatcone.egg')) #plane model -.5,.5 corners
            oceanPlane.setPos(10,10,35)
            oceanPlane.setR(90)
            oceanPlane.setTwoSided(1)
#            oceanPlane.setColor(.8,1,1,1)
            
            oceanPlaneTex = loader.loadTexture(os.path.join(_Datapath, _OceanTex[0]))
#            oceanPlane.setTexGen(TextureStage.getDefault(),TexGenAttrib.MEyePosition)
            self.oceanNode.setTexture(oceanPlaneTex)
#            oceanPlane.setTexScale(TextureStage.getDefault(), _OceanTex[1], _OceanTex[2])
            ocMat = Material()
            ocMat.setShininess(1.0) 
            ocMat.setDiffuse(VBase4(1,1,1,1))
            ocMat.setAmbient(VBase4(.8,1,.8,1))
            self.oceanNode.setMaterial(ocMat)
            self.oceanNode.setTransparency(0)
            self.oceanNode.setScale(1,1,1)

            # Try one big rect
#            W = 2000
#            L = 512
#            self.oceanNode.setPos(-W,-W,_Sealevel)
#            self.oceanNode.setScale(2*W+L,2*W+L,1)
            oceanPlane.reparentTo(self.oceanNode)

        if _DoFog:
            self.terraFog = Fog("Fog Name")
            self.terraFog.setColor(_SKYCOLOR_)
#            self.terraFog.setExpDensity(fogPm[0])
            self.terraFog.setLinearRange(fogPm[0],fogPm[1])
            #setLinearFallback(float angle, float onset, float opaque)
#            self.terraFog.setLinearFallback(fogPm[2],fogPm[3],fogPm[4])
#            render.setFog(terraFog)
            self.terraNode.setFog(self.terraFog)
#            self.skynp.setFog(terraFog)
#            self.oceanNode.setFog(self.terraFog)
        else:
            print "NO FOG. Using auto shader"
            render.setShaderAuto()
            
######### TASKS ADDS

#        taskMgr.add(self.updateTera,"TerrainUpdates")
        taskMgr.add(self.updateAvnp,"update Av node")
        taskMgr.add(self.mouseHandler,"mouseHandler")
        taskMgr.add(self.updateCamera,"UpdateCamera")
#        taskMgr.add(self.updateNPCs,'NPC Updates')

#        taskMgr.add(self.moveArm,'pjoint test')
#        initText.destroy()
###############
#        render.analyze()

    def loadMap(self,mapDefName):
        print 'loading map ', mapDefName,'...',
        tileInfo = pickle.load(open(os.path.join(_Datapath,mapDefName+'.mdf'),'rb'))
        tileID = (0,0)        
        HFname,texList,Objects = tileInfo[tileID][0:3]
#        treeLocs, = data[0:2]
#        self.ttMgr = TerrainManager(tileInfo, focus=self.avnp, size=TILE_SIZE, parentNode=self.terraNode, tileScale=_terraScale)      
#        self.objMgr = objectManager(treeLocs, focus=self.avnp, parentNode=self.floralNode, zFunc=self.ttMgr.getElevation)
        self.mapTile = MapTile('mapTile',self.avnp)
        self.mapTile.setPos(tileID[0]*TILE_SIZE[0],tileID[1]*TILE_SIZE[0],0)
        self.mapTile.reparentTo(self.terraNode)                     
        self.mapTile.setGeom(HFname, _terraScale, position=(0,0,0))
        self.mapTile.setTexture(texList)
        for obj in Objects:
#            r = random.randint(0,9)
#            obj[2] = 'resources/models/sampleTree'+str(r)+'.bam'    # DEBUG OVERRIDE TO TEST MODEL
            self.mapTile.addStaticObject(obj) # takes a an individual object for this tile

        for n in range(1):
            self.mapTile.npcs.append( NPC('guy','resources/models/cone.egg',1,self.mapTile) )
        print "done"
        
    def setupSky(self):
        # MAKE A DIFFERENT SETUP DEF IF GOING MODEL PATH
#        npDome = loader.loadModel(os.path.join(_Datapath,_SkyModel))
#        npDome.setHpr(0,90,0)
      
        skyModel = GeoMipTerrain("scene")
        skyModel.setHeightfield(os.path.join(_Datapath,_SkyModel)) # crude to save and read but works for now
        skyModel.setBruteforce(1)
        skyModel.setFocalPoint(self.avnp)
        npDome = skyModel.getRoot()
        skyModel.generate()
        npDome.setTwoSided(1)
        
        tex1 = loader.loadTexture(os.path.join(_Datapath,_SkyTex[0]))
#        tex1.setFormat(Texture.FAlpha)
        tstage1 = TextureStage('clouds')
#        tstage1.setColor(Vec4(1, 1, 1, 1))
        
        npDome.setTexture(tstage1,tex1)
#        npDome.setTexOffset(tstage1,.5,.5)
        npDome.setTexScale(tstage1,_SkyTex[1],_SkyTex[2])
        npDome.setTransparency(TransparencyAttrib.MDual)
        
        sxy = 1000
        self.skynp.setScale(sxy,sxy,1000)
        self.skynp.setPos(-128*sxy,-128*sxy,0)
        npDome.reparentTo(self.skynp)
        
    def setupLights(self):
        self.dlight = DirectionalLight('dlight')
        self.dlight.setColor(VBase4(1, 1, 1, 1))
#        self.slight.getLens().setNearFar(32,128)
#        self.slight.getLens().setFov(90)
#        self.dlight.setShadowCaster(True,16,16,1)
        self.dlnp = render.attachNewNode(self.dlight)
        self.dlnp.setPos(-1000,0,1000)
        self.dlnp.setHpr(-90,-45,0)        
        render.setLight(self.dlnp)
        
        self.alight = AmbientLight('alight')
        self.alight.setColor(VBase4(.1,.1,.1,1))
        self.alnp = render.attachNewNode(self.alight)
#        render.setLight(self.alnp)     
 
    def setupAvatar(self):    
        self.avnp.setPos(_STARTPOS_[0],_STARTPOS_[1],0)  
#        self.avnp.setBin('fixed',45)
#        print self.avnp.getBinName()
        
#        ruler = loader.loadModel(_Datapath + '/models/plane')
#        ruler.setPos(0,-.5,1) # .5 *2scale
#        ruler.setScale(.05,1,2) #2 unit tall board
#        ruler.setTwoSided(1)
#        ruler.reparentTo(self.avnp)

#        self.aVmodel = loader.loadModel(os.path.join(_Datapath,_AVMODEL_))
        self.aVmodel = Actor(os.path.join(_Datapath,_AVMODEL_))
        self.aVmodel.reparentTo(self.avnp)
#        self.armCtrl = self.aVmodel.controlJoint(None,"modelRoot","Armature")
#        print self.aVmodel.listJoints()
        
#        self.aVmodel.setScale(.5,.5,1)
#        self.aVmodel.setScale(1.0/6)
#        self.aVmodel.setZ(1)
#        self.aVmodel.setH(180)
#        self.aVmodel.setColor(.9,1,.9)
        avMat = Material()
        avMat.setShininess(0)
        self.aVmodel.setMaterial(avMat)
           
    def setupKeys(self):
        _KeyMap ={'left':'q','right':'e','strafe_L':'a','strafe_R':'d','wire':'z'}
           
        self.accept(_KeyMap['left'],self.turn,[1])
        self.accept(_KeyMap['left']+"-up",self.turn,[0])
        self.accept(_KeyMap['right'],self.turn,[-1])
        self.accept(_KeyMap['right']+"-up",self.turn,[0])
    
        
        self.accept(_KeyMap['strafe_L'],self.strafe,[-1])
        self.accept(_KeyMap['strafe_L']+"-up",self.strafe,[0])
        self.accept(_KeyMap['strafe_R'],self.strafe,[1])
        self.accept(_KeyMap['strafe_R']+"-up",self.strafe,[0])
        
        self.accept("w",self.walk,[1])
        self.accept("s",self.walk,[-1])
        self.accept("s-up",self.walk,[0])
        self.accept("w-up",self.walk,[0])
        self.accept("r",self.autoWalk) 
        
        self.accept("page_up",self.camPitch,[-1])
        self.accept("page_down",self.camPitch,[1])
        self.accept("page_up-up",self.camPitch,[0])
        self.accept("page_down-up",self.camPitch,[0])
        self.accept("arrow_left",self.camHead,[-1])
        self.accept("arrow_right",self.camHead,[1])
        self.accept("arrow_left-up",self.camHead,[0])
        self.accept("arrow_right-up",self.camHead,[0])
    
        self.accept("arrow_down",self.camZoom,[1])        
        self.accept("arrow_up",self.camZoom,[-1])
        self.accept("arrow_down-up",self.camZoom,[0])
        self.accept("arrow_up-up",self.camZoom,[0])
    
        self.accept("mouse1",self.mbutton,[1,1])
        self.accept("mouse1-up",self.mbutton,[1,0])
        self.accept("mouse2",self.mbutton,[2,1])
        self.accept("mouse2-up",self.mbutton,[2,0])
        self.accept("mouse3",self.mbutton,[3,1])
        self.accept("mouse3-up",self.mbutton,[3,0])
        self.accept("wheel_up",self.mbutton,[4,-1])
        self.accept("wheel_up-up",self.mbutton,[4,0])
        self.accept("wheel_down",self.mbutton,[4,1])
        self.accept("wheel_down-up",self.mbutton,[4,0])
        self.accept(_KeyMap['wire'],self.toggleWireframe)
        self.accept("escape",sys.exit)

    def mbutton(self,b,s): 
        if b == 4: # add up mouse wheel clicks
            self.mbState[b-1] += s
        else:
            self.mbState[b-1] = s
#        print self.mbState
        # ADD A L+R BUTTON WALK 
                   
    def camPitch(self,dp): self.Kpitch = dp       
    def camHead(self,dp): self.Ktheta = dp
    def camZoom(self,dp): self.Kzoom = dp
        
    def strafe(self,dp): self.Kstrafe = dp
    def turn(self,dp): self.Kturn = dp
    def walk(self,dp): self.Kwalk = dp    
    def autoWalk(self):
        if self.Kwalk == 0:
            self.Kwalk = 1
        else:
            self.Kwalk = 0  
       
    def mouseHandler(self,task):
       
        if base.mouseWatcherNode.hasMouse():
            self.mousePos_old = self.mousePos
            self.mousePos = [base.mouseWatcherNode.getMouseX(), \
            base.mouseWatcherNode.getMouseY()]
        dt = globalClock.getDt()
        if self.mbState[0] and not self.mbState[2]:
            self.camVector[1] += -_TURNRATE_*(self.mousePos[0] - self.mousePos_old[0])
            self.camVector[2] += -_TURNRATE_*(self.mousePos[1] - self.mousePos_old[1])
        if self.mbState[2] and not self.mbState[0]:  # mouse Steer av
            self.avnp.setH(self.avnp,-2*_TURNRATE_*(self.mousePos[0] - self.mousePos_old[0]))
            self.camVector[2] += -_TURNRATE_*(self.mousePos[1] - self.mousePos_old[1])
        if self.mbState[2] and self.mbState[0]:  # mouse Steer av
            self.Kwalk = 1
            self.avnp.setH(self.avnp,-2*_TURNRATE_*(self.mousePos[0] - self.mousePos_old[0]))
            self.camVector[2] += -_TURNRATE_*(self.mousePos[1] - self.mousePos_old[1])
        
    #    print avHandler.mbState[3]
        mbWheel = self.mbState[3]
        if mbWheel:
            self.camVector[0] += 5*(sign(mbWheel))*dt
            self.mbState[3] -= 3*sign(mbWheel)*dt
            if abs(self.mbState[3]) < .15: self.mbState[3] = 0 # anti-jitter on cam
    
        return task.cont

  
    def updateAvnp(self,task):
        dt = globalClock.getDt()
        self.avnp.setPos(self.avnp,_WALKRATE_*self.Kstrafe*dt,_WALKRATE_*self.Kwalk*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
        self.avnp.setH(self.avnp,_TURNRATE_*self.Kturn*dt) #key input steer
        x,y,z = self.avnp.getPos()

# TODO: REMOVE THIS HACK FOR GET Z! 
# just make Avatar another object in the tile. then object can get it's own Z from tile object
#        curIJ = self.ttMgr.curIJ
#        curTile = self.ttMgr.tiles[curIJ]
#        # PROBLEM HERE IS THAT THIS x,y are GLOBAL! NOT A TILES LOCAL...calc locals below
#        lcx = x - curIJ[0]*TILE_SIZE[0]
#        lcy = y - curIJ[1]*TILE_SIZE[1]
        self.avnp.setZ(self.mapTile.terGeom.getElevation(x,y))
        hdg = self.avnp.getH()
        self.textObject.setText(str((int(x),int(y),int(z),int(hdg))))
        return task.cont   
    
    
    def updateCamera(self,task):
        epsilon = .333
        aim = Point3(0,.333,2)
        dt = globalClock.getDt() # to stay time based, not frame based
        self.camVector[0] += 8*(self.Kzoom)*dt
        self.camVector[0] = max(_MINCAMDIST_,min(_MaxCamDist,self.camVector[0]))
        self.camVector[1] += .5*_TURNRATE_*self.Ktheta*dt
        self.camVector[2] += .5*_TURNRATE_*self.Kpitch*dt
        
        phi = max(-pi/2,min(pi/2,self.camVector[2]*pi/180))
        theta = self.camVector[1]*pi/180 # orbit angle un    d this way
        radius = self.camVector[0]
        camera.setX(radius*cos(phi)*sin(theta))
        camera.setY(-radius*cos(phi)*cos(theta))
        camera.setZ(radius*sin(phi)+aim[2])
        
        # Keep Camera above terrain
# TODO: Object occlusion with camera intersection
        
        cx,cy,cz = camera.getPos(self.terraNode)
#        print "localframe: ",app.camera.getPos()
#        print "worldframe: ",app.camera.getPos(terrainRoot)
#        print "terra  WF: ", cx,cy,terrain.getElevation(cx,cy)
# TODO: REMOVE THIS HACK FOR GET Z! 
# just make Avatar another object in the tile. then object can get it's own Z from tile object
#        curIJ = self.ttMgr.curIJ
#        curTile = self.ttMgr.tiles[curIJ]
#        # PROBLEM HERE IS THAT THIS x,y are GLOBAL! NOT A TILES LOCAL...calc locals below
#        lcx = cx - curIJ[0]*TILE_SIZE[0]
#        lcy = cy - curIJ[1]*TILE_SIZE[1]

        terZ = self.mapTile.terGeom.getElevation(cx,cy) # what is terrain elevation at new camera pos
        if cz <= terZ+epsilon:
            camera.setZ(self.terraNode,terZ+epsilon)
#            print cx,cy,cz, terZ
        camera.lookAt(self.avnp,aim) # look at the avatar nodepath
#        camera.lookAt(self.sun.model)

        if _DoFog: self.terraFog.setColor(base.getBackgroundColor()) # cheesy place to update this for now...
        
    #    print camVector                   
        return task.cont
  
    def moveArm(self,task):
        t = task.time/3.0
        self.armCtrl.setHpr(0,90*sin(2*pi*t),0)
        return task.cont
    

    # NETWORK DATAGRAM PROCESSING
    def ProcessData(self,datagram):
        print time.ctime(),' <recv> ',
        I = DatagramIterator(datagram)
        msgID = I.getInt32()
        data = rencode.loads(I.getString()) # data matching msgID
        print msgID,data
#        for iNpc in self.npc:
#            if I.getRemainingSize() > 0:
#                x=I.getFloat32()
#                y=I.getFloat32()
#                z=I.getFloat32() # read it out because it is there
#                h=I.getFloat32()
#                p=I.getFloat32()
#                r=I.getFloat32() # read it out because it is there
#                s=I.getFloat32()
#                iNpc.setPos(x,y,self.ttMgr.tiles[self.ttMgr.curIJ].terGeom.getElevation(x,y))
#                iNpc.setHpr(h,p,r)
#                iNpc.speed = s
        print "</>"
        
def fakeAIchange(self,ttime):
    Q = Quat()
    newH = random.gauss(-180,180)
    Q.setHpr((newH,0,0))
    # GET CUR VELOC VECTOR to MULTUPLE WITH Quat
    self.speed = 3*abs(random.gauss(0,.33333))
    self.updateCommandsBuffer(ttime,[self.getPos(),Q.getForward()*self.speed,Vec3(0,0,0)])
    self.nextUpdate = ttime + 10*random.random() # randomize when to update next
    # fake some AI motion
    for iNpc in tile.npcs:
        if task.time > iNpc.nextUpdate:         # change direction and heading every so often
            iNpc.makeChange(task.time)

W = TileClient()
W.run()
print "closing connection to server"
W.disconnect()
#pycallgraph.make_dot_graph('test.png')