# -*- coding: utf-8 -*-
"""
Created on Fri Feb 03 14:24:37 2012

@author: us997259
"""

import random
from math import sin,cos,pi

from direct.showbase.ShowBase import taskMgr
#from direct.showbase.DirectObject import DirectObject
from panda3d.core import * #PandaNode, NodePath, CollisionNode, CollisionSphere
from direct.fsm.FSM import FSM
from panda3d.ai import *
#from direct.actor.Actor import Actor

TURN_RATE = 90    # Degrees per second
WALK_RATE = 30
MIN_CAM_DIST = .333

from CONSTANTS import *

class GameObject():
    """ fancy wrapper for nodepath """

    def __init__(self,name='', modelName = None):
        self.name = name
        self.root = PandaNode(name + '_Gameobj_node')
        self.np = NodePath(self.root)
        if modelName:
            self.np = loader.loadModel(modelName)
#            self.np = Actor(modelName)
            self.np.setName(name)
#TODO:     is NodePath.attachCollisionSphere the same? better? RESEARCH
#TODO: search for collision geometry in the model and add to object
#        self.cnp = self.np.attachNewNode(CollisionNode(name + '-coll-node'))
#        self.cnp.node().addSolid(CollisionSphere(0,0,1,.5))
        self.np.setTag('selectable','1')

    def setSelected(sel = False):
        if sel:        
            self.np.colorScale(2,0,0)
        else:
            self.np.colorScale(1,1,1)
        
class ControlledObject(GameObject):
    """ GameObject with that add Controls"""

    def __init__(self,controller=None, **kwargs):
        GameObject.__init__(self,**kwargs)
        self.controlState = controller
        taskMgr.add(self.update,'update'+self.name.upper())

    def update(self,task):
#        print self.controlState
        dt = globalClock.getDt()
        if self.controlState:
            self.np.setPos(self.np,WALK_RATE*self.controlState['strafe']*dt,WALK_RATE*self.controlState['walk']*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
#TODO: GENERALIZE CONTROL TO HPR BINDINGS
            self.np.setH(self.np,TURN_RATE*self.controlState['turn']*dt) #key input steer
        return task.cont

class ControlledCamera(ControlledObject):
    """ Expects Panda3d base globals to be present already
    ControlledCamera always has a "target" (think of it as an 'empty' in blender)
    parented to base.render
    nodepath (avatar, tree, something)
    When selecting a game object, it will become parented to the empty...
    We always move the empty: if we want to move Player X, player X game object must be
    parented to cameraTarget"""

    #TODO: GLOBALLY:
    # Add screen picking
    # make zoom a proper PI controller: Set radius with wheel. let PID approach it
    # more robust free camera mode

    MOUSE_STEER_SENSITIVITY = -70*TURN_RATE
    ZOOM_STEP = 1
    radiusGain = 0.5

    def __init__(self,controller=None,**kwargs):
        ControlledObject.__init__(self,controller,**kwargs)
        base.disableMouse() # ONLY disables the mouse drive of the camera
        self._camVector = [10,0,10]    # [goal* distance to target, heading to target, pitch to target ]
        # Target oject or location for camera to look at
        self._target = self.np    # remnant of 1st implementation
        self.np.reparentTo(base.render)
        camera.reparentTo(self._target)

                    
    def update(self,task):
        ControlledObject.update(self,task)
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


        # THERE IS ALWAYS A TARGET EMPTY
        camera.setX(radius*cos(phi)*sin(theta))
        camera.setY(-radius*cos(phi)*cos(theta))
        camera.setZ(radius*sin(phi))
        camera.lookAt(self._target) # look at the avatar nodepath

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


class Gatherer(GameObject,FSM):

    def __init__(self,name=None,modelName=None,modelScale=1,**kwargs):
        GameObject.__init__(self,name,modelName,**kwargs)
        FSM.__init__(self, 'aGatherer')

#        self.defaultTransitions = {
#            'Walk' : [ 'Walk2Swim' ],
#            'Walk2Swim' : [ 'Swim' ],
#            'Swim' : [ 'Swim2Walk', 'Drowning' ],
#            'Swim2Walk' : [ 'Walk' ],
#            'Drowning' : [ ],
#            }

#TODO: Load ACTORS as well as static models...
        self.np.setScale(modelScale)
        color = (VBase4(random.random(),random.random(),random.random(),1))
        self.np.setColor(color)

        self.resPos = None
        self.centerPos = None
        self.cargo = 0
        self.maxCargo = 5
        self.loadRate = 1
        self.AI = AICharacter(name,self.np, 50, 0.05, 5)
        self.behavior = self.AI.getAiBehaviors()

        taskMgr.doMethodLater(.25,self.stateMonitor,'GathererMonitor')


    def setResourcePos(self,position):
        self.resPos = position # should be vec3

    def setCenterPos(self,position):
        self.centerPos = position
#        self.behavior.removeAi('seek')
#        self.behavior.seek(self.centerPos,1.0)

#    def enterSearch(self):
#        self.behavior.wander(10, 0, 64, 1.0)
#
#    def exitSearch(self):
#        self.behavior.removeAi('wander')

    def enterToResource(self):
        self.behavior.seek(self.resPos,1.0)

    def exitToResource(self):
        self.behavior.removeAi('seek')

    def enterGather(self):
#        self.behavior.wander(3, 0, 3, 1.0)
        taskMgr.doMethodLater(5,self.gatherTimer,'gatherTask')

    def exitGather(self):
        self.behavior.removeAi('wander')

    def enterToCenter(self):
        self.behavior.seek(self.centerPos,1.0)

    def exitToCenter(self):
        self.behavior.removeAi('seek')

    def enterDeliver(self):
#        self.behavior.wander(1, 0, 1, 1.0)
        taskMgr.doMethodLater(5,self.deliverTimer,'deliverTask')

    def exitDeliver(self):
        self.behavior.removeAi('wander')

#    def enterDanger(self):
#        print "Aahhh! Implement me!"
#
#    def exitDanger(self):
#        pass

    def stateMonitor(self,task):
        if self.state == 'ToCenter' and self.behavior.behaviorStatus('seek') == 'done':
            self.request('Deliver')
        if self.state == 'ToResource' and self.behavior.behaviorStatus('seek') == 'done':
            self.request('Gather')
        return task.again

    def gatherTimer(self,task):
        self.request('ToCenter')
        return task.done

    def deliverTimer(self,task):
        self.request('ToResource')
        return task.done
