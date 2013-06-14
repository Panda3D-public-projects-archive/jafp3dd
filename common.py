# -*- coding: utf-8 -*-
"""
Created on Fri Feb 03 14:24:37 2012

@author: us997259
"""


from math import sin,cos,pi
import time

from direct.showbase.ShowBase import taskMgr
from direct.showbase.DirectObject import DirectObject
from panda3d.core import * #PandaNode, NodePath, CollisionNode, CollisionSphere
from direct.fsm.FSM import FSM
from direct.actor.Actor import Actor

TURN_RATE = 90    # Degrees per second
MOUSE_TURN_MULTIPLIER = 100
WALK_RATE = 30
MIN_CAM_DIST = .333

from CONSTANTS import *

class resourceNode():
    __health = 0
    __location = [0,0,0]
    def __init__(self,quantity=1,loc=[0,0,0]):
        self.__health = quantity
        self.__location = loc        
        
    def exchange(self,amount):
        self.__health += amount
        
    
        
        
class GameObject(DirectObject): # Inherit from DO for event handling
    """ fancy wrapper for Actor Class. 
        adds properties like selectable and adding
        target reticle graphics and or stat's
    """

    def __init__(self,name='', modelName = None):
        self.name = name
        self.accept(name + 'highlight',self.onFocus)
        self.accept(name + 'clickedOn',self.onClicked)

        self.root = PandaNode(name + '_Gameobj_node')
        self.np = NodePath(self.root)
        if modelName:
#            self.np = loader.loadModel(modelName)
            self.np = Actor(modelName)
            self.np.setName(name)
#            self.np.showBounds()
#TODO:     is NodePath.attachCollisionSphere the same? better? RESEARCH
#TODO: search for collision geometry in the model and add to object
#        self.cnp = self.np.find('**/colbox')
#        if not self.cnp.isEmpty():
##            self.cnp.remove()
            self.cnp = self.np.attachNewNode(CollisionNode(name + '-coll-node'))
            self.cnp.node().addSolid(CollisionSphere(0,0,0,.5))
#            print("Adding ",self.cnp)
            self.cnp.show()


        self.np.setTag('selectable','1')
#        self.isSelected = False
        
    
    def onFocus(self):
        #mouse over focus, do this
        pass

    def onClicked(self):
        # mouse selected, do this
        pass
    
    def terminate(self):
        self.np.cleanup()
        self.np.removeNode()
        

        
        
#class TargetCard():
#    def init(self):
#        self.targetCard = loader.loadModel('resources/targeted.egg')
#        bv = self.np.getBounds()
#        if not bv.isEmpty():
#            self.targetCard.setPos(bv.getCenter())
#            self.targetCard.setScale(1.5*bv.getRadius())
#        self.targetCard.set_billboard_point_eye()
#       def terminate(self):
#   self.targetCard.setDepthTest(False)
#        self.targetCard.setDepthWrite(False)
#        self.targetCard.reparentTo(base.hidden)
#        self.targetCard.set_light_off()
#
#    def _showTarget(self,enabled=False):
#        if enabled:
##            self.targetCard.reparentTo(render)
#            self.targetCard.reparentTo(self.np) # need to follow object np, so parent to it
##            b = self.np.getBounds()
##            localCenter = b.getCenter() - self.targetCard.getPos()
##            self.targetCard.setPos(localCenter)
##            self.targetCard.setScale(1.1*b.getRadius())
#        else:
#            self.targetCard.reparentTo(base.hidden)
        

class Projectile(GameObject):
    # An object that lives for a short time,
    # spawns at initial x,y,z
    # travels in direction V0, with linear acceleration vector Accel
    # TBD add rotation vector(s)?

    def __init__(self,modelName,name='',r0=Vec3(0,0,0),V0=Vec3(0,0,0),Accel=Vec3(0,0,0),timeout = 3):
        GameObject.__init__(self,name,modelName)
        self.r0 = r0
        self.v0 = V0
        self.acc = Accel
        self.t0 = time.time()
        self.Tmax = timeout # duration of object before auto despawning
        
        taskMgr.add(self.update,'UpdatePosition')
        
    def update(self,task):
        T = time.time() - self.t0
        pos = self.r0 + self.v0*T + (self.acc/2.0)*(T**2)
        self.np.setPos(pos)
        if T <= self.Tmax:
            return task.cont
        else:
            GameObject.terminate(self)
            return task.done

        
