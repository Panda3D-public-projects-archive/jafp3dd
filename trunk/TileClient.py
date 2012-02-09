# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 19:06:16 2012

@author: shawn
"""
import random, time
from numpy import sign
import os
import cPickle as pickle

from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.showbase import PythonUtil
from direct.gui.OnscreenText import OnscreenText


from client import NetClient
from common.loadObject import loadObject
from network import rencode as rencode
from maptile import MapTile
#from server import SNAP_INTERVAL
from CONSTANTS import *

_Datapath = "resources"
_AVMODEL_ = os.path.join('models','MrStix.x')
LERP_INTERVAL = 1
_ghost = 0
_serversync = 0

class TileClient(NetClient):
    """ a Game Client mapTile object: a chunk of the world map and all associated NPCs"""
    # TileManager determines what tiles are in scope for rendering on the client

    # Some hacky global consts for now
    _block_size_ = 32    # for LOD chunking
    _lod_near = 96 # ideal = Fog min distance
    _lod_far = 150
    _brute = 1 # use brute force
    _tree_lod_far = 128
    
    def __init__(self, serverIP, name, myNode, mapDefName, focus=None):
        NetClient.__init__(self)
        self.root = PandaNode(name)
        self.np = NodePath(self.root)
#        self.osd = OnscreenText(text = '', pos = (0.9, 0.9), scale = 0.07, fg = (1,1,1,1))       

         # local loop if address = None
        ok = self.connect(serverIP)
         # objects like other PCs and dynObjs that move/change realtime
        self.dynObjs = dict()    # A dictionary of nodepaths representing the moving objects
        self.snapshot = dict()
        self.maxSnap = -1

        if _ghost:
            self.ghost = loadObject(os.path.join(_Datapath,_AVMODEL_),1,'ghost')
            self.ghost.reparentTo(self.np)
            self.ghost.setColor(0,0,1,.4,1)
            
            self.dynObjs.update({'ghost':self.ghost})
        self.avnp = loadObject(os.path.join(_Datapath,_AVMODEL_),1,'avnp')
        self.avnp.reparentTo(self.np)
        print "debug tileclient set av pos"
        self.avnp.setPos(64,64,0)  
        self.myNode = myNode
        self.dynObjs.update({myNode:self.avnp})      
        
#        self.mapTile = MapTile(name,mapDefName, self.root, self.avnp)
        self.mapTile = MapTile(name,mapDefName, self.root)

        taskMgr.add(self.mapTile.updateTerra,'GeoMIPupdate')


    def updateSnap(self):
        """update scene with maxSnapshot - Lerp interval. Always some amount of 
        time behind the latest server snapshot."""
        if self.maxSnap > 0 :
            snapNum = self.maxSnap - LERP_INTERVAL
#            print "Rendering from Snapshot: ",snapNum            
            snap = self.snapshot[snapNum+1] # get NEXT snapshot to interp to
#TODO: THIS IS NOT ROBUST TO LOST SNAPSHOTS. MAKE IT SO!
            for obj in snap: # update all objects in this snapshot
                ID,x,y,z,h,p,r = obj
#                z = self.mapTile.terGeom.getElevation(x,y)
                if ID == self.myNode: 
                    # calculate the prediction errors
#                    print "updating", ID
#                    print "Prediction Errors: ", self.avnp.getPos() - Point3(x,y,z)
#                    self.osd.setText(str(self.avnp.getPos() - Point3(x,y,z))) 
                    if _ghost:
                        self.dynObjs['ghost'].setPos(x,y,z)
                        self.dynObjs['ghost'].setHpr(h,p,r)
                    if _serversync:
                        iv = LerpPosHprInterval(self.avnp,SNAP_INTERVAL,(x,y,z),(h,p,r))
                        iv.start()
                else:
                    if ID not in self.dynObjs: # spawn new object
                        self.dynObjs.update({ID: loadObject('resources/models/Man.egg',.33,'little piggie')})
                        cnp = self.dynObjs[ID].attachNewNode(CollisionNode('model-collision'))
                        cnp.node().addSolid(CollisionSphere(0,0,1,.5))
#                        cnp.show()

                        self.dynObjs[ID].setPos(x,y,z)
                        self.dynObjs[ID].setHpr(h,p,r)
                        self.dynObjs[ID].reparentTo(self.np)
                    else:
                        ch,cp,cr = self.dynObjs[ID].getHpr() # current hpr's
                        h = PythonUtil.fitDestAngle2Src(ch, h)
                        i = LerpPosInterval(self.dynObjs[ID],SNAP_INTERVAL,(x,y,z))
                        i.start()
                        ih=self.dynObjs[ID].hprInterval(3*SNAP_INTERVAL,(h,p,r))
                        ih.start() # just trying both forms
    #                self.dynObjs[ID].printPos()

    # NETWORK DATAGRAM PROCESSING
    def ProcessData(self,datagram):
        I = DatagramIterator(datagram)
        msgID = I.getInt32()
        data = rencode.loads(I.getString()) # data matching msgID
        if msgID == 0:
            for entry in data:
                snapNum = entry.pop(0) # snapshot tick count
                if self.maxSnap < snapNum: self.maxSnap = snapNum
                self.snapshot.update({snapNum:entry})
        elif msgID == 2: 
            print msgID,data
        else:
            print msgID,'::',data
            