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

from common.NPC import serverNPC, Player
import network.rencode as rencode
from network.client import NetServer

NUM_NPC = 10
SERVER_TICK = 0.0166 # seconds
SNAP_INTERVAL = 1.0/20
TX_INTERVAL = 1.0/20

# Player control constants
TURN_RATE = 120    # Degrees per second
WALK_RATE = 8

# THIS MAP SETTINGS
_terraScale = (1,1,60) # xy scaling not working right as of 12-10-11. prob the LOD impacts
_mapName='map2'

class TileServer(NetServer):
    def __init__(self):
        NetServer.__init__(self)
        self.tickCount = 0
        self.snapCount = 0
        self.tlast = time.time()
        self.snapBuffer = []
        self.nextTx = 0
        self.npc = []
        self.players = dict()
        print "MAKE PLAYER LIST A DICTION"
        self.terGeom = None       

        for n in range(NUM_NPC):
            self.npc.append( serverNPC('someGuy'+str(n)))
            self.npc[n].setPos(70,70,0)
            self.npc[n].ID = n

        taskMgr.add(self.NpcAI,'server NPCs')
        taskMgr.doMethodLater(SERVER_TICK,self.calcTick,'calc_tick')
        taskMgr.doMethodLater(SNAP_INTERVAL,self.takeSnapshot,'SnapshotTsk')
        taskMgr.doMethodLater(TX_INTERVAL,self.sendThrottle,'TXatRate')

    def loadTerrainMap(self,HFname):
        self.terGeom = ScalingGeoMipTerrain("myHills",position)
        self.terGeom.setScale(geomScale[0],geomScale[1],geomScale[2]) # for objects of my class
        self.terGeom.setBruteforce(self._brute) # skip all that LOD stuff


    def calcTick(self,task):
        tnow = time.time()
        self.tickCount += 1
        dt = tnow - self.tlast
#        print dt

        for player in self.players.values():        
            player.root.setPos(player.root, WALK_RATE*player.controls['strafe']*dt,WALK_RATE*player.controls['walk']*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
            player.root.setH(player.root, player.controls['mouseTurn'] + TURN_RATE*player.controls['turn']*dt)
#        x,y,z = self.mapTile.avnp.getPos()
#        self.mapTile.avnp.setZ(self.mapTile.terGeom.getElevation(x,y))

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
        for player in self.players.values():
            x,y,z = player.root.getPos()
            h,p,r = player.root.getHpr()
            snapshot.append((player.ID,x,y,z,h,p,r))
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
            print "<TX> snapshot# ",self.snapCount," -> ", client.getAddress()
            self.write(int(0),self.snapBuffer, client) # rencode lets me send objects??
        self.snapBuffer = []
        return task.again


    def ProcessData(self,datagram):
        I = DatagramIterator(datagram)
        clientAddress = datagram.getAddress().getIpString()
        msgID = I.getInt32() # what type of message
        data = rencode.loads(I.getString()) # data matching msgID
#        print t0,msgID,data
        if msgID == 10: print data
        if msgID == 25:
            # add new player
            pc = Player(data) #data is the ID of the client
            pc.root.setPos(64,64,0)
            self.players.update({clientAddress:pc})
            print clientAddress, pc.ID, " added to server players"
        if msgID == 26: # This is a control snapshot from client X
            self.players[clientAddress].controls = data
            
if __name__ == '__main__':
    server = TileServer()
#    nMgr = NPCmanager()
#    server.run()
    taskMgr.run()

