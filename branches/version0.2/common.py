# -*- coding: utf-8 -*-
"""
Created on Fri Feb 03 14:24:37 2012

@author: us997259
"""

import time,random

from direct.showbase.ShowBase import taskMgr
#from direct.showbase.DirectObject import DirectObject
from panda3d.core import *
from panda3d.ai import *

from CONSTANTS import *

class GmObject():
    """ fancy wrapper for nodepath that adds:
        Controls, """

    def __init__(self,modelName = None, controller=None, name=''):
        self.root = PandaNode(name + 'obj_node')
        if modelName:
            self.np = loader.loadModel(modelName)
            if self.np:
                self.cnp = self.np.attachNewNode(CollisionNode(name + '-coll-node'))
                self.cnp.node().addSolid(CollisionSphere(0,0,1,.5))
        if not self.np:
            self.np = NodePath(self.root)
        taskMgr.add(self.update,'update'+name)
        self.controller = controller

    def update(self,task):
#        print self.controller
        dt = globalClock.getDt()
        if self.controller:
            self.np.setPos(self.np,WALK_RATE*self.controller['strafe']*dt,WALK_RATE*self.controller['walk']*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
            self.np.setH(self.np,TURN_RATE*self.controller['turn']*dt) #key input steer

#        x,y,z = self.np.getPos()
#        (xp,yp,zp) = self.ijTile(x,y).root.getRelativePoint(self.np,(x,y,z))
#        self.np.setZ(self.ijTile(x,y).getElevation(x,y))

#        print self.controller
#        print('\n')
        return task.cont
        
class AIengine():
    def __init__(self):
        self.root = NodePath(PandaNode('AIengine'))
        self.tickCount = 0
        self.snapCount = 0
        self.tlast = time.time()
        self.snapBuffer = []
        self.nextTx = 0
        self.npc = []
        self.players = dict()
        self.terGeom = None       

        self.setAI()
        self.cTrav = None
#        self.cTrav = CollisionTraverser('Server Collision Traversal')
#        self.pusher = CollisionHandlerPusher()
        
        taskMgr.doMethodLater(SERVER_TICK,self.calcTick,'calc_tick')
        taskMgr.doMethodLater(SNAP_INTERVAL,self.takeSnapshot,'SnapshotTsk')
        taskMgr.doMethodLater(TX_INTERVAL,self.sendThrottle,'TXatRate')

        print "[AIENGINE]::Ready"
        
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
            newAI.setResourcePos(self.mapTile.staticObjs[random.choice(range(20))].getPos()) #Vec3(tx,ty,35)
            
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
            