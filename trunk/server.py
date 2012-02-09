# -*- coding: utf-8 -*-
"""
Created on Mon Nov 28 13:24:03 2011

@author: us997259
"""

import time,random

from direct.showbase.ShowBase import taskMgr
#from direct.showbase.DirectObject import DirectObject
from panda3d.core import *
from panda3d.ai import *

from common.player import Player
from common.Gatherer import Gatherer
from common.loadObject import loadObject

import network.rencode as rencode
from network.client import NetServer
from maptile import MapTile
from CONSTANTS import *

NUM_NPC = 10
#SERVER_TICK = 0.0166 # seconds
#SNAP_INTERVAL = 1.0/20
#TX_INTERVAL = 1.0/20
#
## Player control constants
#TURN_RATE = 120    # Degrees per second
#WALK_RATE = 8
#PLAYER_START_POS = (64,64)

# THIS MAP SETTINGS
_mapName='map3'

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
        self.cTrav = None
#        self.cTrav = CollisionTraverser('Server Collision Traversal')
#        self.pusher = CollisionHandlerPusher()
        
        taskMgr.doMethodLater(SERVER_TICK,self.calcTick,'calc_tick')
        taskMgr.doMethodLater(SNAP_INTERVAL,self.takeSnapshot,'SnapshotTsk')
        taskMgr.doMethodLater(TX_INTERVAL,self.sendThrottle,'TXatRate')

        print "[TileServer]::Ready"
        
    def setAI(self):
        #Creating AI World
        self.AIworld = AIWorld(self.root)
#        for obj in self.mapTile.staticObjs[0:1]:
#            self.AIworld.addObstacle(obj)

        for n in range(NUM_NPC):
            newAI = Gatherer("NPC"+str(n),'resources/models/golfie.x',.6)
            newAI.setCenterPos(Vec3(64,64,30))
            newAI.np.setPos(70,70,0)
            newAI.np.setTag('ID',str(n))

            tx = random.randint(0,128)
            ty = random.randint(0,128)
            newAI.setResourcePos(Vec3(tx,ty,35))
            newAI.request('ToResource')
            self.npc.append( newAI )
            self.AIworld.addAiChar(newAI.AI)
#            self.seeker.loop("run") # starts actor animations
        
    def calcTick(self,task):
        tnow = time.time()
        self.tickCount += 1
        dt = tnow - self.tlast
#        print dt

        for player in self.players.values():        
            player.np.setPos(player.np, WALK_RATE*player.controls['strafe']*dt,WALK_RATE*player.controls['walk']*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
            player.np.setH(player.np, player.controls['mouseTurn'] + TURN_RATE*player.controls['turn']*dt)
            x,y,z = player.np.getPos()
            player.np.setZ(self.mapTile.terGeom.getElevation(x,y))

        self.AIworld.update()
        print self.npc[0].state
        
        if self.cTrav:
            self.cTrav.traverse(self.root)

        self.tlast = tnow 
        return task.again

    def takeSnapshot(self,task):
#        print time.clock()
        self.snapCount += 1
        snapshot = [self.snapCount]
        # snapshot format [tick,(objectID,x,y,z),(ObjID,x..),...]
        for player in self.players.values():
            x,y,z = player.np.getPos()
            h,p,r = player.np.getHpr()
            snapshot.append((player.ID,x,y,z,h,p,r))
        for iNpc in self.npc:
            x,y,z = iNpc.np.getPos()
            z = self.mapTile.terGeom.getElevation(x,y)
            h,p,r = iNpc.np.getHpr()
            snapshot.append((int(iNpc.np.getTag('ID')),x,y,z,h,p,r))
        self.snapBuffer.append(snapshot)
        # snapBuffer = [snapshot1, snapshot2,...snapshotN] #since last TX

        return task.again

    def sendThrottle(self,task):
        for client in self.activeConnections:
#            print "<TX> snapshot# ",self.snapCount," -> ", client.getAddress()
            self.write(int(0),self.snapBuffer, client) 
        self.snapBuffer = []
        return task.again

    def spawnNewPlayer(self, name):
        #TODO: ADD CHECK IF THIS A A RECONNECT
        pObj = Player(name) #data is the ID of the client
        pObj.np.setPos(PLAYER_START_POS[0],PLAYER_START_POS[1],0)
        if self.cTrav:
            self.pusher.addCollider(pObj.cnp, pObj.np)  
            self.cTrav.addCollider(pObj.cnp, self.pusher)
        return pObj
        
    def ProcessData(self,datagram):
        I = DatagramIterator(datagram)
        clientAddress = datagram.getAddress().getIpString()
        msgID = I.getInt32() # what type of message
        data = rencode.loads(I.getString()) # data matching msgID
#        print t0,msgID,data
        if msgID == 10: print data
        if msgID == 25: 
            pc = self.spawnNewPlayer(data) # add new player
            self.players.update({clientAddress:pc})
            self.write(int(2),_mapName,datagram.getConnection())
            print clientAddress, pc.ID, " added to server players"

        if msgID == 26: # This is a control snapshot from client X
            self.players[clientAddress].controls = data
#            print self.players[clientAddress].controls['turn']
            
if __name__ == '__main__':
    server = TileServer()
#    nMgr = NPCmanager()
#    server.run()
    taskMgr.run()

