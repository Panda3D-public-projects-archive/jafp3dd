# -*- coding: utf-8 -*-
"""
Created on Wed Feb 08 16:46:17 2012

@author: us997259
"""
from direct.showbase.ShowBase import taskMgr
from direct.fsm.FSM import FSM

class Resource(FSM):
    """ Resource FSM. maintains the models and collision nodes (by state if different), the amount of the resource 
    available, the max amount available, and interface method(s) to modify contents"""
    
    def __init__(self, limit=None):
        FSM.__init__(self,'ResourceObj')
        self.contentsLimit = limit
        self.contents = self.contentsLimit
        taskMgr.add(self.stateMonitor,'ResStateMonitor')
        
    def spawn(self):
        self.contents = self.contentsLimit
    
    def take(self, amount):
        if amount > 0:
            self.contents -= amount

    def stateMonitor(self,task):
        pass
        return task.cont