# -*- coding: utf-8 -*-
"""
Created on Thu Dec 01 13:47:28 2011

@author: us997259
"""

from random import random, randint
import pickle
from PDFImage import PDFImage

# TREE PARAMS
_scatter = 1
#_TreeDensity = 5/1000.0
_GridSpace = 2.4 # meters
_startSeeds = 15000    # if not in grid mode(scatter=false), best if this is an int^2
_growCycles = 8
_minAge = .33    #simpleTree.x is 1/2 meter tall scale=1
_maxAge = 3
_modelID = 'resources/models/sampleTree%d.bam'
#_treeMap = './addcli_TM.png'
_treeMap = './uniform_TM.png'
_mapName = 'map2'

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
        newX,newY = PM.getNewLocation()        
        loc.append([(newX%Lx, newY%Ly)]) # mod to tile dimensions to make local tile coordinates
        loc[-1].append(min(maxAge,minAge + random())) # initial age/state=1
        loc[-1].append(_modelID %(randint(0,9)))
        # Assign object location to a grid tile
        ij = (newX/Lx,newY/Ly)
        D.setdefault(ij,[]).append(loc[-1])
        print ij, loc[-1]
    return D

if __name__ == '__main__':
    #        treeLocs = calcTileTrees(self.Ltile,numClusters=100,numTrees=12,clusterRadius=50) # this will be a server call at some point
    treeLocs = calcTileTrees(minSep=_GridSpace,numSeeds=_startSeeds,Lx = 128)
    fip = open('../resources/'+_mapName+'/treeList.dat','wb')
    pickle.dump(treeLocs,fip)
    fip.close()
    print "Done"