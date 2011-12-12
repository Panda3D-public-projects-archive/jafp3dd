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

cManager = QueuedConnectionManager()
cListener = QueuedConnectionListener(cManager,0)
cReader = QueuedConnectionRead(cManager,0)