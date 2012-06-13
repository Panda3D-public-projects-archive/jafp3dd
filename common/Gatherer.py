# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 20:57:23 2012

@author: shawn
"""
import random
from os import urandom

from panda3d.core import *
from direct.showbase.ShowBase import taskMgr
from direct.fsm.FSM import FSM
from panda3d.ai import *
from direct.showbase import Loader
from direct.showbase.DirectObject import DirectObject

loader = Loader.Loader(DirectObject)
 
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
