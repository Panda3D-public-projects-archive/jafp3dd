
# SETUP SOME PATH's
#from sys import path
#path.append('c:\Panda3D-1.7.2')
#path.append('c:\Panda3D-1.7.2\\bin');
#_DATAPATH_ = "./resources"

from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
from math import sin,cos,pi
from numpy import sign

import sys, os


_TURNRATE_ = 90    # Degrees per second
_WALKRATE_ = 30
_MINCAMDIST_ = .333

RESOURCE_PATH = 'resources'

class Scene():
    """ Used to load static geometry"""

    def __init__(self,sceneName):
        if not sceneName:
            print "No Scene name given on init!!!"
            return -1
        self.root = PandaNode(sceneName)
        self.np = self.loadScene(sceneName)
#        self.cnp = self.np.attachNewNode(CollisionNode('plr-coll-node'))
        
    def loadScene(self,sceneName):
        tmp = loader.loadModel(os.path.join(RESOURCE_PATH,sceneName))
        if tmp:
            # do things with tmp like split up, add lights, whatever
            return tmp
        else:
            return None
        # load scene tree from blender
        # find lights from blender and create them with the right properties
        

class ControlledCamera():
    """ Expects Panda3d base globals to be present already """
    def __init__(self,controlState,target=Point3(0,0,0)):
        self.camVector = [10,0,10]    # [distance to target, heading to target, pitch to target ]
        self.target = target    # Target oject or location for camera to look at
        self.follow = True    # should the camera move with the target or stay fixed?
        self.mouseState = controlState
        taskMgr.add(self.update,'Adjust Camera')
        
        
    def update(self,task):
#    def updateCamera(self,task):
        epsilon = 1
        dt = globalClock.getDt() # to stay time based, not frame based
        if self.mouseState[0] and not self.mouseState[2]:
            self.camVector[1] += -_TURNRATE_*self.mouseState[4]
            self.camVector[2] += -_TURNRATE_*self.mouseState[5]
        if not self.mouseState[0] and self.mouseState[2]:  # mouse Steer av
#TODO: ENABLE MOUSE STEER            self.avnp.setH(self.avnp,-2*_TURNRATE_*self.mouseState[4])
            self.camVector[2] += -_TURNRATE_*self.mouseState[5]
        
    #    print avHandler.mouseState[3]
        mbWheel = self.mouseState[3]
        if mbWheel:
            self.camVector[0] += 15*(sign(mbWheel))*dt
            self.mouseState[3] -= 3*sign(mbWheel)*dt
            if abs(self.mouseState[3]) < .15: self.mouseState[3] = 0 # anti-jitter on cam
        
#        self.camVector[0] += 15*(self.Kzoom)*dt
#        self.camVector[1] += .5*_TURNRATE_*self.Ktheta*dt
#        self.camVector[2] += .5*_TURNRATE_*self.Kpitch*dt
#TODO: ENABLE CAMPERA CONTROLS FROM KEYS
     
        phi = max(-pi/2,min(pi/2,self.camVector[2]*pi/180))
        theta = self.camVector[1]*pi/180 # orbit angle unbound this way
        radius = max(_MINCAMDIST_,min(1000,self.camVector[0]))
        if self.follow:
            relativeNP = self.target
        else:
            relativeNP = None
        camera.setX(relativeNP, radius*cos(phi)*sin(theta))
        camera.setY(relativeNP, -radius*cos(phi)*cos(theta))
        camera.setZ(relativeNP, radius*sin(phi))
        
        # Keep Camera above terrain
        # TO DO: Object occlusion with camera intersection
#        cx,cy,cz = camera.getPos(self.terrain.getRoot())
#        terZ = self.terrain.getElevation(cx,cy) # what is terrain elevation at new camera pos
#        print "localframe: ",app.camera.getPos()
#        print "worldframe: ",app.camera.getPos(terrainRoot)
#        print "terra  WF: ", cx,cy,terrain.getElevation(cx,cy)
#        if cz <= terZ+epsilon:
#            camera.setZ(self.terrain.getRoot(),terZ+epsilon)
#        camera.lookAt(self.target,Point3(0,.333,2)) # look at the avatar nodepath
        camera.lookAt(self.target) # look at the avatar nodepath
        
    #    print camVector                   
        return task.cont
        

