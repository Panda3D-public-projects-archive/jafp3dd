##!/usr/local/bin/python

# SETUP SOME PATH's
import sys

_DATAPATH_ = "resources"

import os.path
from math import *
from numpy import sign
import time
import pickle
     
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
#from direct.showbase.DirectObject import DirectObject
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText

from panda3d.core import loadPrcFileData
loadPrcFileData( '', 'sync-video 0' ) 

from CelestialBody import CelestialBody
from tileManager import *
from network.client import netClient


# RENDERING OPTIONS #
_DoLights = 1
_DoFog = 1
_ShowOcean = 0
_ShowSky = 1        # put up the sky dome
_ShowClouds = 1

# COLORS
_DARKBLUE_ = VBase4(.0,.4,.7,1)
_LIGHTBLUE_ = VBase4(.3,.7,1,1)
_BLACK_ = VBase4(0,0,0,1)
_WHITE_= VBase4(1,1,1,1)


# SKY PARMS
#_SkyTex = ('textures/sky0.png',1,1)
_SkyTex = ('textures/skyTexPolar.png',1,1)
_SkyModel = 'textures/curved.png'
_SKYCOLOR_ = _LIGHTBLUE_

_OceanTex = ('textures/oceanTex2.png',1,1)
_Sealevel = 2

_Suntex = 'textures/blueSun.png'


fogPm = (96,128,45,250,500) # last 3 params for linfalloff - not used atm

# AVATAR SETTINGS
_AVMODEL_ = os.path.join('models','MrStix.x')
_STARTPOS_ = (64,64)
_TURNRATE_ = 120    # Degrees per second
_WALKRATE_ = 4
_MINCAMDIST_ = 1
_MaxCamDist = 20
 
# TERRAIN SETTINGS
_terraScale = (1,1,60) # xy scaling not working right as of 12-10-11. prob the LOD impacts
_mapName='map2/map2'
_templ = '%s_%s.x%dy%d.%s' #terrain image name template
_treePath = 'map1/treeList.dat'

PStatClient.connect()
#import pycallgraph
#pycallgraph.start_trace()

class NPC(NodePath):
    def __init__(self,nodeName,modelName,modelScale,parentNode):
        NodePath.__init__(self,nodeName)
        self.commandsBuffer = dict({0:[Vec3(0,0,0),Vec3(0,0,0),Vec3(0,0,0),Vec3(0,0,0)]}) # {time:[list of commands]}
        self.speed = 0
        self.nextUpdate = 0
        self.color = (VBase4(random.random(),random.random(),random.random(),1))
        self.model = loader.loadModel(modelName)
        self.model.reparentTo(self)
        self.setScale(modelScale)
        self.model.setColor(self.color)
        self.reparentTo(parentNode)
        
    def calcPos(self,timenow):
        # get time just previous to time now in buffer
        ts = self.commandsBuffer.keys()
        ix = ([x<=timenow for x in ts]).index(True) # give me the index first entry in the dict that is < timenow
        dT = timenow-ts[ix]
        cmds = self.commandsBuffer[ts[ix]] # give me the command/state associated with time in [ix]
        # store commands as [Point3:pos,Vect3:vel,Vec3:accel,Vec3:Hpr] 
        # velocity direction can be different than the orientation of the model
        pos = cmds[0] + cmds[1]*dT + 0.5*cmds[2]*dT**2
        return pos
    
    def updateCommandsBuffer(self,time,commands):
        if time < self.commandsBuffer.key()[-1]: # adding a time before the last time in the list
        #assuming here that time keys are put in sequential; no sort needed
            raise Exception('command update time before the latest update time!')
        else:
            self.commandsBuffer.update({time:commands})
    
    def makeChange(self,ttime):
        self.speed = 1*abs(random.gauss(0,.33333))
        newH = random.gauss(0,60)
        self.setH(self,newH) #key input steer
        self.nextUpdate = ttime + random.randint(1,10) # randomize when to update next

        
