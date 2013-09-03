
#from pandac.PandaModules import loadPrcFileData
#loadPrcFileData('', 'load-display tinydisplay')

#loadPrcFileData('', 'bullet-additional-damping true')
#loadPrcFileData('', 'bullet-additional-damping-linear-factor 0.005')
#loadPrcFileData('', 'bullet-additional-damping-angular-factor 0.01')
#loadPrcFileData('', 'bullet-additional-damping-linear-threshold 0.01')
#loadPrcFileData('', 'bullet-additional-damping-angular-threshold 0.01')

import sys, random
from math import log

#from panda3d.core import loadPrcFileData
#loadPrcFileData("", "want-directtools #t")
#loadPrcFileData("", "want-tk #t")

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from direct.showbase.InputStateGlobal import inputState

from panda3d.core import AmbientLight
from panda3d.core import DirectionalLight
from panda3d.core import Vec3
from panda3d.core import Vec4
from panda3d.core import Point3
from panda3d.core import TransformState
from panda3d.core import BitMask32

from panda3d.bullet import BulletWorld
from panda3d.bullet import BulletPlaneShape, BulletTriangleMesh, BulletTriangleMeshShape
from panda3d.bullet import BulletBoxShape, BulletSphereShape, BulletCylinderShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletDebugNode

import common

#from panda3d.core import PStatClient
#PStatClient.connect()

NUM_MARBLES = 15
_KeyMap ={'jump':'space','action':'mouse1','left':'a','right':'d','strafe_L':'q','strafe_R':'e','wire':'z'}
sceneID = 'resources/groundg.egg'

class Game(DirectObject):
  mousePos = [0,0]
  mousePos_old = mousePos
  controls = {"turn":0, "walk":0, "strafe":0,"fly":0,'jump':0,\
      'camZoom':0,'camHead':0,'camPitch':0,\
      "mouseDeltaXY":[0,0],"mouseWheel":0,"mouseLook":False,"mouseSteer":False}
  objects = list()

  def __init__(self):
    base.setBackgroundColor(0.1, 0.1, 0.8, 1)
    base.setFrameRateMeter(True)

    # Light
    alight = AmbientLight('ambientLight')
    alight.setColor(Vec4(0.5, 0.5, 0.5, 1)*.2)
    alightNP = render.attachNewNode(alight)

    dlight = DirectionalLight('directionalLight')
    dlight.setDirection(Vec3(1, 1, -1))
    dlight.setColor(Vec4(0.7, 0.7, 0.7, 1))
    dlightNP = render.attachNewNode(dlight)

    render.clearLight()
    render.setLight(alightNP)
    render.setLight(dlightNP)

    # Input

    self._setupKeys()
#    self.accept('r', self.doReset)
    self.accept('f2', self.toggleTexture)
    self.accept('f3', self.toggleDebug)
#    self.accept('f5', self.doScreenshot)

    # Task
    taskMgr.add(self.update, 'updateWorld')
    taskMgr.add(self.mouseHandler,'Mouse Manager')
    base.camera.setPos(0,-5,25)

    # Physics
    self.setup()

    # CAMERA
    base.camera.reparentTo(self.boxNP)
    base.camera.setCompass()
    self.camController = common.ControlledCamera(self.controls, base.camera, self.boxNP)

  def _setupKeys(self):

      self.accept(_KeyMap['left'],self._setControls,["camHead",1])
      self.accept(_KeyMap['left']+"-up",self._setControls,["camHead",0])
      self.accept(_KeyMap['right'],self._setControls,["camHead",-1])
      self.accept(_KeyMap['right']+"-up",self._setControls,["camHead",0])


      self.accept(_KeyMap['strafe_L'],self._setControls,["strafe",-1])
      self.accept(_KeyMap['strafe_L']+"-up",self._setControls,["strafe",0])
      self.accept(_KeyMap['strafe_R'],self._setControls,["strafe",1])
      self.accept(_KeyMap['strafe_R']+"-up",self._setControls,["strafe",0])

      self.accept(_KeyMap['jump'],self._setControls,["jump",1])
      self.accept(_KeyMap['jump']+'-up',self._setControls,["jump",0])

      self.accept("w",self._setControls,["walk",1])
      self.accept("s",self._setControls,["walk",-1])
      self.accept("s-up",self._setControls,["walk",0])
      self.accept("w-up",self._setControls,["walk",0])
      self.accept("r",self._setControls,["autoWalk",1])

      self.accept("page_up",self._setControls,["camPitch",-1])
      self.accept("page_down",self._setControls,["camPitch",1])
      self.accept("page_up-up",self._setControls,["camPitch",0])
      self.accept("page_down-up",self._setControls,["camPitch",0])
      self.accept("arrow_left",self._setControls,["camHead",-1])
      self.accept("arrow_right",self._setControls,["camHead",1])
      self.accept("arrow_left-up",self._setControls,["camHead",0])
      self.accept("arrow_right-up",self._setControls,["camHead",0])

      self.accept("arrow_down",self._setControls,["camZoom",1])
      self.accept("arrow_up",self._setControls,["camZoom",-1])
      self.accept("arrow_down-up",self._setControls,["camZoom",0])
      self.accept("arrow_up-up",self._setControls,["camZoom",0])

      self.accept(_KeyMap['action'],self.pickingFunc)
      self.accept("mouse3",self._setControls,["mouseLook",True])
      self.accept("mouse3-up",self._setControls,["mouseLook",False])
