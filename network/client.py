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
    
class netClient(DirectObject):
    port_address=9099  # same for client and server
    ct = 0 
     # a valid server URL. You can also use a DNS name
     # if the server has one, such as "localhost" or "panda3d.org"
    ip_address="127.0.0.1"
     
     # how long until we give up trying to reach the server?
    timeout_in_miliseconds=3000  # 3 seconds

    def __init__(self,addr=None):
        DirectObject.__init__(self)
        self.cManager = QueuedConnectionManager()
        self.cReader = QueuedConnectionReader(self.cManager,0)
        self.cWriter = ConnectionWriter(self.cManager,0)
        print "netClient adding pollers..."
        taskMgr.add(self.tskReaderPolling,'Poll connection reader',-30)
        if addr: 
            self.connect(addr)
        print "netClient Initialization completed successfully!"
    
    def connect(self,addr=None):
        if addr:
            self.ip_address = addr
        print "netClient connecting to ", self.ip_address
        self.myConnection=self.cManager.openTCPClientConnection(self.ip_address,self.port_address,self.timeout_in_miliseconds)
        if self.myConnection:
          self.cReader.addConnection(self.myConnection)  # receive messages from server
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
    #            myProcessDataFunction(datagram)
                 print time.ctime(),' recv: ', datagram
                 I = DatagramIterator(datagram)
                 if I.getString() == 'pong':
                     self.ct += 1
                     self.write('ping',datagram.getConnection())
                 
        return task.cont

    def write(self,message,toCon=None):
        if self.myConnection or toCon:        
            datagram = NetDatagram()
            datagram.addString(message)
            self.cWriter.send(datagram, toCon or self.myConnection)
        

if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        addr = sys.argv[1]
    else:
        addr = '127.0.0.1'
    client = netClient(addr)

    
    client.write('ping')
    taskMgr.run()
    print "out of the loop somehow!"
    client.cManager.closeConnection(myConnection)