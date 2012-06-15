
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


TURN_RATE = 90    # Degrees per second
WALK_RATE = 30
MIN_CAM_DIST = .333

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
    """ Expects Panda3d base globals to be present already 
    ControlledCamera always has a "target" (think of it as an 'empty' in blender)
    That target can be free (parented to base.render), or it can be attached to another
    nodepath (avatar, tree, something) 
    When selecting a game object, it will become parented to the empty...
    We always move the empty: if we want to move Player X, player X game object must be 
    parented to cameraTarget"""
    
    #TODO: GLOBALLY:
    # Add screen picking
    # make zoom a proper PI controller: Set radius with wheel. let PID approach it    
    # more robust free camera mode
    
    MOUSE_STEER_SENSITIVITY = -70*TURN_RATE
    ZOOM_STEP = .1
    
    def __init__(self,controlState, follow=True):
#    def __init__(self,controlState,target=Point3(0,0,0),follow=True):        
        base.disableMouse() # ONLY disables the mouse drive of the camera
        self._camVector = [10,0,10]    # [goal* distance to target, heading to target, pitch to target ]
        self.follow = follow            # should the camera move with the target or stay fixed?
        self._snapBack = True           # mouseLook=False = return camera to behind target (if we have a target and in follow mode)
        self.controlState = controlState
        self._target = NodePath(PandaNode("CameraTarget"))          # Target oject or location for camera to look at
        self._target.reparentTo(base.render)
        camera.reparentTo(self._target)
        taskMgr.add(self.update,'Adjust Camera')

