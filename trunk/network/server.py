# -*- coding: utf-8 -*-
"""
Created on Mon Nov 28 13:24:03 2011

@author: us997259
"""

import sys
from direct.showbase.ShowBase import taskMgr
from direct.showbase.DirectObject import DirectObject
#import direct.directbase.DirectStart
from panda3d.core import *


class serverApp(DirectObject):
    def __init__(self):
        DirectObject.__init__(self)
#        self.OSD = OnscreenText(text = str("Starting the world..."), pos = (0.5, 0.5), scale = 0.5, fg = (.8,.8,1,.5))       
        print "Starting the world..."
        port_address = 9099
        backlog = 1000 
        self.activeConnections = []
        
        print "Starting up the connections..."
        self.cManager = QueuedConnectionManager()
        self.cListener = QueuedConnectionListener(self.cManager,0)
        self.cReader = QueuedConnectionReader(self.cManager,0)
        self.cWriter = ConnectionWriter(self.cManager,0)

        tcpSocket = self.cManager.openTCPServerRendezvous(port_address,backlog)        
        self.cListener.addConnection(tcpSocket)
        print "Adding pollers..."
        taskMgr.add(self.tskListenerPolling,'Poll connection listener',-39)
        taskMgr.add(self.tskReaderPolling,'Poll connection reader',-40)
        print "Initialization completed successfully!"
        
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
#        self.OSD.setText( "Open Connections: %d" % (len(self.activeConnections)) )
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
    #            myProcessDataFunction(datagram)
                 
                 I = DatagramIterator(datagram)
                 ds = I.getString()
                 print ds
                 if ds == 'ping':
                     print "request recv - replying..."
                     self.write('pong',datagram.getConnection())
            
        return task.cont

    def write(self,message, toConnection):
##TO DO: SERVER SIDE NEEDS TO KNOW WHERE TO SEND THE MESSAGE        
        datagram = NetDatagram()
        datagram.addString(message)
        self.cWriter.send(datagram, toConnection)
        

server = serverApp()
#server.run()
taskMgr.run()
        
        
                