class World(ShowBase,netClient):
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
        netClient.__init__(self)
        self.setBackgroundColor(_SKYCOLOR_)
        self.setFrameRateMeter(1)
        #app.disableMouse()
        render.setAntialias(AntialiasAttrib.MAuto)
        render.setShaderAuto()
        
        self.connect() # local loop if no address
        
        self.terraNode = render.attachNewNode('Terrain Node') 
        self.terraNode.flattenStrong()
        self.avnp = render.attachNewNode("Avatar")
        self.skynp = render.attachNewNode("SkyDome")               
        self.floralNode = self.terraNode.attachNewNode('TreesAndFlowers') # child to inherit terrain fog
        self.camera.reparentTo(self.avnp)
        self.camera.setY(-10)
        self.camera.lookAt(self.avnp)
        self.textObject = OnscreenText(text = str(self.avnp.getPos()), pos = (-0.9, 0.9), scale = 0.07, fg = (1,1,1,1))       
        
        print "Getting Tree Loc's"       
        treefile = open(os.path.join(_DATAPATH_,_treePath))        
        treeLocs = pickle.load(treefile)
        treefile.close()
        tileInfo = enumerateMapTiles(_mapName,16)              
        self.ttMgr = terrainManager(tileInfo, parentNode=self.terraNode, tileScale=_terraScale, \
        focusNode=self.avnp)
        
        self.objMgr = objectManager(treeLocs, parentNode=self.floralNode, focusNode=self.avnp,\
        zFunc=self.ttMgr.getElevation)
        
        self.npc = []
        for n in range(10):
            self.npc.append( NPC('thisguy','resources/models/cone.egg',1,self.terraNode) )
            self.npc[n].setPos(70,70,0)
        
        self.initTime = time.time()
        self.worldTime = self.initTime
        
        if _DoLights: self.setupLights()
#        initText.setText("setting key mapping...")        
        self.setupKeys()
#        initText.setText("Create an Avatar...")
        self.setupAvatar()     
        
        if _ShowSky: 
#            initText.setText("We need a sky!...")            
            self.setupSky() # must occur after setupAvatar    
       
#        initText.setText("The sun, the moon, and someday the stars...")
        self.sun = CelestialBody(self.render, self.avnp, './resources/models/plane', \
        './resources/textures/blueSun.png',radius=4000,Fov=7,phase=pi/9)
        self.sun.period = 3600
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
#            initText.setText("Filling the swimming pool...")
            self.oceanNode = render.attachNewNode('ocean plane')        
#            oceanPlane = loader.loadModel(os.path.join(_DATAPATH_,'models','plane')) #plane model -.5,.5 corners
#            oceanPlane.setPos(.5,.5,0)
#            oceanPlane.setP(-90) # -90 for plane otherwise setTwoSided(1)
            oceanPlane = loader.loadModel(os.path.join(_DATAPATH_,'models','flatcone.egg')) #plane model -.5,.5 corners
            oceanPlane.setPos(0,0,-1)            
            oceanPlane.setTwoSided(1)
#            oceanPlane.setColor(.8,1,1,1)
            
            oceanPlaneTex = loader.loadTexture(os.path.join(_DATAPATH_, _OceanTex[0]))
#            oceanPlane.setTexGen(TextureStage.getDefault(),TexGenAttrib.MEyePosition)
#            oceanPlane.setTexture(oceanPlaneTex)
#            oceanPlane.setTexScale(TextureStage.getDefault(), _OceanTex[1], _OceanTex[2])
#            ocMat = Material()
#            ocMat.setShininess(1.0) 
#            ocMat.setDiffuse(VBase4(1,1,1,1))
#            ocMat.setAmbient(VBase4(.8,1,.8,1))
#            self.oceanNode.setMaterial(ocMat)
            self.oceanNode.setTransparency(0)
            self.oceanNode.setScale(1000,100,1)

            # Try one big rect
#            W = 2000
#            L = 512
#            self.oceanNode.setPos(-W,-W,_Sealevel)
#            self.oceanNode.setScale(2*W+L,2*W+L,1)
            oceanPlane.reparentTo(self.oceanNode)

        if _DoFog:
#            initText.setText("A hazy day...")
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
            print "Using auto shader"
            render.setShaderAuto()
            
######### TASKS ADDS

#        taskMgr.add(self.updateTera,"TerrainUpdates")
        taskMgr.add(self.updateAvnp,"update Av node")
        taskMgr.add(self.mouseHandler,"mouseHandler")
        taskMgr.add(self.updateCamera,"UpdateCamera")
        taskMgr.setupTaskChain('TileUpdates',numThreads=16,threadPriority=2,frameBudget=0.01,frameSync=True)
        taskMgr.add(self.ttMgr.updateTask,'TileManagerUpdates',taskChain='TileUpdates')
        taskMgr.add(self.objMgr.updateTask,'FloraUpdates',taskChain='TileUpdates')
        taskMgr.add(self.updateNPCs,'NPC Updates')

#        taskMgr.add(self.moveArm,'pjoint test')
#        initText.destroy()
###############
#        render.analyze()
        
    def setupSky(self):
        # MAKE A DIFFERENT SETUP DEF IF GOING MODEL PATH
