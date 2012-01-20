# -*- coding: utf-8 -*-
"""
Created on Mon Nov 28 13:24:03 2011

@author: us997259
"""

import time,random,os

from direct.showbase.ShowBase import taskMgr, ShowBase
from direct.showbase.DirectObject import DirectObject
#import direct.directbase.DirectStart
from panda3d.core import *

import rencode

NUM_NPC = 6
SERVER_TICK = 15.0/1000 # seconds

class serverNPC(NodePath):
# Data needed to sync: x,y,z,h,p,r,speed

    nextUpdate = 0
    speed = 0
    def __init__(self,name):
        NodePath.__init__(self, name)
        self.ID = os.urandom(16)
#        print self.ID
        
    def makeChange(self,ttime):
        self.speed = 4*abs(random.gauss(0,.33333))
        newH = random.gauss(0,60)
        self.setH(self,newH) #key input steer
        self.nextUpdate = ttime + 2 # randomize when to update next

#   FOR BUFFERED DYNOBJECT:: ADD!       
#    def fakeAIchange(self,ttime):
#        Q = Quat()
#        newH = random.gauss(-180,180)
#        Q.setHpr((newH,0,0))
#        # GET CUR VELOC VECTOR to MULTUPLE WITH Quat
#        self.speed = 3*abs(random.gauss(0,.33333))
#        self.updateCommandsBuffer(ttime,[self.getPos(),Q.getForward()*self.speed,Vec3(0,0,0)])
#        self.nextUpdate = ttime + 10*random.random() # randomize when to update next

class ServerApp(DirectObject):
    def __init__(self):
        DirectObject.__init__(self)
        print "Starting the world..."
        port_address = 9099
        backlog = 1000
        self.activeConnections = []

        print "Starting up Server Network Managers..."
        self.cManager = QueuedConnectionManager()
        self.cListener = QueuedConnectionListener(self.cManager,0)
        self.cReader = QueuedConnectionReader(self.cManager,0)
        self.cWriter = ConnectionWriter(self.cManager,0)

        tcpSocket = self.cManager.openTCPServerRendezvous(port_address,backlog)
        self.cListener.addConnection(tcpSocket)
        print "Server Adding pollers..."
        taskMgr.add(self.tskListenerPolling,'Poll connection listener',-39)
        taskMgr.add(self.tskReaderPolling,'Poll connection reader',-40)
        taskMgr.doMethodLater(1,self.tskCheckConnect,'Check for lost connections')
        print "Server listening!"

    def tskListenerPolling(self,task):
#        for con in self.activeConnections:
#            if not self.cListener.isConnectionOk(con):
#                self.cListener.removeConnection(con)
#                self.activeConnections.remove(con)
#                print "lost connection"

        if self.cListener.newConnectionAvailable():
            rendezvous = PointerToConnection()
            netAddress = NetAddress()
            newConnection = PointerToConnection()

            if self.cListener.getNewConnection(rendezvous,netAddress, newConnection):
                newConnection = newConnection.p()
                self.activeConnections.append(newConnection)
                self.cReader.addConnection(newConnection)
            print "Open Connections: %d" % (len(self.activeConnections))
        return task.cont

    def tskReaderPolling(self,task):
        if self.cReader.dataAvailable():
            datagram = NetDatagram()
            #Note that the QueuedConnectionReader retrieves data from all clients
            #connected to the server. The NetDatagram can be queried using
            #NetDatagram.getConnection to determine which client sent the message.

            # check return value incase other thread grabbed data first
            if self.cReader.getData(datagram):
                self.ProcessData(datagram)
        return task.cont

    def tskCheckConnect(self,task):
        print "in check"
        if self.cManager.resetConnectionAvailable() == True:
            ptc = PointerToConnection()
            self.cManager.getResetConnection(ptc)
            con = ptc.p()
          
            if con in self.activeConnections:
                self.activeConnections.remove(con)
                print self.activeConnections
            print "CS: Client disconnected" ,con
            self.cManager.closeConnection(con)
        return Task.again
        
    def write(self,messageID, data, connection=None):
        # a none entry results in a broadcast to all active clients
        if not connection: connection = self.activeConnections
#TODO: SERVER SIDE NEEDS TO KNOW WHERE TO SEND THE MESSAGE
        datagram = NetDatagram()
        datagram.addInt32(messageID)
        datagram.addString(rencode.dumps(data,False))
        self.cWriter.send(datagram, connection)

    def ProcessData(self,NetDatagram):
        pass


class TileServer(ServerApp):
    def __init__(self):
        ServerApp.__init__(self)
        self.tickCount = 0
        self.sendBuffer = []
        self.nextTx = 0
        self.npc = []
        for n in range(NUM_NPC):
            self.npc.append( serverNPC('thisguy'+str(n)))
            self.npc[n].setPos(70,70,0)
            self.npc[n].ID = n

        taskMgr.add(self.NpcAI,'server NPCs')
        taskMgr.doMethodLater(1.0,self.sendThrottle,'TXatRate')
        
    def ProcessData(self,datagram):
        t0 = time.ctime()
        I = DatagramIterator(datagram)
        msgID = I.getInt32() # what type of message
        data = rencode.loads(I.getString()) # data matching msgID
        print t0,msgID,data
        if msgID == 10: print data
#            self.write(t0,datagram.getConnection())

    def calcTick(self):
        self.tickCount += 1
        dt = task.getDt()
        data = []
        for iNpc in self.npc:
            iNpc.setPos(iNpc,0,iNpc.speed*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
            x,y,z = iNpc.getPos()
            h,p,r = iNpc.getHpr()
            data.append([self.tickCount,iNpc.ID,x,y,z,h,p,r,iNpc.speed])

        
    def NpcAI(self,task):
        dt = task.getDt()
        self.sendBuffer = []
        for iNpc in self.npc:
            tnow = time.time()
            if tnow > iNpc.nextUpdate:         # change direction and heading every so often
                iNpc.makeChange(time.time())
            iNpc.setPos(iNpc,0,iNpc.speed*dt,0) # these are local then relative so it becomes the (R,F,Up) vector
#            poslist.append(iNpc.getPos())
            x,y,z = iNpc.getPos()
            h,p,r = iNpc.getHpr()
#            iNpc.setZ(self.ttMgr.getElevation((x,y)))
#TODO: What to do about terrain heights???
            self.sendBuffer.append([self.tickCount,iNpc.ID,x,y,z,h,p,r,iNpc.speed])

    def sendThrottle(self,task):
        print "TX>"
        for client in self.activeConnections:
            self.write(int(0),self.sendBuffer, client) # rencode lets me send objects??
        self.sendBuffer = []
        return task.again





if __name__ == '__main__':
    server = TileServer()
#    nMgr = NPCmanager()
#    server.run()
    taskMgr.run()

