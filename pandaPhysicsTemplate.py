
#from pandac.PandaModules import loadPrcFileData
#loadPrcFileData('', 'load-display tinydisplay')

#loadPrcFileData('', 'bullet-additional-damping true')
#loadPrcFileData('', 'bullet-additional-damping-linear-factor 0.005')
#loadPrcFileData('', 'bullet-additional-damping-angular-factor 0.01')
#loadPrcFileData('', 'bullet-additional-damping-linear-threshold 0.01')
#loadPrcFileData('', 'bullet-additional-damping-angular-threshold 0.01')

import sys
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

class Game(DirectObject):

  def __init__(self):
    base.setBackgroundColor(0.1, 0.1, 0.8, 1)
    base.setFrameRateMeter(True)


        
    # Light
    alight = AmbientLight('ambientLight')
    alight.setColor(Vec4(0.5, 0.5, 0.5, 1))
    alightNP = render.attachNewNode(alight)

    dlight = DirectionalLight('directionalLight')
    dlight.setDirection(Vec3(1, 1, -1))
    dlight.setColor(Vec4(0.7, 0.7, 0.7, 1))
    dlightNP = render.attachNewNode(dlight)

    render.clearLight()
#    render.setLight(alightNP)
    render.setLight(dlightNP)

    # Input
    self.accept('escape', self.doExit)
    self.accept('r', self.doReset)
    self.accept('z', self.toggleWireframe)
    self.accept('f2', self.toggleTexture)
    self.accept('f3', self.toggleDebug)
    self.accept('f5', self.doScreenshot)

    inputState.watchWithModifiers('forward', 'w')
    inputState.watchWithModifiers('left', 'a')
    inputState.watchWithModifiers('reverse', 's')
    inputState.watchWithModifiers('right', 'd')
    inputState.watchWithModifiers('turnLeft', 'q')
    inputState.watchWithModifiers('turnRight', 'e')
    inputState.watchWithModifiers('jump', 'space')

    # Task
    taskMgr.add(self.update, 'updateWorld')

    # Physics
    self.setup()
    
  # _____HANDLER_____

  def doExit(self):
    self.cleanup()
    sys.exit(1)

  def doReset(self):
    self.cleanup()
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

  # ____TASK___

  def processInput(self, dt):
    force = Vec3(0, 0, 0)
    torque = Vec3(0, 0, 0)

    if inputState.isSet('forward'): force.setY( 1.0)
    if inputState.isSet('reverse'): force.setY(-1.0)
    if inputState.isSet('left'):    force.setX(-1.0)
    if inputState.isSet('right'):   force.setX( 1.0)
#    if inputState.isSet('forward'): torque.setX(-1.0)
#    if inputState.isSet('reverse'): torque.setX(1.0)

    if inputState.isSet('jump') and not self.isJumping:
        self.isJumping = True
        base.taskMgr.add(self.doJump,'JumpTask')
        
    if inputState.isSet('turnLeft'):  torque.setZ( 1.0)
    if inputState.isSet('turnRight'): torque.setZ(-1.0)

    force *= 10.0
    torque *= 5.0

#    force = render.getRelativeVector(self.boxNP, force)
#    torque = render.getRelativeVector(self.boxNP, torque)

    self.boxNP.node().setActive(True)
    self.boxNP.node().applyCentralForce(force)
    self.boxNP.node().applyTorque(torque)

  def doJump(self,task):
      if task.time < 0.500:      
          self.boxNP.node().applyCentralForce(Vec3(0,0,20))
      else:
          result = self.world.contactTestPair(self.boxNP.node(),self.groundNP.node())
          if result.getNumContacts() > 0:
              self.isJumping = False # reset on contact with ground
              return task.done
      return task.cont

  def update(self, task):
    dt = globalClock.getDt()
#    print self.isJumping

    self.processInput(dt)
    #self.world.doPhysics(dt)
    self.world.doPhysics(dt, 5, 1.0/180.0)
    
    # adjust Camera
    base.cam.setX(self.boxNP,0)
    base.cam.setY(self.boxNP,-20)
    base.cam.setZ(5)
    base.cam.setHpr(self.boxNP.getH(render),0,0)
    base.cam.lookAt(self.boxNP)  
    
    return task.cont

  def cleanup(self):
    self.world.removeRigidBody(self.groundNP.node())
    self.world.removeRigidBody(self.boxNP.node())
    self.world = None

    self.debugNP = None
    self.groundNP = None
    self.boxNP = None

    self.worldNP.removeNode()

  def setup(self):
    self.worldNP = render.attachNewNode('World')
    self.isJumping = False

    # World
    self.debugNP = self.worldNP.attachNewNode(BulletDebugNode('Debug'))
    self.debugNP.show()
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
    terrain = loader.loadModel('resources/groundf.egg')
    print terrain.ls()
    geomNodes = terrain.findAllMatches('**/+GeomNode')
    for geom in geomNodes:
        if(geom.node().getTag('isVisible')):
            geom.reparentTo(render)
            
        mesh = BulletTriangleMesh()
        mesh.addGeom(geom.node().getGeom(0))   
        shape = BulletTriangleMeshShape(mesh,dynamic='false')
    
        self.groundNP = self.worldNP.attachNewNode(BulletRigidBodyNode(geom.node().getName()))
        self.groundNP.node().addShape(shape)
    #    self.groundNP.setPos(0, 0, -2)
        self.groundNP.setCollideMask(BitMask32.allOn())
    
        self.world.attachRigidBody(self.groundNP.node())

    # Box (dynamic)
#    shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
    shape = BulletSphereShape(0.5)
#    shape = BulletCylinderShape(0.5,1,0)
    
    
    self.boxNP = self.worldNP.attachNewNode(BulletRigidBodyNode('Box'))
    self.boxNP.node().setMass(1.0)
    self.boxNP.node().addShape(shape)
    self.boxNP.setPos(0, 0, 2)
    #self.boxNP.setScale(2, 1, 0.5)
    self.boxNP.setCollideMask(BitMask32.allOn())
    #self.boxNP.node().setDeactivationEnabled(False)
    self.boxNP.node().setInertia(Vec3(.1,1e6,.1))
    self.world.attachRigidBody(self.boxNP.node())

    visualNP = loader.loadModel('models/ball.egg')
    visualNP.clearModelNodes()
    visualNP.reparentTo(self.boxNP)
    visualNP.setColor(1,0,0)

    # Bullet nodes should survive a flatten operation!
    #self.worldNP.flattenStrong()
    #render.ls()

game = Game()
run()

