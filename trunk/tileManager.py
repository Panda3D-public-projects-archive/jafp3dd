# -*- coding: utf-8 -*-
"""
Created on Thu Dec 01 15:38:44 2011

@author: us997259
"""
from panda3d.core import *
import time

#from common import NPC
#from maptile import MapTile

class MapTileManager:
    curIJ = (0,0)
    inScopeTiles = [curIJ]
    Lx = Ly = []        # Size of a "Tile" in world units
    addTileQueue = []
    removeTileQueue = []
    lastAddTime = 0
    
    def __init__(self, infoDict, focus, size, delay=1, **kwargs ):
        (self.Lx,self.Ly) = size #
        self.minAddDelay = delay
        self.tileInfo = infoDict    # dictionary keyed by 2D tile indices (0,0) thru (N,M)
        self.tiles = {}        # this IS the list of tiles (dict object)
        self.refreshTileList() # need to initialize the addlist
        self.focusNode = focus
        taskMgr.setupTaskChain('TileUpdates',numThreads=4,threadPriority=1,frameBudget=0.02,frameSync=True)
        taskMgr.add(self.updateTask,'TileManagerUpdates',taskChain='TileUpdates')

    def setupTile(self,**kwds):
        pass

    def addTile(self, tileID):
        if self.addTileQueue.__contains__(tileID): # you are asking for a real add item
            if not self.tiles.has_key(tileID) and self.tileInfo.has_key(tileID): # this is not already in the dictionary but is in the overall dictionary
                til = self.setupTile(tileID)
                if til:    # everything went OK creating the object
                    self.tiles.update({tileID:til})
            if tileID not in self.addTileQueue:
                print "addtile error"
            else:
                self.addTileQueue.remove(tileID) # pull it out of the list even if not in the dict(bad list entry)
        # REMOVE TILES FROM ADD LIST ONCE THEY ARE ADDED

    def removeTile(self,tileID):    # make this a background task eventually?
        if self.removeTileQueue.__contains__(tileID): # you are asking for a real remove item
            if self.tiles.has_key(tileID): # this is really in the dictionary
                removed = self.tiles.pop(tileID)
                del removed # MAKE SURE THE REMOVED OBJECT CLEANS ITSELF UP WITH A del Call!!!
            self.removeTileQueue.remove(tileID) # pull it out of the list even if not in the dict(bad list entry)
        
    def refreshTileList(self,radius=1):    # make this a background task ?
#       determine what the in range tile list should be and update it
        inScopeTiles = []
        for di in xrange(-radius,radius+1):
            for dj in xrange(-radius,radius+1):
                # GENERATING THE LIST FIRST ALLOW TO DO IN BACKGROUND TASK LATER
                # COMPARE CURRENT AAND NEW; CREATE AN "ADD" list and a REMOVE LIST
                # THE ADD/REMOVE TASKS CAN BE SET ON DIFFERENT PRIORITIES (remove low)
                # THIS WOULD ALSO ENABLE CACHING OF SOME SORT-don't remove until X
                newKey = ( max(0,self.curIJ[0]+di), max(0,self.curIJ[1]+dj) )
                if not self.tiles.has_key(newKey): # look for new key in current dict
                    if not self.addTileQueue.__contains__(newKey): # double check not in add list already
                        self.addTileQueue.append( newKey )    # add to the add list
#                        print "adding ", newKey
                if not inScopeTiles.__contains__(newKey):
                    inScopeTiles.append( newKey )        # build up the new list for later
        # Now check for removes from current
        for key in self.tiles.keys():
            if not inScopeTiles.__contains__(key):    # compare newlist to current,
                if not self.removeTileQueue.__contains__(key):    #double check again
                    self.removeTileQueue.append(key)        #remove currents not in newlist

    def ijTile(self,position):
        i = int(position[0] / self.Lx)
        j = int(position[1] / self.Ly)
        return i,j

#    def updatePos(self,position): # of the focus
#        self.curPos = position
#        self.curIJ = self.ijTile(position)

    def updateTask(self,task):
        # Update the current tile based on where our focus node moved
        self.curIJ = self.ijTile(self.focusNode.getPos())
        # Manage the tile list; add remove, etc
        self.refreshTileList()
        if self.addTileQueue and time.time()-self.lastAddTime > self.minAddDelay:
            self.addTile(self.addTileQueue[0])
            self.lastAddTime = time.time()
        elif self.removeTileQueue:
#            print "removing tiles from dict"
            self.removeTile(self.removeTileQueue[0])
        for tile in self.tiles.values():
            tile.updateTile(task)

        return task.cont


#class TerrainManager(MapTileManager):
#
#    def __init__(self,info, parentNode,tileScale=(1,1,1), **kwargs ):
#        MapTileManager.__init__(self,info, **kwargs)
#        self.parentNode = parentNode
#        self.tileScale = tileScale
#        self.focusNode = kwargs['focus']
#        self.addTile(self.curIJ)
#
#
#    def setupTile(self,tileID):
##TODO:        if self.tileInfo.has_key(tileID):
#        HFname,texList,Objects = self.tileInfo[tileID][0:3]
#
#        newTile = MapTile('mapTile',self.focusNode)
#        newTile.setPos(tileID[0]*self.Lx,tileID[1]*self.Ly,0)
#        newTile.reparentTo(self.parentNode)
#
#        newTile.setGeom(HFname, self.tileScale, position=(0,0,0))
#        newTile.setTexture(texList)
#        for obj in Objects:
##            r = random.randint(0,9)
##            obj[2] = 'resources/models/sampleTree'+str(r)+'.bam'    # DEBUG OVERRIDE TO TEST MODEL
#            newTile.addStaticObject(obj) # takes a an individual object for this tile
#
#        for n in range(1):
#            newTile.npcs.append( NPC('guy','resources/models/cone.egg',1,newTile) )
##TODO: HOW TO GET NPC INFO PER TILE FROM SERVER???
#
#        return newTile
