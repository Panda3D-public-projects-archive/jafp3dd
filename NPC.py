# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 20:57:23 2012

@author: shawn
"""
from panda3d.core import *
import random

class NPC(NodePath):
    def __init__(self,nodeName,modelName,modelScale,parentNode):
        NodePath.__init__(self,nodeName)
        self.commandsBuffer = dict({0:[Vec3(70,70,0),Vec3(0,0,0),Vec3(0,0,0),Vec3(0,0,0)]}) # {time:[list of commands]}
        self.speed = 0
        self.nextUpdate = 0
        self.color = (VBase4(random.random(),random.random(),random.random(),1))
        self.model = loader.loadModel(modelName)
        self.model.reparentTo(self)
        self.setScale(modelScale)
        self.model.setColor(self.color)
        self.reparentTo(parentNode)
        
    def calcPos(self,timenow):
        # get time just previous to time now in buffer
        utimes = self.commandsBuffer.keys()
        utimes.sort()
        for ix in utimes:
            if ix <= timenow: ts = ix # give me the index first entry in the dict that is < timenow
        dT = timenow-ts
        cmds = self.commandsBuffer[ts] # give me the command/state associated with time in [ix]
        # store commands as [Point3:pos,Vect3:vel,Vec3:accel,Vec3:Hpr] 
        # velocity direction can be different than the orientation of the model
        pos = cmds[0] + cmds[1]*dT + cmds[2]*0.5*dT**2
        self.setPos(pos)
        return pos
    
    def updateCommandsBuffer(self,time,commands):
        if time < (self.commandsBuffer.keys())[-1]: # adding a time before the last time in the list
        #assuming here that time keys are put in sequential; no sort needed
            raise Exception('command update time before the latest update time!')
        else:
            self.commandsBuffer.update({time:commands})


    def makeChange(self,ttime):
        Q = Quat()
        newH = random.gauss(-180,180)
        Q.setHpr((newH,0,0))
        # GET CUR VELOC VECTOR to MULTUPLE WITH Quat
        self.speed = 3*abs(random.gauss(0,.33333))
        self.updateCommandsBuffer(ttime,[self.getPos(),Q.getForward()*self.speed,Vec3(0,0,0)])
    #        self.setH(self,newH) #key input steer
        self.nextUpdate = ttime + 10*random.random() # randomize when to update next

#    def updateNpc(self):
#        x,y,z = self.calcPos(task.time)
#        self.setZ(self.ttMgr.tiles[self.ttMgr.curIJ].terGeom.getElevation(x,y))
 