#    def setTarget(self,target=None):
#        if not target:
#            camera.reparentTo(base.render)
#        else:
#            camera.reparentTo(target)
        
    def update(self,task):
        dt = globalClock.getDt() # to stay time based, not frame based

        # MOVE TARGET EMPTY
        self._target.setPos(self._target,WALK_RATE*self.controlState['strafe']*dt,WALK_RATE*self.controlState['walk']*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
        self._target.setH(self._target,TURN_RATE*self.controlState['turn']*dt) #key input steer
#TODO:    implement mouse steer as child object inheriting cam target's heading
# NOT mouse steer is what we actually need!
        if self.controlState["mouseSteer"]:
            self._target.setH(self._target,self.MOUSE_STEER_SENSITIVITY*self.controlState['mousePos'][0]*dt) # mouse steering
        
        # MOVE CAMERA ACCORDINGLY
        if self.controlState["mouseLook"]:
            self._camVector[1] += -TURN_RATE*self.controlState["mousePos"][0]
        if self.controlState["mouseLook"] or self.controlState["mouseSteer"]:
            self._camVector[2] += -TURN_RATE*self.controlState["mousePos"][1]


#TODO: ENABLE CAMERA CONTROLS FROM KEYS
#        self._camVector[0] += 15*(self.Kzoom)*dt
#        self._camVector[1] += .5*TURN_RATE*self.Ktheta*dt
#        self._camVector[2] += .5*TURN_RATE*self.Kpitch*dt

#        mbWheel = self.controlState["mouseWheel"]
#        if mbWheel:
#            self._camVector[0] += 15*(sign(mbWheel))*dt
#            self.controlState["mouseWheel"] -= 3*sign(mbWheel)*dt
#            if abs(self.controlState["mouseWheel"]) < .15: self.controlState["mouseWheel"] = 0 # anti-jitter on cam
        self._camVector[0] += self.controlState["mouseWheel"] * self.ZOOM_STEP
#        distErr = currentDistance - self._camVector[0]
#        change self.current radius by gain*distError

        phi = max(-pi/2,min(pi/2,self._camVector[2]*pi/180))
        theta = self._camVector[1]*pi/180 # orbit angle unbound this way
        radius = self._camVector[0]
        if radius >= 1000:
            radius = 1000
            self.controlState["mouseWheel"] = 0 # clear out any buffered changes
        elif radius <= MIN_CAM_DIST:
            radius = MIN_CAM_DIST
            self.controlState["mouseWheel"] = 0 # clear out any buffered changes
    

#        if self._target:
        # IN ORBIT TARGET MODE
        # THERE IS ALWAYS A TARGET EMPTY
        camera.setX(radius*cos(phi)*sin(theta))
        camera.setY(-radius*cos(phi)*cos(theta))
        camera.setZ(radius*sin(phi))
        camera.lookAt(self._target) # look at the avatar nodepath
#        else:
#            camera.setHpr(theta, phi, 0)

        camera.printPos()

#===============================================================================
# Keep Camera above terrain
#===============================================================================
#TODO: Object occlusion with camera intersection
#        epsilon = 1
#        cx,cy,cz = camera.getPos(self.terrain.getRoot())
#        terZ = self.terrain.getElevation(cx,cy) # what is terrain elevation at new camera pos
#        print "localframe: ",app.camera.getPos()
#        print "worldframe: ",app.camera.getPos(terrainRoot)
#        print "terra  WF: ", cx,cy,terrain.getElevation(cx,cy)
#        if cz <= terZ+epsilon:
#            camera.setZ(self.terrain.getRoot(),terZ+epsilon)
#        camera.lookAt(self.target,Point3(0,.333,2)) # look at the avatar nodepath

    #    print _camVector
        return task.cont


class Player():
    """ fancy wrapper for player nodepath"""

    def __init__(self,modelName,controlState=None, name=None):
        if not modelName:
            print('No model name passed to player.py!')
            return None
        self.root = PandaNode('player_node')
        self.np = loader.loadModel(modelName)
        if self.np:
            self.cnp = self.np.attachNewNode(CollisionNode('plr-coll-node'))
            self.cnp.node().addSolid(CollisionSphere(0,0,1,.5))
        taskMgr.add(self.update,'updatePlayer')
        self.controlState = controlState

    def update(self,task):
#        print self.controlState
        dt = globalClock.getDt()
        if self.controlState:
            self.np.setPos(self.np,WALK_RATE*self.controlState['strafe']*dt,WALK_RATE*self.controlState['walk']*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
            self.np.setH(self.np,TURN_RATE*self.controlState['turn']*dt) #key input steer

#        x,y,z = self.np.getPos()
#        (xp,yp,zp) = self.ijTile(x,y).root.getRelativePoint(self.np,(x,y,z))
#        self.np.setZ(self.ijTile(x,y).getElevation(x,y))

#        print self.controlState
#        print('\n')
        return task.cont



class World(ShowBase):

    #pure control states
    mbState = [0,0,0,0] # 3 mouse buttons + wheel, buttons: 1 down, 0 on up
    mousePos = [0,0]
    mousePos_old = mousePos
    controls = {"turn":0, "walk":0, "autoWalk":0,"strafe":0,'camZoom':0,\
        'camHead':0,'camPitch':0, "mouseTurn":0, "mousePos":[0,0],"mouseWheel":0,"mouseLook":False,"mouseSteer":False}

    def __init__(self):
        ShowBase.__init__(self)
        self.setFrameRateMeter(1)
        self.setupKeys()
        taskMgr.add(self.mouseHandler,'Mouse Manager')
        self.loadScene('testscene.x')

        self.CC = ControlledCamera(self.controls, follow=True)

        self.player = Player(os.path.join(RESOURCE_PATH,'cube.x'),self.controls,'Player_1')
        self.player.np.reparentTo(self.CC._target)
        self.player.np.setZ(.2)

        self.textObject = OnscreenText(text = str(self.player.np.getPos()), pos = (-0.9, 0.9), scale = 0.07, fg = (1,1,1,1))
        taskMgr.add(self.updateOSD,'OSDupdater')

    def loadScene(self,sceneName):
        self.scene = Scene(sceneName)
        self.scene.np.reparentTo(render)
#        self.setupModels()
        self.setupLights()

    def setupLights(self):
        self.render.setShaderAuto()
        self.alight = AmbientLight('alight')
        self.alight.setColor(VBase4(1,1,1,1))
        self.alnp = self.render.attachNewNode(self.alight)
        render.setLight(self.alnp)

        self.dlight = DirectionalLight('dlight')
        self.dlight.setColor(VBase4(.8,.8,.8,1))
        self.dlnp = self.render.attachNewNode(self.dlight)
        render.setLight(self.dlnp)

        self.slight = Spotlight('slight')
        self.slight.setColor(VBase4(1,1,1,1))
        self.slnp = self.render.attachNewNode(self.slight)
        self.slnp.setPos(0,0,10)
        render.setLight(self.slnp)

#        self.slnp.lookAt(self.model)

    def setupKeys(self):

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

#        self.accept("mouse2",self._mwheel,[3,1])
#        self.accept("mouse2-up",self._mwheel,[3,0])
        self.accept("mouse1",self._setControls,["mouseLook",True])
        self.accept("mouse1-up",self._setControls,["mouseLook",False])
        self.accept("mouse3",self._setControls,["mouseSteer",True])
        self.accept("mouse3-up",self._setControls,["mouseSteer",False])

        self.accept("wheel_up",self._setControls,["mouseWheel",-1])
        self.accept("wheel_up-up",self._setControls,["mouseWheel",0])
        self.accept("wheel_down",self._setControls,["mouseWheel",1])
        self.accept("wheel_down-up",self._setControls,["mouseWheel",0])

        self.accept(_KeyMap['wire'],self.toggleWireframe)
        self.accept("escape",sys.exit)

    def _setControls(self,key,value):
            self.controls[key] = value
            # manage special conditions/states
            if key == 'autoWalk':
                if self.controls["walk"] == 0:
                    self.controls["walk"] = 1
                else:
                    self.controls["walk"] = 0
            if key == 'mouseWheel': 
                self.controls['mouseWheel'] += value # add up mouse wheel clicks
                print self.controls['mouseWheel']
                
#    def _mwheel(self,b,s):
#        if b == 4: # add up mouse wheel clicks
#            self.controls['mouseWheel'] += s
#        print self.mbState
        # ADD A L+R BUTTON WALK

    def mouseHandler(self,task):

        if base.mouseWatcherNode.hasMouse():
            self.mousePos_old = self.mousePos
            self.mousePos = [base.mouseWatcherNode.getMouseX(), \
            base.mouseWatcherNode.getMouseY()]
            dX = self.mousePos[0] - self.mousePos_old[0] # mouse horizontal delta
            dY = self.mousePos[1] - self.mousePos_old[1] # mouse vertical delta
            self.controls['mousePos'] = [dX,dY]
        return task.cont

    def updateOSD(self,task):
#TODO: change to dotasklater with 1 sec update...no need to hammer this        
        [x,y,z] = self.player.np.getPos()
        [hdg,p,r] = self.player.np.getHpr()
        self.textObject.setText(str((int(x),int(y),int(z),int(hdg))))
        return task.cont

W = World()
W.run()