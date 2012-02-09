##!/usr/local/bin/python

# SETUP SOME PATH's
import sys

_Datapath = "resources"

import os.path
from math import sin,cos,pi
from numpy import sign
import time
     
from direct.showbase.ShowBase import ShowBase
#from direct.showbase.DirectObject import DirectObject
#from direct.actor.Actor import Actor
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText

from pandac.PandaModules import loadPrcFileData
#loadPrcFileData("", "want-directtools #t")
#loadPrcFileData("", "want-tk #t")
loadPrcFileData( '', 'sync-video 0' ) 

from CelestialBody import CelestialBody
from network.client import NetClient
from network.rencode import *
from server import _mapName
from CONSTANTS import *
from TileClient import TileClient, SERVER_IP

# RENDERING OPTIONS #
_DoLights = 1
_DoFog = 1
_ShowSky = 1        # put up the sky dome
_ShowClouds = 0
_ShowOcean = 0

# COLORS
_DARKBLUE_ = VBase4(.0,.4,.7,1)
_LIGHTBLUE_ = VBase4(.3,.7,1,1)
_BLACK_ = VBase4(0,0,0,1)
_WHITE_= VBase4(1,1,1,1)


# SKY PARMS
_SkyTex = ('textures/sky0.png',1,1)
#_SkyTex = ('textures/skyTexPolar.png',1,1)
_SkyModel = 'models/wintersky.egg'
_SKYCOLOR_ = _DARKBLUE_

_OceanTex = ('textures/oceanTex2.png',1,1)
_Sealevel = 2

_Suntex = 'textures/blueSun.png'


fogPm = (192,256,45,250,500) # last 3 params for linfalloff - not used atm

# AVATAR SETTINGS
_MINCAMDIST_ = 1
_MaxCamDist = 20
 
PStatClient.connect()
#import pycallgraph
#pycallgraph.start_trace()

MY_ID = 'fahkohr'
       
class World(ShowBase,NetClient):
    mbState = [0,0,0,0] # 3 mouse buttons + wheel, 1 on down, 0 on up
    mousePos = [0,0]

    ## SOME CAM STUFF
    camDist,camHdg,camPitch = [10,0,15]    # [distance, heading, pitch ]
    mousePos_old = mousePos
        
    def __init__(self,local=False):
        ShowBase.__init__(self)
        NetClient.__init__(self)
        self.connect(SERVER_IP)
        self.write(int(25),MY_ID,self.myConnection) # Tell Server Who we are
        
        self.setBackgroundColor(_SKYCOLOR_)
        self.setFrameRateMeter(1)
        render.setAntialias(AntialiasAttrib.MAuto)
        render.setShaderAuto()

        self.terraNode = render.attachNewNode('Terrain Node') 
        self.terraNode.flattenStrong()
        self.skynp = render.attachNewNode("SkyDome")   

        self.client = TileClient(SERVER_IP,'Tile001', MY_ID, _mapName)
        self.client.np.reparentTo(self.terraNode)
        
        cnodePath = self.client.avnp.attachNewNode(CollisionNode('cnode'))
        cnodePath.node().addSolid(CollisionSphere(0, 0, 1.25, .25))
        cnodePath.node().addSolid(CollisionSphere(0, 0, .2, .25))
        cnodePath.show()
        self.pusher = CollisionHandlerPusher()
        self.pusher.addCollider(cnodePath, self.client.avnp)
        
        base.cTrav = CollisionTraverser('traverser name')
        base.cTrav.addCollider(cnodePath, self.pusher)
        
        self.mapTile = self.client.mapTile
        self.camera.reparentTo(self.client.avnp)
        self._setupKeys()
        self.tlast = time.time()
        
        self.textObject = OnscreenText(text = '', pos = (-0.9, 0.9), scale = 0.07, fg = (1,1,1,1))       
######### TASKS ADDS
        taskMgr.add(self.calcTick,"updatePlayer")
        taskMgr.add(self.mouseHandler,"mouseHandler")
        taskMgr.add(self.updateCamera,"UpdateCamera")
        taskMgr.doMethodLater(SNAP_INTERVAL,self.updateSnap,'discrete_tick')
        taskMgr.doMethodLater(SERVER_TICK,self.calcTick,'calc_tick')

