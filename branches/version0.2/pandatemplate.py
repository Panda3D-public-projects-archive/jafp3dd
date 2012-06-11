
# SETUP SOME PATH's
from sys import path
path.append('c:\Panda3D-1.7.2')
path.append('c:\Panda3D-1.7.2\\bin');
_DATAPATH_ = "./resources"

from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
from math import sin,cos,pi
from numpy import sign

import sys, os

_TURNRATE_ = 90    # Degrees per second
_WALKRATE_ = 30
_MINCAMDIST_ = .333

   
class World(ShowBase):
    Kturn = 0
    Kwalk = 0
    Kstrafe = 0
    Kzoom = 0
    Kpitch = 0
    Ktheta = 0
    mbState = [0,0,0,0] # 3 mouse buttons + wheel, 1 down, 0 on up

    ## SOME CAM STUFF
    camVector = [10,0,10]    # [distance, heading, pitch ]
    mousePos = [0,0]
    mousePos_old = mousePos

    def __init__(self):
        ShowBase.__init__(self)
        self.setFrameRateMeter(1)
        #app.disableMouse()
        self.setupModels()
        self.setupLights()
        self.setupKeys()
        taskMgr.add(self.updateAvnp,'Move Avatar Node')
        taskMgr.add(self.updateCamera,'Adjust Camera')
        taskMgr.add(self.mouseHandler,'Mouse Manager')
        
    def setupModels(self):
        self.avnp = render.attachNewNode('AVNP')
        camera.reparentTo(self.avnp)
        self.textObject = OnscreenText(text = str(self.avnp.getPos()), pos = (-0.9, 0.9), scale = 0.07, fg = (1,1,1,1))       

        
    def setupLights(self):
        self.render.setShaderAuto()
        self.alight = AmbientLight('alight')
        self.alight.setColor(VBase4(.1,.1,.1,1))
        self.alnp = self.render.attachNewNode(self.alight)
        render.setLight(self.alnp)

        self.dlight = DirectionalLight('dlight')
        self.dlight.setColor(VBase4(.8,.8,.8,1))
        self.dlnp = self.render.attachNewNode(self.dlight)
#        render.setLight(self.dlnp)       

        self.slight = Spotlight('slight')
        self.slight.setColor(VBase4(1,0,0,1))
        self.slnp = self.render.attachNewNode(self.slight)
        self.slnp.setPos(0,0,10)
        render.setLight(self.slnp)
        
#        self.slnp.lookAt(self.model)
              
      
    def setupKeys(self):          
        self.accept("a",self.turn,[1])
        self.accept("a-up",self.turn,[0])
        self.accept("d",self.turn,[-1])
        self.accept("d-up",self.turn,[0])
    
        
        self.accept("q",self.strafe,[-1])
        self.accept("q-up",self.strafe,[0])
        self.accept("e",self.strafe,[1])
        self.accept("e-up",self.strafe,[0])
        
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
            self.camVector[0] += 15*(sign(mbWheel))*dt
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
#        self.avnp.setZ(self.ijTile(x,y).getElevation(x,y))
        
        self.textObject.setText(str((int(x),int(y),int(z),int(hdg))))
        return task.cont   
    
    
    def updateCamera(self,task):
        epsilon = 1
        dt = globalClock.getDt() # to stay time based, not frame based
        self.camVector[0] += 15*(self.Kzoom)*dt
        self.camVector[1] += .5*_TURNRATE_*self.Ktheta*dt
        self.camVector[2] += .5*_TURNRATE_*self.Kpitch*dt
        
        phi = max(-pi/2,min(pi/2,self.camVector[2]*pi/180))
        theta = self.camVector[1]*pi/180 # orbit angle unbound this way
        radius = max(_MINCAMDIST_,min(1000,self.camVector[0]))
        camera.setX(radius*cos(phi)*sin(theta))
        camera.setY(-radius*cos(phi)*cos(theta))
        camera.setZ(radius*sin(phi))
        
        # Keep Camera above terrain
        # TO DO: Object occlusion with camera intersection
#        cx,cy,cz = camera.getPos(self.terrain.getRoot())
#        terZ = self.terrain.getElevation(cx,cy) # what is terrain elevation at new camera pos
#        print "localframe: ",app.camera.getPos()
#        print "worldframe: ",app.camera.getPos(terrainRoot)
#        print "terra  WF: ", cx,cy,terrain.getElevation(cx,cy)
#        if cz <= terZ+epsilon:
#            camera.setZ(self.terrain.getRoot(),terZ+epsilon)
        camera.lookAt(self.avnp,Point3(0,.333,2)) # look at the avatar nodepath
#        camera.lookAt(self.sun.model)
        
    #    print camVector                   
        return task.cont
        

W = World()
#W.useDrive()
#W.camera.setPos(100,100,10)
W.run()
