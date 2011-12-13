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
    
from panda3d.core import *
    
cManager = QueuedConnectionManager()
cReader = QueuedConnectionReader(cManager,0)
cWriter = ConnectionWriter(cManager,0)
    
port_address=9099  # same for client and server
 
 # a valid server URL. You can also use a DNS name
 # if the server has one, such as "localhost" or "panda3d.org"
ip_address="127.0.0.1"
 
 # how long until we give up trying to reach the server?
timeout_in_miliseconds=3000  # 3 seconds
 
myConnection=cManager.openTCPClientConnection(ip_address,port_address,timeout_in_miliseconds)
if myConnection:
  cReader.addConnection(myConnection)  # receive messages from server

while(1): print "Client Loop"  
#cManager.closeConnection(myConnection)