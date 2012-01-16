from sys import path
path.append('c:\Panda3D-1.7.2')
path.append('c:\Panda3D-1.7.2\\bin');

from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
import sys
from CelestialBody import CelestialBody
   

class World(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)
#        self.env = self.loader.loadModel("/c/Panda3D-1.7.2/models/environment.egg.pz")
#        self.env.reparentTo(self.render)
#        self.env.setScale(.25,.25,.25)
#        self.env.setPos(-8,42,0)
        self.setupRendering()
        self.setupModels()
        self.setupKeys()
        self.sun = CelestialBody(self.alight,self.dlight,self.dlnp,'./resources/models/plane','./resources/images/blueSun.png',base.camera)
        taskMgr.add(self.sun.updateTask,'sun task')
#        taskMgr.add(self.followSun,'folow')
        self.camera.setPos(200,200,10)
        
    def followSun(self,task):
        self.camera.lookAt(self.sun.model)
        return task.cont
        
    def setupModels(self):        
        self.terrain = GeoMipTerrain("MyTerrain")
        self.terrain.setHeightfield("./resources/terrain/mine_HM.png")
#        self.terrain.setColorMap("pink1024x32.png")
        tex1 = loader.loadTexture("./resources/terrain/mine_TX.png")
        self.terrain.getRoot().setTexture(tex1)
        self.terrain.getRoot().reparentTo(self.render)
        self.terrain.getRoot().setSz(10)
        self.terrain.generate()
        mat1 = Material()
        mat1.setShininess(1)
        mat1.setAmbient(VBase4(1,1,1,1))
        self.terrain.getRoot().setMaterial(mat1)
        
    def setupKeys(self):
        self.accept("escape",sys.exit)
        self.accept('r',camera.setPosHpr,[0,0,0,0,0,0])
        
    def setupRendering(self):
#        self.render.setShaderAuto()
        self.alight = AmbientLight('alight')
        self.alight.setColor(VBase4(.8,.8,.8,1))
        self.alnp = self.render.attachNewNode(self.alight)
        self.dlight = DirectionalLight('dlight')
        self.dlight.setColor(VBase4(.8,.8,.8,1))
        self.dlnp = self.render.attachNewNode(self.dlight)
        render.setLight(self.dlnp)       
        render.setLight(self.alnp)

W = World()
#W.useDrive()
W.camera.setPos(100,100,10)
W.run()
