# -*- coding: utf-8 -*-
"""
Created on Tue Aug 28 16:23:24 2012

@author: shawn
"""

import random
from direct.fsm.FSM import FSM
from panda3d.ai import *
from panda3d.core import VBase4

from common import GameObject



class NpcAI(GameObject,FSM):

    def __init__(self,name=None,modelName=None,**kwargs):
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
#        self.np.setScale(modelScale)
        self.AI = AICharacter(name,self.np, 50, 0.05, 5)
        self.behavior = self.AI.getAiBehaviors()
        self.accept(name + 'terminate',self.terminate)
        taskMgr.doMethodLater(.25,self.stateMonitor,name + 'StateMonitor')
#    
    def terminate(self):
        self.np.cleanup()
        self.np.removeNode()
        
    def stateMonitor(self,task):
#        if self.state == 'ToCenter' and self.behavior.behaviorStatus('seek') == 'done':
#            self.request('Deliver')
        pass
        return task.again

class Wanderer(NpcAI):

    def __init__(self,name=None,modelName=None,**kwargs):
        NpcAI.__init__(self,name,modelName,**kwargs)

        color = (VBase4(random.random(),random.random(),random.random(),1)*0.8)
        self.np.setColor(color)

        self.AI = AICharacter(name,self.np, 50, 0.05, 3)
        self.np.setPlayRate(3,'spin')   # custom playrate to anicube2 right now (08-29-12)
        self.behavior = self.AI.getAiBehaviors()
        
        self.behavior.wander(25,3,25,.5)
        self.behavior.obstacleAvoidance(1)
        
class Gatherer(NpcAI):

    def __init__(self,name=None,modelName=None,**kwargs):
        NpcAI.__init__(self,name,modelName,**kwargs)

        color = (VBase4(random.random(),random.random(),random.random(),1)*0.8)
        self.np.setColor(color)

        self.resPos = None
        self.centerPos = None
        self.cargo = 0
        self.maxCargo = 5
        self.loadRate = 1
        self.AI = AICharacter(name,self.np, 50, 0.05, .9)
        self.np.setPlayRate(3,'spin')   # custom playrate to anicube2 right now (08-29-12)
        self.behavior = self.AI.getAiBehaviors()
        
        self.behavior.obstacleAvoidance(1.0)

    def onClicked(self):
        GameObject.onClicked(self)
#        self.np.play('spin')
      
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
        self.np.loop('spin', restart=0)

    def exitToResource(self):
        self.behavior.removeAi('seek')
        self.np.stop()
        self.np.pose('spin', 0)
        
    def enterGather(self):
#        self.behavior.wander(3, 0, 3, 1.0)
#        self.np.loop('spin')
        taskMgr.doMethodLater(5,self.gatherTimer,'gatherTask')

    def exitGather(self):
        self.behavior.removeAi('wander')
#        self.np.play('spin', fromFrame= self.np.getCurrentFrame('spin'))
        
    def enterToCenter(self):
        self.behavior.seek(self.centerPos,1.0)
        self.np.loop('spin', restart=0)

    def exitToCenter(self):
        self.behavior.removeAi('seek')
        self.np.stop()
        self.np.pose('spin', 0)
        
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

