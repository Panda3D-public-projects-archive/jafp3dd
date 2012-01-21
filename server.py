# -*- coding: utf-8 -*-
"""
Created on Mon Nov 28 13:24:03 2011

@author: us997259
"""

import time

from direct.showbase.ShowBase import taskMgr
#from direct.showbase.DirectObject import DirectObject
#import direct.directbase.DirectStart
from panda3d.core import *

from common.NPC import serverNPC
import network.rencode as rencode
from network.client import NetServer

NUM_NPC = 10
SERVER_TICK = 0.0166 # seconds
SNAP_INTERVAL = 0.050

class TileServer(NetServer):
    def __init__(self):
        NetServer.__init__(self)
        self.tickCount = 0
        self.snapCount = 0
        self.tlast = time.time()
        self.snapBuffer = []
        self.nextTx = 0
        self.npc = []

        for n in range(NUM_NPC):
            self.npc.append( serverNPC('someGuy'+str(n)))
            self.npc[n].setPos(70,70,0)
            self.npc[n].ID = n

        taskMgr.add(self.NpcAI,'server NPCs')
        taskMgr.doMethodLater(SERVER_TICK,self.calcTick,'calc_tick')
        taskMgr.doMethodLater(SNAP_INTERVAL,self.takeSnapshot,'SnapshotTsk')
        taskMgr.doMethodLater(1.0,self.sendThrottle,'TXatRate')

    def ProcessData(self,datagram):
        t0 = time.ctime()
        I = DatagramIterator(datagram)
        msgID = I.getInt32() # what type of message
        data = rencode.loads(I.getString()) # data matching msgID
        print t0,msgID,data
        if msgID == 10: print data
#            self.write(t0,datagram.getConnection())

    def calcTick(self,task):
        tnow = time.time()
        self.tickCount += 1
        dt = tnow - self.tlast
#        print dt
#        dt = task.getDt()
        for iNpc in self.npc:
            iNpc.setPos(iNpc,0,iNpc.speed*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
#            iNpc.setZ(self.ttMgr.getElevation((x,y)))
#TODO: What to do about terrain heights???
#            iNpc.printPos()
#        print "tick:",self.tickCount
        self.tlast = tnow
        return task.again

    def takeSnapshot(self,task):
#        print time.clock()
        self.snapCount += 1
        snapshot = [self.snapCount]
        # snapshot format [tick,(objectID,x,y,z),(ObjID,x..),...]
        for iNpc in self.npc:
            x,y,z = iNpc.getPos()
            h,p,r = iNpc.getHpr()
            snapshot.append((iNpc.ID,x,y,z,h,p,r))
        self.snapBuffer.append(snapshot)
        # snapBuffer = [snapshot1, snapshot2,...snapshotN] #since last TX

        return task.again
    def NpcAI(self,task):
        for iNpc in self.npc:
            tnow = time.time()
            if tnow > iNpc.nextUpdate:         # change direction and heading every so often
                iNpc.makeChange(tnow)
        return task.cont

    def sendThrottle(self,task):
        for client in self.activeConnections:
            print "tick:",self.tickCount," TX->", client.getAddress()
            self.write(int(0),self.snapBuffer, client) # rencode lets me send objects??
        self.snapBuffer = []
        return task.again


if __name__ == '__main__':
    server = TileServer()
#    nMgr = NPCmanager()
#    server.run()
    taskMgr.run()

