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
_treePath = 'map1/treeList.dat'
_mapName='map3'

def enumerateMapTiles(dirName,N):
    # map tiles must be saved in the format (dirName).hmXY.png 
    # with a matching texture (dirName).txXY.png
    dirName = os.path.join(_Datapath,dirName,dirName) # add dirName 2x, files are named MAPm/MAPm_HMmm
    tileList = {}
    for nx in range(N):
        for ny in range(N):
            tileList.update({(nx,ny):(_templ%(dirName,'HM',nx,ny,'png'), _templ%(dirName,'TX',nx,ny,'png'))})
    return tileList

if __name__ == "__main__":
    print "Getting Tree Loc's"       
    treefile = open(os.path.join('..',_Datapath,_treePath))        
    treeLocs = pickle.load(treefile)
    treefile.close()
    
    tileInfo = enumerateMapTiles(_mapName,1)
    
    mdf = open(os.path.join('..',_Datapath,_mapName+'.mdf'),'wb')
    pickle.dump([treeLocs,tileInfo],mdf)
    mdf.close()    
    print "mdf created"