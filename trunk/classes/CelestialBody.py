# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 14:11:56 2011

@author: us997259
"""
from sys import path
path.append('c:\Panda3D-1.7.2')
path.append('c:\Panda3D-1.7.2\\bin');

from panda3d.core import *
from math import sin,cos,pi,sqrt

class CelestialBody():
    period = 10  # seconds per revolution
    radius = 1.0 # arbitraty panda units
    declin = 0
    FOV = 1
    phase = 0
    dColor = VBase4(1,1,1,1)
    eColor = VBase4(0,0,0,0)
    aColor = VBase4(0,0,0,1)
    aMin = VBase4(0,0,0,1)
    dayColor = [] # only set this for a sun cycle object
    
    def __init__(self,lightNode,followNode, model=None,tex=None, radius=None,Fov=None,phase=None,eColor=None):
        # Requires 2 nodes: The nodepath to apply lighting to, the nodepath of the camera

        if radius: self.radius = radius
        if Fov: self.FOV = Fov
        if phase: self.phase = phase
        if eColor: self.eColor = eColor
        self.scFact = float(self.radius/self.FOV)
        self.lightNode = lightNode
        self.followNode = followNode    
        
        self.model = loader.loadModel(model)
        self.model.setScale(self.scFact) # keeps anglular span fixed
        self.model.reparentTo(render)
        self.model.setTwoSided(1)
        self.model.setCompass(render)
#        self.model.setH(-90)
        mat1 = Material()
        mat1.setEmission(self.eColor)
        self.model.setMaterial(mat1)
        if tex: 
            tex1 = loader.loadTexture(tex)
            self.model.setTexture(tex1)
            self.model.setTransparency(1)
        self.model.setBin("transparent",30)
#        self.model.showBounds()
        
#        if 0:
#            self.sunHaze = Fog("Sun Haze")
#            self.sunHaze.setColor((0,1,1,1))
#    #        myFog.setExpDensity(0.0035)
#            self.sunHaze.setLinearRange(0,100000)
#            self.sunHaze.setLinearFallback(0,100000,100000)
#            self.model.setFog(self.sunHaze)

        self.dlight = DirectionalLight('dlight')
        self.dlight.setColor(self.dColor)
#        self.dlight.setShadowCaster(True,512,512)
        self.dlnp = lightNode.attachNewNode(self.dlight)
#        self.dlnp.printHpr()
        self.dlnp.setH(90)
        self.lightNode.setLight(self.dlnp)
        
        self.alight = AmbientLight('alight')
        self.alight.setColor(self.aMin)
        self.alnp = lightNode.attachNewNode(self.alight)
        self.lightNode.setLight(self.alnp)     

# PRE WORK FOR SUNRISE/SET COLORING
#        self.slight = Spotlight('slight')
#        self.slight.setColor(VBase4(1, 0, 0, 1))
#        lens = PerspectiveLens()
#        self.slight.setLens(lens)
#        self.slnp = lightNode.attachNewNode(self.slight)
##        self.slnp.setPos(10, 20, 0)
#        self.slnp.lookAt(followNode)
#        self.slnp.showBounds()
#        lightNode.setLight(self.slnp)
        
    def updateTask(self,task):
        # assume X = +east -west, Y +N -S, Z +up; % 0,pi) is "day" phase
#        theta = 3*pi/4 + ((pi/2/self.period)*task.time) % pi/2
        theta = (2*pi/self.period)*task.time + self.phase
#        theta = .93*pi # DEBUG USE
        
        x = self.radius*cos(theta)
        sz = sin(theta)
        z = self.radius*sz
#        y = self.followNode.getY() + z + self.radius*sin(self.declin) # THIS IS NOT WORKING
        y = self.followNode.getY()
        horzLine = min(1,max(0,float(z/self.scFact)+1))
        
        self.model.setPos(x, y, z)
        self.model.lookAt(self.followNode)
        self.dlnp.setP(-theta*180/pi) 
        
        if theta%(2*pi) < pi:        
            self.alight.setColor(self.aMin + self.aColor*horzLine)
            self.dlight.setColor(self.dColor*horzLine)
        else:
#            self.alight.setColor(self.aMin)
            self.dlight.setColor(VBase4(0,0,0,1))
            
        if self.dayColor: base.setBackgroundColor(self.dayColor*horzLine)
        return task.cont