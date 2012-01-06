# -*- coding: utf-8 -*-
"""
Created on Thu Dec 01 13:47:28 2011

@author: us997259
"""

from random import random
import pickle
from PDFImage import PDFImage

# TREE PARAMS
_scatter = 1
#_TreeDensity = 5/1000.0
_GridSpace = 2.4 # meters
_startSeeds = 15000    # if not in grid mode(scatter=false), best if this is an int^2
_growCycles = 8
_minAge = .75    #simpleTree.x is 1/2 meter tall scale=1
_maxAge = 3
_modelID = 'resources/models/sampleTree.bam'
_treeMap = './addcli_TM.png'
_treeMap = './uniform_TM.png'

def calcTileTrees(tileSize=None, minSep=None, Lx=None,Ly=None,numSeeds=_startSeeds, numCycles=_growCycles,minAge=_minAge,maxAge=_maxAge):  
    PM = PDFImage(_treeMap,tileSize) # Probability Map object

    if not Lx: 
        Lx = PM.A.shape[0] # no divisions will occur
        Ly = PM.A.shape[1]      # only need Lx for square tiling
    elif not Ly:
        Ly = Lx
        
        
    loc=[]
    D = {}
    for i in range(numSeeds):            
        loc.append([PM.getNewLocation()])
        loc[-1].append(min(maxAge,minAge + random())) # initial age/state=1
        loc[-1].append(_modelID)
        # Assign object location to a grid tile
        ij = (loc[-1][0][0]/Lx, loc[-1][0][1]/Ly)
        D.setdefault(ij,[]).append(loc[-1])
        print ij, loc[-1]
    return D
    

#def calcTileTrees(tileSize, minSep=None, numSeeds=0, numCycles=0):      
#    #Generate tree locations and spawn new tree locations on a growth cycle
#    # This is ultimately a server side application
#    
##    numTrees = int(tileSize**2 * density) # treeDensity is given in tree/sq unit
#    nGrid = int(tileSize / minSep)
#    pos = lambda x,y: ( minSep*x, minSep*min(nGrid,y+.5*(x%2)) )
#    _limit = (int(minSep), int(nGrid-minSep))
#    
#    # Plant original seeds    
#    loc = []
#    state=[]
#    if _scatter:
#        for i in range(numSeeds):
#            x = (random.randint(_limit[0],_limit[1]))            # could use random.sample to prevent duplicate (x,y)
#            y = (random.randint(_limit[0],_limit[1]))            # could use random.sample to prevent duplicate (x,y)
#    #        if x%2 and y<nGrid: y+=.5
#            loc.append((x,y))
#            state.append(min(_maxAge,_minAge + random.random())) # initial age/state=1
#    else:
#        
#        nCell= ceil(sqrt(numSeeds)) # number of cells per side
#        step = int((_limit[1]-_limit[0]) / nCell) # int size of each cell side
#        centerScatter = step/2
#        for x in range(_limit[0],_limit[1],step):
#            for y in range(_limit[0],_limit[1],step):
#                loc.append((step/2+x+centerScatter*random.uniform(-1,1), step/2+y+centerScatter*random.uniform(-1,1))) 
#                state.append(min(_maxAge,_minAge + random.random())) # initial age/state=1
#
#    #iterate over growth cycles
#    for ic in range(numCycles):
#        #iterate over existing locations and reseed
#        curLocs = tuple(loc)
#        for i, tree in enumerate(curLocs):
#            # age the current tree
#            state[i] = max(_minAge,min(_maxAge,state[i]+1))
#            # 8 locations of neighbors. N = position 1, going clockwise
#            # check if location available
#            # if not...skip turn for now?
#            dx = random.randint(-1,1)
#            dy = random.randint(-1,1)
#            newLoc = (min(_limit[1],max(_limit[0],tree[0]+dx)), max(_limit[0],min(_limit[1],tree[1]+dy))) # keep in bounds of tile area
#            if newLoc not in loc:
#                loc.append(newLoc)
#                state.append(min(_maxAge,_minAge + random.random())) # initial age/state=1
#        
#    cvtLoc = []
#    for L in loc:
#        # could make noise a func of minSep (.3333Minsep)
#        noise = (random.uniform(-1,1), random.uniform(-1,1))
#        cvtLoc.append(pos(L[0]+noise[0],L[1]+noise[1]))
#    print "add culling of center trees to generator func? do client side?"
#    return cvtLoc, state
#    


if __name__ == '__main__':
    #        treeLocs = calcTileTrees(self.Ltile,numClusters=100,numTrees=12,clusterRadius=50) # this will be a server call at some point
    treeLocs = calcTileTrees(minSep=_GridSpace,numSeeds=_startSeeds,Lx = 128)
    fip = open('../resources/map1/treeList.dat','wb')
    pickle.dump(treeLocs,fip)
    fip.close()
    print "Done"