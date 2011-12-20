# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 14:54:51 2011

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
from panda3d.core import *
    
    
class netClient(ShowBase):
    port_address=9099  # same for client and server
     
     # a valid server URL. You can also use a DNS name
     # if the server has one, such as "localhost" or "panda3d.org"
    ip_address="127.0.0.1"
     
     # how long until we give up trying to reach the server?
    timeout_in_miliseconds=3000  # 3 seconds

    def __init__(self,addr=None):
        ShowBase.__init__(self)
        self.closeWindow(self.win)
        if addr: self.ip_address = addr
        self.cManager = QueuedConnectionManager()
        self.cReader = QueuedConnectionReader(self.cManager,0)
        self.cWriter = ConnectionWriter(self.cManager,0)
        print "Adding pollers..."
        taskMgr.add(self.tskReaderPolling,'Poll connection reader',-30)
        print "connecting to ", self.ip_address
        self.connect()
        print "Initialization completed successfully!"
    
    def connect(self):
        self.myConnection=self.cManager.openTCPClientConnection(self.ip_address,self.port_address,self.timeout_in_miliseconds)
        if self.myConnection:
          self.cReader.addConnection(self.myConnection)  # receive messages from server

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
                 I = DatagramIterator(datagram)
                 if I.getString() == 'pong':
                     self.write('ping',datagram.getConnection())
                 
        return task.cont

    def write(self,message,toConnection):
        datagram = NetDatagram()
        datagram.addString(message)
        self.cWriter.send(datagram, toConnection)
        

client = netClient('127.0.0.1')
from time import sleep

client.write('ping',client.myConnection)
client.run()
print "out of the loop somehow!"
client.cManager.closeConnection(myConnection)