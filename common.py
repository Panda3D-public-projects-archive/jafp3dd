# -*- coding: utf-8 -*-
"""
Created on Fri Feb 03 14:24:37 2012

@author: us997259
"""

from direct.showbase.ShowBase import taskMgr
#from direct.showbase.DirectObject import DirectObject
from panda3d.core import * #PandaNode, NodePath, CollisionNode, CollisionSphere

from CONSTANTS import *

class GameObject():
    """ fancy wrapper for nodepath """

    def __init__(self,name='', modelName = None):
        self.name = name
        self.root = PandaNode(name + '_Gameobj_node')
        self.np = NodePath(self.root)
        if modelName:
            self.np = loader.loadModel(modelName)
#TODO:     is NodePath.attachCollisionSphere the same? better? RESEARCH            
        self.cnp = self.np.attachNewNode(CollisionNode(name + '-coll-node'))
        self.cnp.node().addSolid(CollisionSphere(0,0,1,.5))


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
   