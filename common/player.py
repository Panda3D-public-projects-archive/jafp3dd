# -*- coding: utf-8 -*-
"""
Created on Fri Feb 03 14:24:37 2012

@author: us997259
"""

from panda3d.core import PandaNode, NodePath, CollisionNode, CollisionSphere


class Player():
    """ Objects that represent the game clients. Inputs from game client snapshots
    sent from the client app are used to update server PC object position, heading, state
    etcetera. The server calculated state is then included in the snapshot for that frame
    and sent out to all clients, including the source client"""
    
    def __init__(self,name):
        self.root = PandaNode('player_node')
        self.np = NodePath(self.root)
        self.cnp = self.np.attachNewNode(CollisionNode('plr-coll-node'))
        self.cnp.node().addSolid(CollisionSphere(0,0,1,.5))
        self.ID = name
        self.controls = {"turn":0, "walk":0, "autoWalk":0,"strafe":0,'camZoom':0,\
        'camHead':0,'camPitch':0, "mouseTurn":0, "mousePos":[0,0]}