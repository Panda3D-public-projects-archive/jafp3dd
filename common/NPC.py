# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 20:57:23 2012

@author: shawn
"""
from panda3d.core import *
import random

class DynamicObject(NodePath):
    def __init__(self,nodeName,modelName,modelScale,parentNode=None):
        NodePath.__init__(self,nodeName)
        self.commandsBuffer = dict({0:[Vec3(70,70,0),Vec3(0,0,0),Vec3(0,0,0),Vec3(0,0,0)]}) # {time:[list of commands]}
        self.speed = 0
        self.nextUpdate = 0
        self.color = (VBase4(random.random(),random.random(),random.random(),1))
        self.model = loader.loadModel(modelName)
#TODO: Load ACTORS as well as static models...        
        self.model.reparentTo(self)
        self.setScale(modelScale)
        self.model.setColor(self.color)
        if parentNode: self.reparentTo(parentNode)
        
    def _timeToKey(self,timenow):
        """ return the buffer key time just previous to timenow """
        # get time in buffer that is just previous to time now 
        utimes = self.commandsBuffer.keys()
        utimes.sort()
        for t in utimes:
            if t <= timenow: 
                timekey = t # give me the index first entry in the dict that is < timenow 
        return timekey
        
    def calcPos(self,timenow):
        ts = self._timeToKey(timenow)
        dT = timenow-ts
        cmds = self.commandsBuffer[ts] # give me the command/state associated with time in [ix]
        # store commands as [Point3:pos,Vect3:vel,Vec3:accel,Vec3:Hpr] 
        # velocity direction can be different than the orientation of the model
        pos = cmds[0] + cmds[1]*dT + cmds[2]*0.5*dT**2
        pos = (max(0,pos[0]),max(0,pos[1]),max(0,pos[2]))
        self.setPos(pos)
        return pos
    
    def updateCommandsBuffer(self,time,commands):
        #assuming here that time keys are put in sequential; no sort needed
        if time > (self.commandsBuffer.keys())[-1]:
            self.commandsBuffer.update({time:commands})
        else:
             # adding a time before the last time in the list triggers a recalc
             # assumption is that this is a server based update, thus in the past
             # and the new pos needs to be calculated
            raise Exception('command update time before the latest update time!')
             