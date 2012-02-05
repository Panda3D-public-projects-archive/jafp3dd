#!/usr/local/bin/python
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 31 20:41:34 2012

@author: shawn
"""

import random

from direct.showbase import Loader
from panda3d.core import VBase4, CollisionNode, CollisionSphere
from direct.showbase.DirectObject import DirectObject

loader = Loader.Loader(DirectObject)

def loadObject(modelName,modelScale,objName=None):
    color = (VBase4(random.random(),random.random(),random.random(),1))
    model = loader.loadModel(modelName)
#TODO: Load ACTORS as well as static models...        
    model.setScale(modelScale)
    model.setColor(color)
    
    if objName: model.setName(objName)
    return model