#      self.accept("mouse2",self._setControls,["mouseLook",True])
#      self.accept("mouse2-up",self._setControls,["mouseLook",False])
#      self.accept("mouse3",self._setControls,["mouseSteer",True])
#      self.accept("mouse3-up",self._setControls,["mouseSteer",False])

      self.accept("wheel_up",self._setControls,["mouseWheel",-1])
      self.accept("wheel_down",self._setControls,["mouseWheel",1])
  #        self.accept("wheel_up-up",self._setControls,["mouseWheel",0])
  #        self.accept("wheel_down-up",self._setControls,["mouseWheel",0])

      self.accept(_KeyMap['wire'],self.toggleWireframe)
      self.accept("escape",sys.exit)


  def _setControls(self,key,value):
    self.controls[key] = value
    # manage special conditions/states
    if key == 'autoWalk':
        if self.controls["walk"] == 0:
            self.controls["walk"] = 1
        else:
            self.controls["walk"] = 0
    if key == 'mouseWheel':
        cur = self.controls['mouseWheel']
        self.controls['mouseWheel'] = cur + value # add up mouse wheel clicks



  def mouseHandler(self,task):

    if base.mouseWatcherNode.hasMouse():
      self.mousePos_old = self.mousePos
      self.mousePos = [base.mouseWatcherNode.getMouseX(), \
      base.mouseWatcherNode.getMouseY()]
      dX = self.mousePos[0] - self.mousePos_old[0] # mouse horizontal delta
      dY = self.mousePos[1] - self.mousePos_old[1] # mouse vertical delta
      self.controls['mouseDeltaXY'] = [dX,dY]

      #TODO: ADD RAY TEST FOR FOCUS HERE

      return task.cont


  # _____HANDLER_____

  def doExit(self):
    self.cleanup()
    sys.exit(1)

  def doReset(self):
    self.cleanup()
    #TODO: FIX CLEANUP
    print ".cleanup() does not properly clear geomnodes of ground"
    self.setup()

  def toggleWireframe(self):
    base.toggleWireframe()

  def toggleTexture(self):
    base.toggleTexture()

  def toggleDebug(self):
    if self.debugNP.isHidden():
      self.debugNP.show()
    else:
      self.debugNP.hide()

  def doScreenshot(self):
    base.screenshot('Bullet')

  def pickingFunc(self):
    # Get to and from pos in camera coordinates
    pMouse = base.mouseWatcherNode.getMouse()
    pFrom = Point3()
    pTo = Point3()
    base.camLens.extrude(pMouse, pFrom, pTo)

    # Transform to global coordinates
    pFrom = render.getRelativePoint(base.cam, pFrom)
    pTo = render.getRelativePoint(base.cam, pTo)
    result = self.world.rayTestClosest(pFrom,pTo)
    if result:
      print result.getNode().getName()

  # ____TASK___

  def processInput(self, dt):
    force = Vec3(0, 0, 0)
    torque = Vec3(0, 0, 0)

    force.setY(self.controls['walk'])
#    force.setX(self.controls['strafe'])
#    torque.setZ(self.controls['turn'])
    if self.controls['jump']:
      result = self.world.contactTest(self.boxNP.node())
#      print result.getNumContacts()
      if result.getNumContacts() > 0:
        self.boxNP.node().applyCentralImpulse(Vec3(0,0,5))

    force *= 10.0
    torque *= 5.0

    force = render.getRelativeVector(camera, force)
