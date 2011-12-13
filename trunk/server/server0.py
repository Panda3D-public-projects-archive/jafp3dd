# -*- coding: utf-8 -*-
"""
Created on Mon Nov 28 13:24:03 2011

@author: us997259
"""

# SETUP SOME PATH's
import sys
import platform
if platform.system() == 'Windows':
    sys.path.append('c:\Panda3D-1.7.2')
    sys.path.append('c:\Panda3D-1.7.2\\bin')
    _DATAPATH_ = "./resources"
else:
    sys.path.append('/usr/lib/panda3d')
    sys.path.append('/usr/share/panda3d')
    _DATAPATH_ = "/home/shawn/Documents/project0/resources"

from direct.showbase.ShowBase import ShowBase
#from direct.showbase.DirectObject import DirectObject
#import direct.directbase.DirectStart
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText


class serverApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.OSD = OnscreenText(text = str("Starting the world..."), pos = (0, 0.5), scale = 0.1, fg = (.8,.8,1,.5))       

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
        for con in self.activeConnections:
            if not self.cListener.isConnectionOk(con):
                self.cListener.removeConnection(con)
                self.activeConnections.remove(con)
                print "lost connection"

        if self.cListener.newConnectionAvailable():
            rendezvous = PointerToConnection()
            netAddress = NetAddress()
            newConnection = PointerToConnection()
            
            if self.cListener.getNewConnection(rendezvous,netAddress, newConnection):
                newConnection = newConnection.p()
                self.activeConnections.append(newConnection)
                self.cReader.addConnection(newConnection)
        self.OSD.setText(str(("Open Connections: ",len(self.activeConnections))))
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
                 print datagram
        return task.cont
        

server = serverApp()
server.run()
        
        
                