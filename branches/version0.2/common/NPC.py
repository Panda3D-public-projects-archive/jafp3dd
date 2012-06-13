# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 20:57:23 2012

@author: shawn
"""
import random
from os import urandom

from panda3d.core import *
#from direct.showbase import Loader
from direct.showbase.ShowBase import taskMgr
from direct.fsm.FSM import FSM
from panda3d.ai import *
 
class Gatherer(FSM):

    def __init__(self,name,nodePath):
        FSM.__init__(self, 'aGatherer')
#        self.defaultTransitions = {
#            'Walk' : [ 'Walk2Swim' ],
#            'Walk2Swim' : [ 'Swim' ],
#            'Swim' : [ 'Swim2Walk', 'Drowning' ],
#            'Swim2Walk' : [ 'Walk' ],
#            'Drowning' : [ ],
#            } 
        self.np = nodePath
        self.resPos = None
        self.centerPos = None
        self.cargo = 0
        self.maxCargo = 2
        self.loadRate = 1
        self.AI = AICharacter(name,nodePath, 50, 0.05, 5)
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
        
class serverNPC():
# Data needed to sync: x,y,z,h,p,r,speed
    
    nextUpdate = 0
    speed = 0
    def __init__(self,name):
        self.root = NodePath(PandaNode(name))
        self.ID = urandom(16)
#        print self.ID
        
    def makeChange(self,ttime):
        self.speed = .5 + 3.5*abs(random.gauss(0,.33333))
        newH = random.gauss(0,60)
        self.setH(self,newH) #key input steer
        self.nextUpdate = ttime + 2 # randomize when to update next


class DynamicObject():
    def __init__(self,nodeName,modelName,modelScale,parentNode=None):
        self.loader = Loader.Loader(self)
        self.color = (VBase4(random.random(),random.random(),random.random(),1))
        self.model = self.loader.loadModel(modelName)
#TODO: Load ACTORS as well as static models...        
        self.model.reparentTo(parentNode)
        self.model.setScale(modelScale)
        self.model.setColor(self.color)
        
#        self.commandsBuffer = dict({0:[Vec3(70,70,0),Vec3(0,0,0),Vec3(0,0,0),Vec3(0,0,0)]}) # {time:[list of commands]}
#        self.speed = 0
#        self.nextUpdate = 0
#        
#        
#    def _timeToKey(self,timenow):
#        """ return the buffer key time just previous to timenow """
#        # get time in buffer that is just previous to time now 
#        utimes = self.commandsBuffer.keys()
#        utimes.sort()
#        for t in utimes:
#            if t <= timenow: 
#                timekey = t # give me the index first entry in the dict that is < timenow 
#        return timekey
#        
#    def calcPos(self,timenow):
#        ts = self._timeToKey(timenow)
#        dT = timenow-ts
#        cmds = self.commandsBuffer[ts] # give me the command/state associated with time in [ix]
#        # store commands as [Point3:pos,Vect3:vel,Vec3:accel,Vec3:Hpr] 
#        # velocity direction can be different than the orientation of the model
#        pos = cmds[0] + cmds[1]*dT + cmds[2]*0.5*dT**2
#        pos = (max(0,pos[0]),max(0,pos[1]),max(0,pos[2]))
#        self.setPos(pos)
#        return pos
#    
#    def updateCommandsBuffer(self,time,commands):
#        #assuming here that time keys are put in sequential; no sort needed
#        if time > (self.commandsBuffer.keys())[-1]:
#            self.commandsBuffer.update({time:commands})
#        else:
#             # adding a time before the last time in the list triggers a recalc
#             # assumption is that this is a server based update, thus in the past
#             # and the new pos needs to be calculated
#            raise Exception('command update time before the latest update time!')
#             