#        taskMgr.add(self.moveArm,'pjoint test')
###############
   
        if _DoLights: self._setupLights()        
        if _ShowSky: self._setupSky() # must occur after setupAvatar    
                
        self.sun = CelestialBody(self.render, self.client.avnp, './resources/models/plane', \
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
#        self.moon = CelestialBody(self.render,self.client.avnp, './resources/models/plane', \
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
            
#        render.analyze()


    def _setupSky(self):
        # MAKE A DIFFERENT SETUP DEF IF GOING MODEL PATH
#        npDome = loader.loadModel(os.path.join(_Datapath,_SkyModel))
#        npDome.setHpr(0,90,0)
      
#        skyModel = GeoMipTerrain("scene")
#        skyModel.setHeightfield(os.path.join(_Datapath,_SkyModel)) # crude to save and read but works for now
#        skyModel.setBruteforce(1)
#        skyModel.setFocalPoint(self.client.avnp)
#        npDome = skyModel.getRoot()
#        skyModel.generate()
        npDome = loader.loadModel(os.path.join(_Datapath,_SkyModel))
        npDome.setTwoSided(1)
        npDome.reparentTo(self.skynp)
        
#        tex1 = loader.loadTexture(os.path.join(_Datapath,_SkyTex[0]))
#        tex1.setFormat(Texture.FAlpha)
#        tstage1 = TextureStage('clouds')
#        tstage1.setColor(Vec4(1, 1, 1, 1))
        
#        npDome.setTexture(tstage1,tex1)
#        npDome.setTexOffset(tstage1,.5,.5)
#        npDome.setTexScale(tstage1,_SkyTex[1],_SkyTex[2])
#        npDome.setTransparency(TransparencyAttrib.MDual)
        
#        sxy = 10
#        self.skynp.setScale(sxy,sxy,1000)
#        self.skynp.setPos(-128*sxy,-128*sxy,0)
        
    def _setupLights(self):
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
            
    def _setupKeys(self):
        self.controls = {"turn":0, "walk":0, "autoWalk":0,"strafe":0,'camZoom':0,\
        'camHead':0,'camPitch':0, "mouseTurn":0, "mousePos":[0,0]}

        _KeyMap ={'left':'q','right':'e','strafe_L':'a','strafe_R':'d','wire':'z'}
           
        self.accept(_KeyMap['left'],self._setControls,["turn",1])
        self.accept(_KeyMap['left']+"-up",self._setControls,["turn",0])
        self.accept(_KeyMap['right'],self._setControls,["turn",-1])
        self.accept(_KeyMap['right']+"-up",self._setControls,["turn",0])
    
        
        self.accept(_KeyMap['strafe_L'],self._setControls,["strafe",-1])
        self.accept(_KeyMap['strafe_L']+"-up",self._setControls,["strafe",0])
        self.accept(_KeyMap['strafe_R'],self._setControls,["strafe",1])
        self.accept(_KeyMap['strafe_R']+"-up",self._setControls,["strafe",0])
        
        self.accept("w",self._setControls,["walk",1])
        self.accept("s",self._setControls,["walk",-1])
        self.accept("s-up",self._setControls,["walk",0])
        self.accept("w-up",self._setControls,["walk",0])
        self.accept("r",self._setControls,["autoWalk",1]) 
        
        self.accept("page_up",self._setControls,["camPitch",-1])
        self.accept("page_down",self._setControls,["camPitch",1])
        self.accept("page_up-up",self._setControls,["camPitch",0])
        self.accept("page_down-up",self._setControls,["camPitch",0])
        self.accept("arrow_left",self._setControls,["camHead",-1])
        self.accept("arrow_right",self._setControls,["camHead",1])
        self.accept("arrow_left-up",self._setControls,["camHead",0])
        self.accept("arrow_right-up",self._setControls,["camHead",0])
    
        self.accept("arrow_down",self._setControls,["camZoom",1])        
        self.accept("arrow_up",self._setControls,["camZoom",-1])
        self.accept("arrow_down-up",self._setControls,["camZoom",0])
        self.accept("arrow_up-up",self._setControls,["camZoom",0])
    
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

    def _setControls(self,key,value):
            self.controls[key] = value
            if key == 'autoWalk':
                if self.controls["walk"] == 0:
                    self.controls["walk"] = 1
                else:
                    self.controls["walk"] = 0  
        
    def mbutton(self,b,s): 
        if b == 4: # add up mouse wheel clicks
            self.mbState[b-1] += s
        else:
            self.mbState[b-1] = s                   
       
    def mouseHandler(self,task):
       
        if base.mouseWatcherNode.hasMouse():
            self.mousePos_old = self.mousePos
            self.mousePos = [base.mouseWatcherNode.getMouseX(), \
            base.mouseWatcherNode.getMouseY()]
        dt = globalClock.getDt()
        if self.mbState[0] and not self.mbState[2]:
            self.camHdg += -TURN_RATE*(self.mousePos[0] - self.mousePos_old[0])
            self.camPitch += -TURN_RATE*(self.mousePos[1] - self.mousePos_old[1])
        if self.mbState[2] and not self.mbState[0]:  # mouse Steer av
            self.controls['mouseTurn'] = -2*TURN_RATE*(self.mousePos[0] - self.mousePos_old[0])
            self.camPitch += -TURN_RATE*(self.mousePos[1] - self.mousePos_old[1])

        mbWheel = self.mbState[3]
        if mbWheel:
            self.camDist += 5*(sign(mbWheel))*dt
            self.mbState[3] -= 3*sign(mbWheel)*dt
            if abs(self.mbState[3]) < .15: self.mbState[3] = 0 # anti-jitter on cam
    
        return task.cont    

    def updateCamera(self,task):
        """There is probably a whole lot better ways of doing this...one of the 
        first things I worked on...but it works"""
        
        epsilon = .333 # Minimum distance above the terrain to float the camera
        aim = Point3(0,.333,2)
        dt = globalClock.getDt() # to stay time based, not frame based
        self.camDist += 8*(self.controls['camZoom'])*dt
        self.camDist = max(_MINCAMDIST_,min(_MaxCamDist,self.camDist))
        self.camHdg += .5*TURN_RATE*self.controls['camHead']*dt
        self.camPitch += .5*TURN_RATE*self.controls['camPitch']*dt
        
        phi = max(-pi/2,min(pi/2,self.camPitch*pi/180))
        theta = self.camHdg*pi/180 # orbit angle un    d this way
        camera.setX(self.camDist*cos(phi)*sin(theta))
        camera.setY(-self.camDist*cos(phi)*cos(theta))
        camera.setZ(self.camDist*sin(phi)+aim[2])
        
# TODO: Object occlusion with camera intersection
        # Keep Camera above terrain        
        cx,cy,cz = camera.getPos(self.terraNode)
        terZ = self.mapTile.terGeom.getElevation(cx,cy) # what is terrain elevation at new camera pos
        if cz <= terZ+epsilon:
            camera.setZ(self.terraNode,terZ+epsilon)
        camera.lookAt(self.client.avnp,aim) # look at the avatar nodepath
#        camera.lookAt(self.sun.model)

        if _DoFog: self.terraFog.setColor(base.getBackgroundColor()) # cheesy place to update this for now...       
        x,y,z = self.client.avnp.getPos()
        h,p,r = self.client.avnp.getHpr()
        self.textObject.setText(str((int(x),int(y),int(z),int(h))))

        return task.cont

    def calcTick(self,task):
#        dt = globalClock.getDt()
        self.write(int(26),self.controls,self.myConnection)

        tnow = time.time()
        dt = tnow - self.tlast
        self.client.avnp.setPos(self.client.avnp,WALK_RATE*self.controls['strafe']*dt,WALK_RATE*self.controls['walk']*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
        self.client.avnp.setH(self.client.avnp,self.controls['mouseTurn'] + TURN_RATE*self.controls['turn']*dt) #key input steer
        x,y,z = self.client.avnp.getPos()
        self.client.avnp.setZ(self.mapTile.terGeom.getElevation(x,y))
        self.tlast = tnow
        return task.again

    def updateSnap(self,task):
        self.client.updateSnap()
        return task.again

    def moveArm(self,task):
        t = task.time/3.0
        self.armCtrl.setHpr(0,90*sin(2*pi*t),0)
        return task.cont
    

    # NETWORK DATAGRAM PROCESSING
#    def ProcessData(self,datagram):
#        print time.ctime(),' <recv> '
#        I = DatagramIterator(datagram)
#        msgID = I.getInt32()
#        data = rencode.loads(I.getString()) # data matching msgID
 
W = World()
W.run()
print "closing connection to server"
W.disconnect()
#pycallgraph.make_dot_graph('test.png')