class Player():
    """ fancy wrapper for player nodepath"""
    
    def __init__(self,modelName,controlState, name=None):
        if not modelName:
            print('No model name passed to player.py!')
            return None
        self.root = PandaNode('player_node')
        self.np = loader.loadModel(modelName)
        if self.np:
            self.cnp = self.np.attachNewNode(CollisionNode('plr-coll-node'))
            self.cnp.node().addSolid(CollisionSphere(0,0,1,.5))
        taskMgr.add(self.update,'updatePlayer') #TODO: Move to Avatar class
        self.controlState = controlState
        
    def update(self,task):
        dt = globalClock.getDt()
        self.np.setPos(self.np,_WALKRATE_*self.controlState['strafe']*dt,_WALKRATE_*self.controlState['walk']*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
        self.np.setH(self.np,_TURNRATE_*self.controlState['turn']*dt) #key input steer
        x,y,z = self.np.getPos()
#        (xp,yp,zp) = self.ijTile(x,y).root.getRelativePoint(self.np,(x,y,z))

#        self.np.setZ(self.ijTile(x,y).getElevation(x,y))
        return task.cont   

  
        
class World(ShowBase):
    
    #pure control states
    mbState = [0,0,0,0,0,0] # 3 mouse buttons + wheel,deltaX, deltaY; buttons: 1 down, 0 on up
    mousePos = [0,0]
    mousePos_old = mousePos
        
    def __init__(self):
        ShowBase.__init__(self)
        self.setFrameRateMeter(1)
        #app.disableMouse()
        self.setupKeys()
        taskMgr.add(self.mouseHandler,'Mouse Manager')
        self.loadScene('testscene.x')

        self.player = Player(os.path.join(RESOURCE_PATH,'cube.x'),self.controls,'Player_1')
        self.player.np.reparentTo(render)

        self.CC = ControlledCamera(self.mbState,target=self.player.np)
        
#        taskMgr.add(self.updateAvnp,'Move Avatar Node') #TODO: Move to Avatar class
#        taskMgr.add(self.updateCamera,'Adjust Camera')
        

    #TODO: ADD OSD of FPS and following:
#        self.textObject = OnscreenText(text = str(self.avnp.getPos()), pos = (-0.9, 0.9), scale = 0.07, fg = (1,1,1,1))       
#        hdg = self.np.getH()       
#        self.textObject.setText(str((int(x),int(y),int(z),int(hdg))))

    def loadScene(self,sceneName):
        self.scene = Scene(sceneName)
        self.scene.np.reparentTo(render)      
#        self.setupModels()
        self.setupLights()
        
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
    
        self.accept("mouse1",self._mbutton,[1,1])
        self.accept("mouse1-up",self._mbutton,[1,0])
        self.accept("mouse2",self._mbutton,[2,1])
        self.accept("mouse2-up",self._mbutton,[2,0])
        self.accept("mouse3",self._mbutton,[3,1])
        self.accept("mouse3-up",self._mbutton,[3,0])
        self.accept("wheel_up",self._mbutton,[4,-1])
        self.accept("wheel_up-up",self._mbutton,[4,0])
        self.accept("wheel_down",self._mbutton,[4,1])
        self.accept("wheel_down-up",self._mbutton,[4,0])

        self.accept(_KeyMap['wire'],self.toggleWireframe)      
        self.accept("escape",sys.exit)

    def _setControls(self,key,value):
            self.controls[key] = value
            if key == 'autoWalk':
                if self.controls["walk"] == 0:
                    self.controls["walk"] = 1
                else:
                    self.controls["walk"] = 0  

    def _mbutton(self,b,s): 
        if b == 4: # add up mouse wheel clicks
            self.mbState[b-1] += s
        else:
            self.mbState[b-1] = s
#        print self.mbState
        # ADD A L+R BUTTON WALK 
                          
    def mouseHandler(self,task):
       
        if base.mouseWatcherNode.hasMouse():
            self.mousePos_old = self.mousePos
            self.mousePos = [base.mouseWatcherNode.getMouseX(), \
            base.mouseWatcherNode.getMouseY()]
            self.mbState[4] = self.mousePos[0] - self.mousePos_old[0] # mouse horizontal delta
            self.mbState[5] = self.mousePos[1] - self.mousePos_old[1] # mouse vertical delta
            
        return task.cont

#    def updateAvnp(self,task):
#        dt = globalClock.getDt()
#        self.avnp.setPos(self.avnp,_WALKRATE_*self.Kstrafe*dt,_WALKRATE_*self.Kwalk*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
#        self.avnp.setH(self.avnp,_TURNRATE_*self.Kturn*dt) #key input steer
#        x,y,z = self.avnp.getPos()
##        (xp,yp,zp) = self.ijTile(x,y).root.getRelativePoint(self.avnp,(x,y,z))
#
#        hdg = self.avnp.getH()
##        self.avnp.setZ(self.ijTile(x,y).getElevation(x,y))
#        
#        self.textObject.setText(str((int(x),int(y),int(z),int(hdg))))
#        return task.cont   
    

W = World()
#W.useDrive()
#W.camera.setPos(100,100,10)
W.run()
