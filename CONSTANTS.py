# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 14:50:01 2012

@author: us997259
"""
from os import path, getcwd


HOME_PATH = '' #os.getcwd()
RESOURCE_PATH = 'resources'
MAP_DEF_PATH = path.join(HOME_PATH,RESOURCE_PATH)
MODEL_PATH = path.join(HOME_PATH,RESOURCE_PATH,'models')
TEXTURE_PATH = path.join(HOME_PATH,RESOURCE_PATH,'textures')

MODEL_PATH = 'resources\models'
TEXTURE_PATH = 'resources\textures'

NUM_NPC = 10
SERVER_TICK = 0.0166 # seconds
SNAP_INTERVAL = 1.0/20
TX_INTERVAL = 1.0/20

# Player control constants
TURN_RATE = 120    # Degrees per second
WALK_RATE = 8
PLAYER_START_POS = (64,64)

#SERVER_IP = '192.168.1.188'
SERVER_IP = None

_terraScale = (10,10,100) # xy scaling not working right as of 12-10-11. prob the LOD impacts