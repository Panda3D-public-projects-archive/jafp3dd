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


from client import NetClient
from common.NPC import DynamicObject
from network import rencode as rencode
from server import SNAP_INTERVAL, TURN_RATE
from maptile import MapTile

_Datapath = "resources"
_AVMODEL_ = os.path.join('models','MrStix.x')
#SERVER_IP = '192.168.1.188'
SERVER_IP = None
LERP_INTERVAL = 1
_ghost = 1

class TileClient(NetClient):
    """ a Game Client mapTile object: a chunk of the world map and all associated NPCs"""
    # TileManager determines what tiles are in scope for rendering on the client

    # Some hacky global consts for now
    _block_size_ = 32    # for LOD chunking
    _lod_near = 96 # ideal = Fog min distance
    _lod_far = 150
    _brute = 1 # use brute force
    _tree_lod_far = 128
    
    def __init__(self, name, myNode, mapDefName, focus=None):
        NetClient.__init__(self)
        self.root = NodePath(PandaNode(name))
        
         # local loop if address = None
        ok = self.connect(SERVER_IP)
         # objects like other PCs and dynObjs that move/change realtime
        self.dynObjs = dict()    # A dictionary of nodepaths representing the moving objects
        self.snapshot = dict()
        self.maxSnap = -1

        if _ghost:
            self.ghost = DynamicObject('ghostnode', os.path.join(_Datapath,_AVMODEL_),1)
            self.ghost.root.reparentTo(self.root)
#            self.ghost.setColor(0,0,1,.4,1)
            self.dynObjs.update({'ghost':self.ghost})
        av = DynamicObject('AVNP', os.path.join(_Datapath,_AVMODEL_),1)
        self.avnp = av.root
        self.avnp.reparentTo(self.root)
        print "debug tileclient set av pos"
        self.avnp.setPos(64,64,0)  
        self.myNode = myNode
        self.dynObjs.update({myNode:self.avnp})      
        
        self.mapTile = MapTile(name,mapDefName, self.root, self.avnp)
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
                    if _ghost:
                        self.dynObjs['ghost'].root.setPos(x,y,z)
                        self.dynObjs['ghost'].root.setHpr(h,p,r)
#                    self.avnp.setPos(x,y,z)
#                    self.avnp.setHpr(h,p,r)
                  
                else:
                    if ID not in self.dynObjs: # spawn new object
                        self.dynObjs.update({ID: DynamicObject('guy','resources/models/golfie.x',.6,self.root)})
                        self.dynObjs[ID].root.setPos(x,y,z)
                        self.dynObjs[ID].root.setHpr(h,p,r)
                    else:
                        ch,cp,cr = self.dynObjs[ID].root.getHpr() # current hpr's
                        h = PythonUtil.fitDestAngle2Src(ch, h)
                        i = LerpPosInterval(self.dynObjs[ID].root,SNAP_INTERVAL,(x,y,z))
                        i.start()
                        ih=self.dynObjs[ID].root.hprInterval(3*SNAP_INTERVAL,(h,p,r))
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
        else:
            print msgID,'::',data
            