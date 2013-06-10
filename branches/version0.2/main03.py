
# SETUP SOME PATH's
#from sys import path
#path.append('c:\Panda3D-1.7.2')
#path.append('c:\Panda3D-1.7.2\\bin');
#_DATAPATH_ = "./resources"

import sys, os, random

from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
#from direct.actor.Actor import Actor
from panda3d.ai import *

import common
import AI

#PStatClient.connect()
#from pandac.PandaModules import loadPrcFileData
#loadPrcFileData("", "want-directtools #t")
#loadPrcFileData("", "want-tk #t")

NUM_NPC = 5

RESOURCE_PATH = 'resources'
SCENE_MODEL_FILE = 'grounde.egg'

    
class World(ShowBase):
    #pure control states
    mousePos = [0,0]
    mousePos_old = mousePos
    controls = {"turn":0, "walk":0, "strafe":0,"fly":0,\
        'camZoom':0,'camHead':0,'camPitch':0,\
        "mouseDeltaXY":[0,0],"mouseWheel":0,"mouseLook":False,"mouseSteer":False}

    def __init__(self):
        ShowBase.__init__(self)
        base.cTrav = CollisionTraverser('Standard Traverser') # add a base collision traverser
        base.cTrav.showCollisions(self.render)

        self.traverser = CollisionTraverser('CameraPickingTraverse') # set up picker's own traverser for responsiveness
#        self.traverser.showCollisions(self.render)

        self.handlerQ = CollisionHandlerQueue()
        self.handlerPush = CollisionHandlerPusher()
        self.terrainLifter = CollisionHandlerFloor()

        self.setFrameRateMeter(1)
        self.setupKeys()
        self.setAI()
        
        projP = common.Projectile(os.path.join(RESOURCE_PATH,'axes.egg'),'projectile1',r0=Vec3(1,1,1,))
        projP.np.reparentTo(self.render)
        
        taskMgr.add(self.mouseHandler,'Mouse Manager')
        
        print('starting music...')
        self.setupMusic()
        
        print('loading scenery...')
        self.loadScene(os.path.join(RESOURCE_PATH,SCENE_MODEL_FILE))
        
        print('loading player...')
        
        self.player = common.GameObject(name='Player_1',modelName=os.path.join(RESOURCE_PATH,'axes.egg'))
        self.playerController = common.NodePathController(self.controls,self.player.np)
        self.player.np.reparentTo(render)
        
        camera.reparentTo(self.player.np)
        self.ccnp = camera.attachNewNode(CollisionNode('Camera-floor-follower'))
        
        self.ccnp.node().addSolid(CollisionSphere(0,0,0,1))
        self.camController = common.ControlledCamera(self.controls, camera, self.player.np)
        
        # ADD COLLISION NODES
#        self.player.np.setZ(1)
        self.player.cnp = self.player.np.attachNewNode(CollisionNode('Player1--coll-node'))
        self.player.cnp2 = self.player.np.attachNewNode(CollisionNode('Player1--coll-floor'))

        self.player.cnp.node().addSolid(CollisionSphere(0,0,1,.25))
        self.player.cnp2.node().addSolid(CollisionRay(0,0,0,0,0,-1))
        
        print "Adding ",self.player.cnp
        self.player.cnp.show()
        
        self.terrainLifter.addCollider(self.player.cnp2, self.player.np)
        self.terrainLifter.addCollider(self.ccnp, camera)
        
        self.handlerPush.addCollider(self.player.cnp,self.player.np)
        
        base.cTrav.addCollider(self.player.cnp2,self.terrainLifter)
        base.cTrav.addCollider(self.ccnp,self.terrainLifter)
        base.cTrav.addCollider(self.player.cnp,self.handlerPush)
        print(self.player.np.ls())
        
        
        self.textObject = OnscreenText(text = str(self.player.np.getPos()), pos = (-0.9, 0.9), scale = 0.07, fg = (1,1,1,1))
        taskMgr.doMethodLater(1,self.updateOSD,'OSDupdater')
#        taskMgr.doMethodLater(3,self.playAni,'test')
        
        self.stickyTarget = None
        self.focus = None
        
        # setup camera view picker
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerNode.setIntoCollideMask(0) # nothing runs INTO the ray.
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.traverser.addCollider(self.pickerNP, self.handlerQ)
        
        # TESTING SECTION
#        door = common.GameObject('testdoor','resources/door.egg')
#        door.np.reparent(render)
#        door.np.setPos(2,1,0)
        #
    
    def setupMusic(self):
        ms = loader.loadMusic('music/epilogue.ogg')
        ms.setLoop(True)
        ms.setVolume(0.4)
        ms.play()
        ms.status()
       
    def spawnNPC(self,NPCname):
        newAI = AI.Wanderer(NPCname,'resources/aniCube2.egg')
        newAI.np.reparentTo(render)
        tx = random.randint(-1,1)
        ty = random.randint(-1,1)        
        newAI.np.setPos(Vec3(tx,ty,0.01))
        newAI.np.setTag('ID',NPCname)

#            newAI.setCenterPos(Vec3(-1,1,0))
#            tx = random.randint(-10,10)
#            ty = random.randint(-10,10)
#            newAI.setResourcePos( Vec3(tx,ty,0) )

#            newAI.request('ToResource')
        self.npc.append( newAI )
        self.AIworld.addAiChar(newAI.AI)
