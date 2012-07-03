
# SETUP SOME PATH's
#from sys import path
#path.append('c:\Panda3D-1.7.2')
#path.append('c:\Panda3D-1.7.2\\bin');
#_DATAPATH_ = "./resources"

import sys, os, random

from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from panda3d.ai import *

import common

PStatClient.connect()

NUM_NPC = 10

RESOURCE_PATH = 'resources'

#class Scene(common.GameObject):
#    """ Used to load static geometry"""
#
#    def __init__(self,sceneName):
#        if not sceneName:
#            print "No Scene name given on init!!!"
#            return -1
#        common.GameObject.__init__(self)
#        self.np = self.loadScene(sceneName)
##        self.cnp = self.np.attachNewNode(CollisionNode('plr-coll-node'))
#
#    def loadScene(self,sceneName):
#        tmp = loader.loadModel(os.path.join(RESOURCE_PATH,sceneName))
#        if tmp:
#            # do things with tmp like split up, add lights, whatever
#            return tmp
#        else:
#            return None
#        # load scene tree from blender
#        # find lights from blender and create them with the right properties

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
        self.setFrameRateMeter(1)
        self.loadScene(os.path.join(RESOURCE_PATH,'groundc.x'))
        self.CC = common.ControlledCamera(self.controls)

        self.setupKeys()
        self.setAI()
        taskMgr.add(self.mouseHandler,'Mouse Manager')

        self.player = common.ControlledObject(name='Player_1',modelName=os.path.join(RESOURCE_PATH,'axes.x'),controller=None)
         # Attach the player node to the camera empty node
        self.player.np.reparentTo(self.CC._target)
        self.player.np.setZ(.2)

        self.textObject = OnscreenText(text = str(self.CC.np.getPos()), pos = (-0.9, 0.9), scale = 0.07, fg = (1,1,1,1))
        taskMgr.add(self.updateOSD,'OSDupdater')

        self.stickyTarget = None
        self.hover = None
        self.traverser = CollisionTraverser('CameraPickingTraverse')
        self.pq = CollisionHandlerQueue()

        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.traverser.addCollider(self.pickerNP, self.pq)
        
#        self.targetCard = loader.loadModel('resources/targeted.egg')
#        self.targetCard.set_billboard_point_eye()
#        self.targetCard.setDepthTest(False)
#        self.targetCard.setDepthWrite(False)
#        self.targetCard.reparentTo(self.hidden)
#        self.targetCard.set_light_off()
        
    def setAI(self):
        #Creating AI World
        self.AIworld = AIWorld(render)
        taskMgr.add(self.updateAI,'updateAI')

        self.npc = []
        for n in range(NUM_NPC):

            newAI = common.Gatherer("NPC"+str(n),'resources/aniCube')
            newAI.np.reparentTo(render)
            newAI.np.setPos(0,0,0)
            newAI.np.setTag('ID',str(n))

            newAI.setCenterPos(Vec3(-1,1,0))
            tx = random.randint(-50,50)
            ty = random.randint(-50,50)
            newAI.setResourcePos( Vec3(tx,ty,0) )

            newAI.request('ToResource')
            self.npc.append( newAI )
            self.AIworld.addAiChar(newAI.AI)
#            self.seeker.loop("run") # starts actor animations

    def updateAI(self,task):
        self.AIworld.update()
        return task.cont
        
    def loadScene(self,sceneName):
        self.scene = common.GameObject('ground',sceneName)
        self.scene.np.setTag('selectable','0')
        self.scene.np.reparentTo(render)
#        self.setupModels()
        self.setupLights()

    def setupLights(self):
        self.render.setShaderAuto()
        self.alight = AmbientLight('alight')
        self.alight.setColor(VBase4(1,1,1,1))
        self.alnp = self.render.attachNewNode(self.alight)
        render.setLight(self.alnp)

        self.dlight = DirectionalLight('dlight')
        self.dlight.setColor(VBase4(.8,.8,.8,1))
        self.dlnp = self.render.attachNewNode(self.dlight)
        render.setLight(self.dlnp)

        self.slight = Spotlight('slight')
        self.slight.setColor(VBase4(1,1,1,1))
        self.slnp = self.render.attachNewNode(self.slight)
        self.slnp.setPos(0,0,10)
        render.setLight(self.slnp)

    def setupKeys(self):

        _KeyMap ={'action':'mouse1','left':'q','right':'e','strafe_L':'a','strafe_R':'d','wire':'z'}

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
            mpos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())

            self.traverser.traverse(render)
            messenger.send('highlight',[None])
            if self.pq.getNumEntries() > 0:
                self.pq.sortEntries()        # This is so we get the closest object.
                picked = self.pq.getEntry(0).getIntoNodePath()
                picked = picked.findNetTag('selectable')
                self.hover = None
                if not picked.isEmpty() and picked.getNetTag('selectable') == '1':
                    messenger.send('highlight',[picked.getName()])
                    self.hover = picked                   

        return task.cont

    def pickingFunc(self):
#        messenger.send('deselect',[self.stickyTarget]) # toggle the old sticky target off     
        self.stickyTarget = self.hover                  # assign a new sticky target
        if self.stickyTarget:
            messenger.send('clickedOn',[self.stickyTarget.getName()]) # tell new sticky target it is clicked on (and do actions accordingly)
        
    def updateOSD(self,task):
#TODO: change to dotasklater with 1 sec update...no need to hammer this
        [x,y,z] = self.player.np.getParent().getPos()
        [hdg,p,r] = self.player.np.getParent().getHpr()
        self.textObject.setText(str( (int(x), int(y), int(z), int(hdg)) ))
        return task.cont

W = World()
W.run()