#    torque = render.getRelativeVector(camera, torque)

    self.boxNP.node().setActive(True)
    self.boxNP.node().applyCentralForce(force)
    self.boxNP.node().applyTorque(torque)


  def update(self, task):
    dt = globalClock.getDt()
    self.processInput(dt)
    #self.world.doPhysics(dt)
    self.world.doPhysics(dt, 5, 1.0/180.0)
    self.marbleAI() # give them some sort of reactions
    return task.cont

  def cleanup(self):
    self.world.removeRigidBody(self.groundNP.node())
    self.world.removeRigidBody(self.boxNP.node())
    for o in self.objects:
      self.world.removeRigidBody(o.node())
    self.objects = list()
    self.world = None

#    self.debugNP = None
    self.groundNP = None
    self.boxNP = None

    self.worldNP.removeNode()


  def importBlenderScene(self,eggname):

      terrain = loader.loadModel(eggname)
      print terrain.ls()
      geomNodes = terrain.findAllMatches('**/+GeomNode')
      for geom in geomNodes:
          if not geom.node().getTag('isGhost'):
              geom.reparentTo(render)
          mesh = BulletTriangleMesh()
          mesh.addGeom(geom.node().getGeom(0))
          shape = BulletTriangleMeshShape(mesh,dynamic='false')
          self.groundNP = self.worldNP.attachNewNode(BulletRigidBodyNode(geom.node().getName()))
          self.groundNP.node().addShape(shape)
      #    self.groundNP.setPos(0, 0, -2)
          self.groundNP.setCollideMask(BitMask32.allOn())
          self.world.attachRigidBody(self.groundNP.node())

  def spawnMarble(self,name='',size=1.0,position=Vec3(0,0,0),color=Vec3(1,1,1)):
    # Ball2 (dynamic)
    shape = BulletSphereShape(0.45)
    ballnp = self.worldNP.attachNewNode(BulletRigidBodyNode(name))
    ballnp.setScale(size)
    ballnp.node().setMass(size**3)  # dynamic objects have mass; constant density -> m = scale***3
    ballnp.node().addShape(shape)
    ballnp.setPos(position)
    ballnp.setCollideMask(BitMask32.allOn())
    #ballnp.node().setDeactivationEnabled(False)
#    ballnp.node().setInertia(Vec3(.1,1e6,.1))
    self.world.attachRigidBody(ballnp.node()) # add to bullet world

    visualNP = loader.loadModel('models/ball.egg')
    visualNP.clearModelNodes()
    visualNP.reparentTo(ballnp)
    visualNP.setColor(color)

    return ballnp

  def marbleAI(self):
    for thismarble in self.objects:
      for thatmarble in self.objects:
        if not thismarble == thatmarble:
          delta = thismarble.getPos() - thatmarble.getPos()
          dist = delta.length()
          if dist < 10:
            Af = 10 / (dist**2)
          else:
            Af = 0.0
          delta.setZ(0)
          delta.normalize()
          force = delta * Af
          thismarble.node().setActive(True)
          thismarble.node().applyCentralForce(force)

  def setup(self):
    self.worldNP = render.attachNewNode('World')
    # World
    self.debugNP = self.worldNP.attachNewNode(BulletDebugNode('Debug'))
#    self.debugNP.show()
    self.debugNP.node().showWireframe(True)
    self.debugNP.node().showConstraints(True)
    self.debugNP.node().showBoundingBoxes(False)
    self.debugNP.node().showNormals(True)
    #self.debugNP.showTightBounds()
    #self.debugNP.showBounds()

    self.world = BulletWorld()
    self.world.setGravity(Vec3(0, 0, -9.81))
    self.world.setDebugNode(self.debugNP.node())

    # Ground (static)
#    shape = BulletPlaneShape(Vec3(0, 0, 1), 1)
    self.importBlenderScene(sceneID)

    # Player Ball
    self.boxNP = self.spawnMarble('Player1',1.0,Vec3(0,0,2),Vec4(1,0,0,1))
    self.boxNP.node().applyCentralImpulse(Vec3(0,0,15))

    # Objective balls
    for i in range(NUM_MARBLES):
      R = 10
      rs = .25 + 1.75*random.random()
      rp = Vec3(random.randint(-R,R),random.randint(-R,R),random.randint(.5*R,2*R))
      rc = Vec4(random.random(),random.random(),random.random(),1)
      newMarble = self.spawnMarble('Marble'+str(i),rs,rp,rc)
      self.objects.append(newMarble)
    # Bullet nodes should survive a flatten operation!
    #self.worldNP.flattenStrong()
    #render.ls()

game = Game()
run()