#            self.seeker.loop("run") # starts actor animations

    def setAI(self):
        #Creating AI World
        self.AIworld = AIWorld(render)
        taskMgr.add(self.updateAI,'updateAI')

        self.npc = []
        for n in range(NUM_NPC):
            self.spawnNPC("NPC"+str(n))

    def updateAI(self,task):
        self.AIworld.update()
        return task.cont
        
    def loadScene(self,sceneName):
        self.scene = loader.loadModel(sceneName)
        
        # TEST ADDING AI OBSTACLES
        self.wall= loader.loadModel("./resources/wall.egg")
        self.wall.reparentTo(render)
        self.wall.setColor(1,0,0,1)
        self.wall.setPosHpr(0,1,0,90,0,0)
        self.AIworld.addObstacle(self.wall)

        self.walls = self.scene.find_all_matches('**/=isaWall')
        print self.walls
        for w in self.walls:
            w.printPos()
#            w.hide()
#            w.show()
#            self.AIworld.addObstacle(w)
        
        self.scene.reparentTo(render)
#        self.setupModels()
        self.setupLights()

    def setupLights(self):
        self.render.setShaderAuto()
        self.alight = AmbientLight('alight')
        self.alight.setColor(VBase4(1,1,1,1)*.3)
        self.alnp = self.render.attachNewNode(self.alight)
        render.setLight(self.alnp)

        self.dlight = DirectionalLight('dlight')
        self.dlight.setColor(VBase4(.8,.8,.8,1))
        self.dlnp = self.render.attachNewNode(self.dlight)
        render.setLight(self.dlnp)

        self.slight = Spotlight('slight')
        self.slight.setColor(VBase4(1,.1,.1,1))
        self.slnp = self.render.attachNewNode(self.slight)
        self.slnp.setPos(0,0,10)
        render.setLight(self.slnp)

    def setupKeys(self):

        _KeyMap ={'action':'mouse1','left':'a','right':'d','strafe_L':'q','strafe_R':'e','wire':'z'}

        self.accept(_KeyMap['left'],self._setControls,["turn",1])
        self.accept(_KeyMap['left']+"-up",self._setControls,["turn",0])
        self.accept(_KeyMap['right'],self._setControls,["turn",-1])
        self.accept(_KeyMap['right']+"-up",self._setControls,["turn",0])


        self.accept(_KeyMap['strafe_L'],self._setControls,["strafe",-1])
        self.accept(_KeyMap['strafe_L']+"-up",self._setControls,["strafe",0])
        self.accept(_KeyMap['strafe_R'],self._setControls,["strafe",1])
        self.accept(_KeyMap['strafe_R']+"-up",self._setControls,["strafe",0])

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
        self.accept("mouse1-up",self._setControls,["mouseLook",False])
        self.accept("mouse2",self._setControls,["mouseLook",True])
        self.accept("mouse2-up",self._setControls,["mouseLook",False])
        self.accept("mouse3",self._setControls,["mouseSteer",True])
        self.accept("mouse3-up",self._setControls,["mouseSteer",False])

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

#TODO: Clean merger with above; same variables, etc
            # RAY PICKING STARTS HERE
            mpos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())

            self.traverser.traverse(render)
            if self.handlerQ.getNumEntries() > 0:
                self.handlerQ.sortEntries()        # This is so we get the closest object.
                picked = self.handlerQ.getEntry(0).getIntoNodePath()
                picked = picked.findNetTag('selectable')
                if not picked.isEmpty():
                    if not picked == self.focus:
                        if self.focus:
                            self.focus.setColorScale(1,1,1,1) # remove highlight from previously picked    
                        self.focus = picked # change 
                        self.focus.setColorScale(1.5,1.5,1.5,1)
                else: # a collisions occured but not with a selectable object so clear focus
                    if self.focus:
                        self.focus.setColorScale(1,1,1,1) # remove highlight from previously picked
                        self.focus = None
                        print "Focus lost\n"
            elif self.focus: # no collisions means lost focus (with collidables) so disable last known focus
                self.focus.setColorScale(1,1,1,1) # remove highlight from previously picked
                self.focus = None
                print "Focus lost\n"
        return task.cont

    def pickingFunc(self):
# and picked.getNetTag('selectable') == '1'
#        if self.focus:
#            ai = [x for x in self.npc if  x.np.getName() in self.focus.getName()]
#            if ai:
#                ai = ai[0]
#                print ai.np.getName()
#                self.npc.remove(ai)
#                ai.terminate()
#                del(ai)
                
        self.stickyTarget = self.focus                  # assign a new sticky target
        if self.stickyTarget:
            print(self.stickyTarget.getName())
#            messenger.send(self.stickyTarget.getName() + 'clickedOn') # tell new sticky target it is clicked on (and do actions accordingly)
            targetName = self.stickyTarget.getName()            
            messenger.send(targetName + 'terminate')
            self.AIworld.removeAiChar(targetName) # REMOVE AI FROM AIWORLD, OTHERWISE WILL CRASH ON NEXT UPDATE
            
    def updateOSD(self,task):
#TODO: change to dotasklater with 1 sec update...no need to hammer this
        [x,y,z] = self.player.np.getPos()
        [hdg,p,r] = self.player.np.getHpr()
        self.textObject.setText(str( (int(x), int(y), int(z), int(hdg)) ))
        return task.cont
    
W = World()
W.run()