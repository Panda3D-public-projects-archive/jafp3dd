# -*- coding: utf-8 -*-
"""
Created on Mon Nov 28 13:24:03 2011

@author: us997259
"""

import time

#import direct.directbase.DirectStart
from direct.showbase.ShowBase import taskMgr
#from direct.showbase.DirectObject import DirectObject
#import direct.directbase.DirectStart
from panda3d.core import *
from panda3d.ai import *

from common.NPC import DynamicObject, Player
import network.rencode as rencode
from network.client import NetServer
from maptile import MapTile

#loadPrcFileData("", "want-directtools #t")
#loadPrcFileData("", "want-tk #t")

NUM_NPC = 10
SERVER_TICK = 0.0166 # seconds
SNAP_INTERVAL = 1.0/20
TX_INTERVAL = 1.0/20

# Player control constants
TURN_RATE = 120    # Degrees per second
WALK_RATE = 8
PLAYER_START_POS = (64,64)

# THIS MAP SETTINGS
_mapName='map2'

class TileServer(NetServer):
    def __init__(self):
        NetServer.__init__(self)
        self.root = NodePath(PandaNode('ServerRoot'))
        self.tickCount = 0
        self.snapCount = 0
        self.tlast = time.time()
        self.snapBuffer = []
        self.nextTx = 0
        self.npc = []
        self.players = dict()
        self.terGeom = None       
        self.mapTile = MapTile('TileServerX',_mapName, self.root)

        self.setAI()
        
        taskMgr.doMethodLater(SERVER_TICK,self.calcTick,'calc_tick')
        taskMgr.doMethodLater(SNAP_INTERVAL,self.takeSnapshot,'SnapshotTsk')
        taskMgr.doMethodLater(TX_INTERVAL,self.sendThrottle,'TXatRate')

    def setAI(self):
        #Creating AI World
        self.AIworld = AIWorld(self.root)
#        for obj in self.mapTile.staticObjs[0:1]:
#            self.AIworld.addObstacle(obj)

        self.AIchar=[]
        self.AIbehaviors=[]
        for n in range(NUM_NPC):
            self.npc.append( DynamicObject('someguy'+str(n),'resources/models/golfie.x',.6,self.root) )
            self.npc[n].root.setPos(70,70,0)
            self.npc[n].ID = n
            self.AIworld.addObstacle(self.npc[n].root)
            
            self.AIchar.append( AICharacter("conie"+str(n),self.npc[n].root, 300, 0.05, 5))
            self.AIworld.addAiChar(self.AIchar[n])
            self.AIbehaviors.append( self.AIchar[n].getAiBehaviors())
            
            self.AIbehaviors[n].wander(5, 0, 10, .50)
#            self.AIbehaviors[n].obstacleAvoidance(1.0)    
#        self.AIworld.addObstacle(self.obstacle1)
        
#            self.seeker.loop("run") # starts actor animations
     
        #AI World update        
#        taskMgr.add(self.AIUpdate,"AIUpdate")
 
    #to update the AIWorld    
    def AIUpdate(self,task):
        self.AIworld.update()            
        return task.cont
        


    def calcTick(self,task):
        tnow = time.time()
        self.tickCount += 1
        dt = tnow - self.tlast
#        print dt

        for player in self.players.values():        
            player.root.setPos(player.root, WALK_RATE*player.controls['strafe']*dt,WALK_RATE*player.controls['walk']*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
            player.root.setH(player.root, player.controls['mouseTurn'] + TURN_RATE*player.controls['turn']*dt)
            x,y,z = player.root.getPos()
            player.root.setZ(self.mapTile.terGeom.getElevation(x,y))

        self.AIworld.update()
            
#        for iNpc in self.npc:
#            iNpc.setPos(iNpc,0,iNpc.speed*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
#            x,y,z = iNpc.root.getPos()
#            z = self.mapTile.terGeom.getElevation(x,y)
#            iNpc.root.setZ(z)
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
            x,y,z = iNpc.root.getPos()
            z = self.mapTile.terGeom.getElevation(x,y)
            h,p,r = iNpc.root.getHpr()
            snapshot.append((iNpc.ID,x,y,z,h,p,r))
        self.snapBuffer.append(snapshot)
        # snapBuffer = [snapshot1, snapshot2,...snapshotN] #since last TX

        return task.again
        
#    def NpcAI(self,task):
#        for iNpc in self.npc:
#            tnow = time.time()
#            if tnow > iNpc.nextUpdate:         # change direction and heading every so often
#                iNpc.makeChange(tnow)
#        return task.cont

    def sendThrottle(self,task):
        for client in self.activeConnections:
#            print "<TX> snapshot# ",self.snapCount," -> ", client.getAddress()
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
            pc.root.setPos(PLAYER_START_POS[0],PLAYER_START_POS[1],0)
            self.players.update({clientAddress:pc})
            print clientAddress, pc.ID, " added to server players"
        if msgID == 26: # This is a control snapshot from client X
            self.players[clientAddress].controls = data
#            print self.players[clientAddress].controls['turn']
            
if __name__ == '__main__':
    server = TileServer()
#    nMgr = NPCmanager()
#    server.run()
    taskMgr.run()

