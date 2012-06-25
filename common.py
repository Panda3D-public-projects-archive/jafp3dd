# -*- coding: utf-8 -*-
"""
Created on Fri Feb 03 14:24:37 2012

@author: us997259
"""

import random

from direct.showbase.ShowBase import taskMgr
#from direct.showbase.DirectObject import DirectObject
from panda3d.core import * #PandaNode, NodePath, CollisionNode, CollisionSphere
from direct.fsm.FSM import FSM
from panda3d.ai import *

from CONSTANTS import *

class GameObject():
    """ fancy wrapper for nodepath """

    def __init__(self,name='', modelName = None):
        self.name = name
        self.root = PandaNode(name + '_Gameobj_node')
        self.np = NodePath(self.root)
        if modelName:
            self.np = loader.loadModel(modelName)
            self.np.setName(name)
#TODO:     is NodePath.attachCollisionSphere the same? better? RESEARCH
#TODO: search for collision geometry in the model and add to object
        self.cnp = self.np.attachNewNode(CollisionNode(name + '-coll-node'))
        self.cnp.node().addSolid(CollisionSphere(0,0,1,.5))
        self.np.setTag('selectable','1')

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


class Gatherer(FSM):

    def __init__(self,name,modelName,modelScale=1):
        FSM.__init__(self, 'aGatherer')
#        self.defaultTransitions = {
#            'Walk' : [ 'Walk2Swim' ],
#            'Walk2Swim' : [ 'Swim' ],
#            'Swim' : [ 'Swim2Walk', 'Drowning' ],
#            'Swim2Walk' : [ 'Walk' ],
#            'Drowning' : [ ],
#            }
        #TODO: Load ACTORS as well as static models...
        self.np = loader.loadModel(modelName)
        self.np.setName(name)
        self.np.setScale(modelScale)
        self.np.setH(180)
        color = (VBase4(random.random(),random.random(),random.random(),1))
        self.np.setColor(color)


        cnp = self.np.attachNewNode(CollisionNode('model-collision'))
        cnp.node().addSolid(CollisionSphere(0,0,1,.5))

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
        print self.centerPos
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
        print self.state
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