#        npDome = loader.loadModel(os.path.join(_DATAPATH_,_SkyModel))
#        npDome.setHpr(0,90,0)
      
        skyModel = GeoMipTerrain("scene")
        skyModel.setHeightfield(os.path.join(_DATAPATH_,_SkyModel)) # crude to save and read but works for now
        skyModel.setBruteforce(1)
        skyModel.setFocalPoint(self.avnp)
        npDome = skyModel.getRoot()
        skyModel.generate()
        npDome.setTwoSided(1)
        
        tex1 = loader.loadTexture(os.path.join(_DATAPATH_,_SkyTex[0]))
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
        self.dlight.setColor(VBase4(.5, .5, .5, 1))
#        self.dlight.setShadowCaster(True,512,512)        
        self.dlnp = render.attachNewNode(self.dlight)
        self.dlnp.setHpr(-90,-15,0)        
        render.setLight(self.dlnp)
        
        self.alight = AmbientLight('alight')
        self.alight.setColor(VBase4(.1,.1,.1,1))
        self.alnp = render.attachNewNode(self.alight)
#        render.setLight(self.alnp)     
 
    def setupAvatar(self):    
        self.avnp.setPos(_STARTPOS_[0],_STARTPOS_[1],0)  
#        self.avnp.setBin('fixed',45)
#        print self.avnp.getBinName()
        
#        ruler = loader.loadModel(_DATAPATH_ + '/models/plane')
#        ruler.setPos(0,-.5,1) # .5 *2scale
#        ruler.setScale(.05,1,2) #2 unit tall board
#        ruler.setTwoSided(1)
#        ruler.reparentTo(self.avnp)

#        self.aVmodel = loader.loadModel(os.path.join(_DATAPATH_,_AVMODEL_))
        self.aVmodel = Actor(os.path.join(_DATAPATH_,_AVMODEL_))
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
#        (xp,yp,zp) = self.ijTile(x,y).root.getRelativePoint(self.avnp,(x,y,z))

        hdg = self.avnp.getH()
        self.avnp.setZ(self.ttMgr.getElevation((x,y)))
        # POSSIBLE PERFOMANCE ISSUE HERE. Couldget the current tile once and only call a new one at boundary
        
        self.ttMgr.updatePos(self.avnp.getPos())
#        self.objMgr.curIJ = self.ttMgr.curIJ # sync terrain manager loc and obj mgr

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
        # TO DO: Object occlusion with camera intersection
#        zmin = self.avnp.getZ() + epsilon
#        if camera.getZ() < zmin: camera.setZ(zmin)
        
        cx,cy,cz = camera.getPos(self.terraNode)
#        print "localframe: ",app.camera.getPos()
#        print "worldframe: ",app.camera.getPos(terrainRoot)
#        print "terra  WF: ", cx,cy,terrain.getElevation(cx,cy)
        terZ = self.ttMgr.getElevation((cx,cy)) # what is terrain elevation at new camera pos
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
    
    def updateNPCs(self,task):
        dt = globalClock.getDt()
        for iNpc in self.npc:
            if task.time > iNpc.nextUpdate:         # change direction and heading every so often
                iNpc.makeChange(task.time)
                self.write('time')
            iNpc.setPos(iNpc,0,iNpc.speed*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
            x,y,z = iNpc.getPos()
            iNpc.setZ(self.ttMgr.getElevation((x,y)))

        return task.cont   

    # NETWORK DATAGRAM PROCESSING
    def ProcessData(self,datagram):
        print time.ctime(),' <recv> ',
        I = DatagramIterator(datagram)
        for iNpc in self.npc:
            if I.getRemainingSize() > 0:
                x=I.getFloat32()
                y=I.getFloat32()
                z=I.getFloat32() # read it out because it is there
                h=I.getFloat32()
                p=I.getFloat32()
                r=I.getFloat32() # read it out because it is there
                s=I.getFloat32()
                iNpc.setPos(x,y,self.ttMgr.getElevation((x,y)))
                iNpc.setHpr(h,p,r)
                iNpc.speed = s
        print "</>"
        
def enumerateMapTiles(dirName,N):
    # map tiles must be saved in the format (dirName).hmXY.png 
    # with a matching texture (dirName).txXY.png
    dirName = os.path.join(_DATAPATH_,dirName)
    tileList = {}
    for nx in range(N):
        for ny in range(N):
            tileList.update({(nx,ny):(_templ%(dirName,'HM',nx,ny,'png'), _templ%(dirName,'TX',nx,ny,'png'))})
    return tileList

#
## NOTES
## OPTIMIZE CAMERA LOOK POINT
## OPTIMIZE SKY DIMENSIONS AND TEX - (move to cubemap someday...)
#
#print """TODO: 
#-good grass tex 
#-plant/clutter bmps 
#-Mip Levels on terrain tex's to reduce far patterning
#-fog color by sky color dynamic"""

W = World()
W.run()
print "closing connection to server"
W.disconnect()
#pycallgraph.make_dot_graph('test.png')