class NodePathController():
    """ Controls for a nodepath (usually a game object associated with)
    """

    def __init__(self,controller=None,ctrlNP=None):
        self.controlState = controller
        self.controlledNP = ctrlNP
        taskMgr.add(self.update,'updateController')

    def update(self,task):
#        print self.controlState
        dt = globalClock.getDt()
        if self.controlState:
            self.controlledNP.setPos(self.controlledNP,WALK_RATE*self.controlState['strafe']*dt,WALK_RATE*self.controlState['walk']*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
#TODO: GENERALIZE CONTROL TO HPR BINDINGS
            self.controlledNP.setH(self.controlledNP,TURN_RATE*self.controlState['turn']*dt) #key input steer
            
        return task.cont
         
#class ControlledObject(GameObject,NodePathController):
#    """ GameObject with that add Controls"""
#
#    def __init__(self,controller=None, **kwargs):
#        GameObject.__init__(self,**kwargs)
#        NodePathController.__init__(self,controller,self.np)


class ControlledCamera(NodePathController):
    """ Expects Panda3d base globals to be present already
    ControlledCamera always has a "target" (think of it as an 'empty' in blender)
    parented to base.render
    nodepath (avatar, tree, something)
    When selecting a game object, it will become parented to the empty...
    We always move the empty: if we want to move Player X, player X game object must be
    parented to cameraTarget
    """

    #TODO: GLOBALLY:
    # make zoom a proper PI controller: Set radius with wheel. let PID approach it
    # more robust free camera mode

    MOUSE_STEER_SENSITIVITY = -MOUSE_TURN_MULTIPLIER*TURN_RATE
    ZOOM_STEP = 1
    radiusGain = 0.5

    def __init__(self,controller=None,np=None,target=None):
        NodePathController.__init__(self,controller,np)
        base.disableMouse() # ONLY disables the mouse drive of the camera
        self._camVector = [10,0,10]    # [goal* distance to target, heading to target, pitch to target ]
        # Target object or location for camera to look at
        self._target = target    # remnant of 1st implementation
#        self.np.reparentTo(base.render)
#        camera.reparentTo(self._target)

                    
    def update(self,task):
        if self.controlState:
            NodePathController.update(self,task)
            dt = globalClock.getDt() # to stay time based, not frame based
    
            if self.controlState["mouseSteer"]:
                self._target.setH(self._target,self.MOUSE_STEER_SENSITIVITY*self.controlState['mouseDeltaXY'][0]*dt) # mouse steering
            else:
                pass
    
            # MOVE CAMERA ACCORDINGLY
            if self.controlState["mouseLook"]:
                self._camVector[1] += -TURN_RATE*self.controlState["mouseDeltaXY"][0]
            if self.controlState["mouseLook"] or self.controlState["mouseSteer"]:
                self._camVector[2] += -TURN_RATE*self.controlState["mouseDeltaXY"][1]
    
    
    #TODO: ENABLE CAMERA CONTROLS FROM KEYS
    #        self._camVector[0] += 15*(self.Kzoom)*dt
    #        self._camVector[1] += .5*TURN_RATE*self.Ktheta*dt
    #        self._camVector[2] += .5*TURN_RATE*self.Kpitch*dt
    
            self._camVector[0] += self.controlState["mouseWheel"] * self.ZOOM_STEP
            self.controlState["mouseWheel"] = 0
            radius = self._camVector[0]
            radiusErr = camera.getPos().length() - radius
    #        print self.controlState["mouseWheel"], radiusErr
    
            if radiusErr > 0.0:
                radius -= self.radiusGain*radiusErr
    
            phi = max(-pi/2,min(pi/2,self._camVector[2]*pi/180))
            theta = self._camVector[1]*pi/180 # orbit angle unbound this way
            if radius >= 1000:
                radius = 1000
    #            self.controlState["mouseWheel"] = 0 # clear out any buffered changes
            elif radius <= MIN_CAM_DIST:
                radius = MIN_CAM_DIST
    #            self.controlState["mouseWheel"] = 0 # clear out any buffered changes
    
    
            camera.setX(radius*cos(phi)*sin(theta))
            camera.setY(-radius*cos(phi)*cos(theta))
            camera.setZ(radius*sin(phi))
        
        if self._target:
            camera.lookAt(self._target) # look at the target nodepath

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


