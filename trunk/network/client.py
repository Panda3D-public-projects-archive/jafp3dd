# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 14:54:51 2011

@author: us997259
"""


# SETUP SOME PATH's
import sys
import time
from direct.showbase.ShowBase import taskMgr
from direct.showbase.DirectObject import DirectObject
from panda3d.core import *
import rencode # from Thomas Egi??? on Panda3d IRC. Let me know so I can credit!

class NetClient(DirectObject):
    port_address=9099  # same for client and server
     # a valid server URL. You can also use a DNS name
     # if the server has one, such as "localhost" or "panda3d.org"
    ip_address="127.0.0.1"

     # how long until we give up trying to reach the server?
    timeout_in_miliseconds=3000  # 3 seconds

    def __init__(self,addr=None):
        DirectObject.__init__(self)

        print "[NetClient]::Starting up Network Managers..."
        self.cManager = QueuedConnectionManager()
        self.cReader = QueuedConnectionReader(self.cManager,0)
        self.cWriter = ConnectionWriter(self.cManager,0)
        print "[NetClient]::netClient adding pollers..."
        taskMgr.add(self.tskReaderPolling,'Poll connection reader',-30)
        if addr:
            self.connect(addr)
        print "[NetClient]::Initialization completed successfully!"

    def connect(self,addr=None):
        if addr:
            self.ip_address = addr
        print "[NetClient]::Connecting to ", self.ip_address
        self.myConnection=self.cManager.openTCPClientConnection(self.ip_address,self.port_address,self.timeout_in_miliseconds)
        if self.myConnection:            
            self.cReader.addConnection(self.myConnection)  # receive messages from server
            return 1
        else:
            print "[NetClient]::Unable to Connect]"
            return 0
        
    def disconnect(self):
        self.cManager.closeConnection(myConnection)

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

    def ProcessData(self,datagram):
        pass
#        print time.ctime(),' <recv> ',
#        print "</>"

#    def write(self,messageID,data,toCon=None):
#        if self.myConnection or toCon:
#            datagram = NetDatagram()
#            datagram.addInt32(messageID)
#            datagram.addString(rencode.dumps(data,False))
#            self.cWriter.send(datagram, toCon or self.myConnection)

    def write(self,messageID, data, connection=None):
#TODO: SERVER SIDE NEEDS TO KNOW WHERE TO SEND THE MESSAGE
        # a none entry results in a broadcast to all active clients
        if not connection: connection = self.activeConnections
        datagram = NetDatagram()
        datagram.addInt32(messageID)
        datagram.addString(rencode.dumps(data,False))
        self.cWriter.send(datagram, connection)


#TODO: MOve Lost Connection tsk into base NetClient class??
class NetServer(NetClient):
    backlog = 1000
    activeConnections = []

    def __init__(self):
        NetClient.__init__(self)
        self.cListener = QueuedConnectionListener(self.cManager,0)
        tcpSocket = self.cManager.openTCPServerRendezvous(self.port_address,self.backlog)
        self.cListener.addConnection(tcpSocket)
        print "[NetServer]::Adding pollers..."
        taskMgr.add(self.tskListenerPolling,'Poll connection listener',-39)

        taskMgr.doMethodLater(1,self.tskCheckConnect,'Check for lost connections')        
        chain = taskMgr.mgr.findTaskChain("default") 
        chain.setTickClock(True)
        print "[NetServer]::listening!"
 
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

    def tskCheckConnect(self,task):
        if self.cManager.resetConnectionAvailable() == True:
            ptc = PointerToConnection()
            self.cManager.getResetConnection(ptc)
            con = ptc.p()
          
            if con in self.activeConnections:
                self.activeConnections.remove(con)
                print self.activeConnections
            print "-XX- Client " ,con.getAddress(), "disconnected -XX-"
            self.cManager.closeConnection(con)
        return task.again
        





#
#
#
#
#class NetServer(DirectObject):
#    def __init__(self):
#        DirectObject.__init__(self)
#        port_address = 9099
#        self.activeConnections = []
#
#        print "Starting up Server Network Managers..."
#        self.cManager = QueuedConnectionManager()
#        self.cListener = QueuedConnectionListener(self.cManager,0)
#        self.cReader = QueuedConnectionReader(self.cManager,0)
#        self.cWriter = ConnectionWriter(self.cManager,0)
#
#        tcpSocket = self.cManager.openTCPServerRendezvous(port_address,backlog)
#        self.cListener.addConnection(tcpSocket)
#        print "Server Adding pollers..."
#        taskMgr.add(self.tskListenerPolling,'Poll connection listener',-39)
#        taskMgr.add(self.tskReaderPolling,'Poll connection reader',-40)
#        taskMgr.doMethodLater(1,self.tskCheckConnect,'Check for lost connections')
#        
#        chain = taskMgr.mgr.findTaskChain("default") 
#        chain.setTickClock(True)
#        print "Server listening!"
#
#    def tskListenerPolling(self,task):
##        for con in self.activeConnections:
##            if not self.cListener.isConnectionOk(con):
##                self.cListener.removeConnection(con)
##                self.activeConnections.remove(con)
##                print "lost connection"
#
#        if self.cListener.newConnectionAvailable():
#            rendezvous = PointerToConnection()
#            netAddress = NetAddress()
#            newConnection = PointerToConnection()
#
#            if self.cListener.getNewConnection(rendezvous,netAddress, newConnection):
#                newConnection = newConnection.p()
#                self.activeConnections.append(newConnection)
#                self.cReader.addConnection(newConnection)
#            print "Open Connections: %d" % (len(self.activeConnections))
#        return task.cont
#
#    def tskReaderPolling(self,task):
#        if self.cReader.dataAvailable():
#            datagram = NetDatagram()
#            #Note that the QueuedConnectionReader retrieves data from all clients
#            #connected to the server. The NetDatagram can be queried using
#            #NetDatagram.getConnection to determine which client sent the message.
#
#            # check return value incase other thread grabbed data first
#            if self.cReader.getData(datagram):
#                self.ProcessData(datagram)
#        return task.cont
#
#    def tskCheckConnect(self,task):
#        if self.cManager.resetConnectionAvailable() == True:
#            ptc = PointerToConnection()
#            self.cManager.getResetConnection(ptc)
#            con = ptc.p()
#          
#            if con in self.activeConnections:
#                self.activeConnections.remove(con)
#                print self.activeConnections
#            print "CS: Client disconnected" ,con
#            self.cManager.closeConnection(con)
#        return task.again
#        
#    def write(self,messageID, data, connection=None):
#        # a none entry results in a broadcast to all active clients
#        if not connection: connection = self.activeConnections
##TODO: SERVER SIDE NEEDS TO KNOW WHERE TO SEND THE MESSAGE
#        datagram = NetDatagram()
#        datagram.addInt32(messageID)
#        datagram.addString(rencode.dumps(data,False))
#        self.cWriter.send(datagram, connection)
#
#    def ProcessData(self,NetDatagram):
#        pass
#

if __name__ == '__main__':

    if len(sys.argv) > 1:
        addr = sys.argv[1]
    else:
        addr = '127.0.0.1'
    client = NetClient(addr)


    client.write(int(1000),'ping',client.myConnection)
    taskMgr.run()
    print "out of the loop somehow!"
    client.cManager.closeConnection(myConnection)