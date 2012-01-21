# -*- coding: utf-8 -*-
"""
Created on Sat Jan 14 11:13:58 2012

@author: shawn
Map definition file
MapDef should contain 
    the terrain tile information (ht maps and tile texture(s))
    static objects dictionary (treeloc for example)
    
main.py will call a ::loadMap(...) method
    loadMap will 
        "unload" the current map (nodePaths)
        load the terrain (new ttMgr)
        load the static objects (new objMgr)
"""

import os
import cPickle as pickle

_Datapath = 'resources'
_templ = '%s_%s.x%dy%d.%s' #terrain image name template
#_treePath = 'map1/treeList.dat'
_mapName='map3'
NUM_DIV = 1
TILE_SIZE = 128

def enumerateMapTiles(dirName,N,Objects):
    # map tiles must be saved in the format (dirName).hmXY.png 
    # with a matching texture (dirName).txXY.png
    dirName = os.path.join(_Datapath,dirName,dirName) # add dirName 2x, files are named MAPm/MAPm_HMmm
    tileList = {}
    for nx in range(N):
        for ny in range(N):
            tileList.update({(nx,ny):(_templ%(dirName,'HM',nx,ny,'png'), _templ%(dirName,'TX',nx,ny,'jpg'), Objects[(nx,ny)])})
    return tileList

if __name__ == "__main__":
    print "Getting Tree Loc's"       
    treefile = open(os.path.join('..',_Datapath,_mapName,'treeList.dat'))        
    treeLocs = pickle.load(treefile)
    treefile.close()
    
    tileInfo = enumerateMapTiles(_mapName,NUM_DIV,treeLocs)
    
    mdf = open(os.path.join('..',_Datapath,_mapName+'.mdf'),'wb')
    pickle.dump(tileInfo,mdf)
    mdf.close()    
    print "mdf created"