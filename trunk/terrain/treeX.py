# -*- coding: utf-8 -*-
"""
Created on Thu Nov 24 19:35:08 2011

@author: shawn
"""

'''
Created on 11.12.2010
Based on Kwasi Mensah's (kmensah@andrew.cmu.edu) "The Fractal Plants Sample Program" from 8/05/2005
@author: Praios

Edited by Craig Macomber

'''
import sys
#sys.path.append('/usr/lib/panda3d')
#sys.path.append('/usr/share/panda3d')

from panda3d.core import NodePath, Geom, GeomNode, GeomVertexArrayFormat, TransformState, GeomVertexWriter, GeomTristrips, GeomVertexRewriter, GeomVertexReader, GeomVertexData, GeomVertexFormat, InternalName
from panda3d.core import Mat4, Vec3, Vec4, CollisionNode, CollisionTube, Point3, Quat
import math, random
from collections import namedtuple
import random

#from panda3d.core import PStatClient
#PStatClient.connect()

_BarkTex_ = "../resources/models/barkTexture.jpg"
_LeafTex_ = '../resources/models/material-12.png'
_Uscale = 1
_Vscale = 1 #repeats
_DoLeaves_ = 0
_Nstep = 12
_polySize = 6

#this is for making the tree not too straight
#def _randomBend(inQuat, maxAngle=20):
#    q=Quat()
#    angle=random.random()*2*math.pi
#   
#    #power of 2 here makes distrobution even withint a circle
#    # (makes larger bends are more likley as they are further spread)
#    ammount=(random.random()**2)*maxAngle
#    q.setHpr((math.sin(angle)*ammount,math.cos(angle)*ammount,0))
#    return inQuat*q

def _randomBend(inQuat, maxAngle=20):
    q=Quat()
    theta = random.randint(-maxAngle,maxAngle)
    phi = random.randint(-maxAngle,maxAngle)
   
    #power of 2 here makes distrobution even withint a circle
    # (makes larger bends are more likley as they are further spread)
#    ammount=(random.random()**2)*maxAngle
    q.setHpr((0,theta,phi))
    return inQuat*q


# TODO : This needs to get updated to work with quat. Using tmp hack.
def _angleRandomAxis(quat, angle):
#     fwd = quat.getUp()
#     perp1 = quat.getRight()   
#     perp2 = quat.getForward() 
#     nangle = angle + math.pi * (0.125 * random.random() - 0.0625)
#     nfwd = fwd * (0.5 + 2 * random.random()) + perp1 * math.sin(nangle) + perp2 * math.cos(nangle)
#     nfwd.normalize()
#     nperp2 = nfwd.cross(perp1)
#     nperp2.normalize()
#     nperp1 = nfwd.cross(nperp2)
#     nperp1.normalize()
    return _randomBend(quat,angle)


#class BranchNode():
#    def __init__(self,l=1,rad=1,Q=Quat(),pos=Vec3(0,0,0)):
#        self.radius = rad            # radius of child end (parent end will obvious have it's radius)
#        self.quat = Q         # orientation quaternion; which way am I pointing?
#        self.pos = pos     # center point of this branch node
#        self.gen = 0               # generation ID
#
#        self.length = l            # MOVE TO GENERATION ROUTINE. DON'T NEED LENGTHS, ONLY POSITIONS; redundant with child positions
#        self.children = []         # list of children from THIS branch's end

BranchNode = namedtuple('BranchNode','pos quat radius gen')

class FractalTree(NodePath):
    __format = None
    def __init__(self, barkTexture, leafModel, lengthList, numCopiesList, radiusList):
        NodePath.__init__(self, "Tree Holder")
        self.numPrimitives = 0
        self.leafModel = leafModel
        self.barkTexture = barkTexture
        self.bodies = NodePath("Bodies")
        self.leaves = NodePath("Leaves")
        self.coll = self.attachNewNode(CollisionNode("Collision"))   
        self.bodydata = GeomVertexData("body vertices", self.__format, Geom.UHStatic)
        self.numCopiesList = list(numCopiesList)   
        self.radiusList = list(radiusList) 
        self.lengthList = list(lengthList) 
        self.iterations = 1
        
#        self.makeEnds()
#        self.makeFromStack(True)
        self.coll.show()       
        self.bodies.setTexture(barkTexture)
        self.coll.reparentTo(self)
        self.bodies.reparentTo(self)
        self.leaves.reparentTo(self)
       
    #this makes a flattened version of the tree for faster rendering...
    def getStatic(self):
        np = NodePath(self.node().copySubgraph())
        np.flattenStrong()
        return np       
   
    #this should make only one instance
    @classmethod
    def makeFMT(cls):
        if cls.__format is not None:
            return
        formatArray = GeomVertexArrayFormat()
        formatArray.addColumn(InternalName.make("drawFlag"), 1, Geom.NTUint8, Geom.COther)   
        format = GeomVertexFormat(GeomVertexFormat.getV3n3t2())
        format.addArray(formatArray)
        cls.__format = GeomVertexFormat.registerFormat(format)
   
    def makeEnds(self, pos=Vec3(0, 0, 0), quat=None):
        if quat is None: quat=Quat()
        self.ends = [(pos, quat, 0)]
       
    def makeFromStack(self, makeColl=False):
        stack = self.ends
        to = self.iterations
        lengthList = self.lengthList
        numCopiesList = self.numCopiesList
        radiusList = self.radiusList
        ends = []
        while stack:
            pos, quat, depth = stack.pop()
            print depth
            length = lengthList[depth]
            if depth != to and depth + 1 < len(lengthList):
                self.drawBody(pos, quat, radiusList[depth])     
                #move foward along the right axis
                newPos = pos + quat.getUp() * length
                if makeColl:
                    self.makeColl(pos, newPos, radiusList[depth])
                numCopies = numCopiesList[depth] 
                if numCopies:       
                    for i in xrange(numCopies):
#                        stack.append((newPos, _angleRandomAxis(quat, 2 * math.pi * i / numCopies), depth + 1))
                        stack.append((newPos, _randomBend(quat, self.maxAngle), depth + 1))
                        # 
                        #stack.append((newPos, _randomAxis(vecList,3), depth + 1))
                else:
                    #just make another branch connected to this one with a small variation in direction
                    stack.append((newPos, _randomBend(quat, self.maxBend), depth + 1))
            else:
                self.drawBody(pos, quat, radiusList[depth], False)
                if _DoLeaves_: self.drawLeaf(pos, quat)
                ends.append((pos, quat, depth))
        self.ends = ends
        
       
    def makeColl(self, pos, newPos, radius):
        tube = CollisionTube(Point3(pos), Point3(newPos), radius)
        self.coll.node().addSolid(tube)
         
    #this draws the body of the tree. This draws a ring of vertices and connects the rings with
    #triangles to form the body.
    #this keepDrawing paramter tells the function wheter or not we're at an end
    #if the vertices before you were an end, dont draw branches to it
    def drawBody(self, pos, quat, radius=1, keepDrawing=True, numVertices=_polySize):
        vdata = self.bodydata
        circleGeom = Geom(vdata)
        vertWriter = GeomVertexWriter(vdata, "vertex")
        #colorWriter = GeomVertexWriter(vdata, "color")
        normalWriter = GeomVertexWriter(vdata, "normal")
        drawReWriter = GeomVertexRewriter(vdata, "drawFlag")
        texReWriter = GeomVertexRewriter(vdata, "texcoord")

        startRow = vdata.getNumRows()
        vertWriter.setRow(startRow)
        #colorWriter.setRow(startRow)
        normalWriter.setRow(startRow)       

        sCoord = 0   
        if (startRow != 0):
            texReWriter.setRow(startRow - numVertices) #go back numVert in the vert list
            sCoord = texReWriter.getData2f().getX() + _Vscale           # UV SCALE HERE!
            drawReWriter.setRow(startRow - numVertices)
            if(drawReWriter.getData1f() == False):
                sCoord -= _Vscale                                # UV SCALE HERE!
        drawReWriter.setRow(startRow)
        texReWriter.setRow(startRow)   
       
        angleSlice = 2 * math.pi / numVertices
        currAngle = 0
        #axisAdj=Mat4.rotateMat(45, axis)*Mat4.scaleMat(radius)*Mat4.translateMat(pos)
        perp1 = quat.getRight()
        perp2 = quat.getForward()   
        
        #vertex information is written here
        for i in xrange(numVertices+1): #doubles the last vertex to fix UV seam
            adjCircle = pos + (perp1 * math.cos(currAngle) + perp2 * math.sin(currAngle)) * radius
            normal = perp1 * math.cos(currAngle) + perp2 * math.sin(currAngle)       
            normalWriter.addData3f(normal)
            vertWriter.addData3f(adjCircle)
            texReWriter.addData2f(_Uscale*i / numVertices,sCoord)            # UV SCALE HERE!
            #colorWriter.addData4f(0.5, 0.5, 0.5, 1)
            drawReWriter.addData1f(keepDrawing)
            currAngle += angleSlice 
        drawReader = GeomVertexReader(vdata, "drawFlag")
        drawReader.setRow(startRow - numVertices)   
        
        #we cant draw quads directly so we use Tristrips
        if (startRow != 0) and (drawReader.getData1f() != False):
            lines = GeomTristrips(Geom.UHStatic)         
            for i in xrange(numVertices+1):
                lines.addVertex(i + startRow)
                lines.addVertex(i + startRow - numVertices-1)
            lines.addVertex(startRow)
            lines.addVertex(startRow - numVertices)
            lines.closePrimitive()
            #lines.decompose()
            circleGeom.addPrimitive(lines)           
            circleGeomNode = GeomNode("Debug")
            circleGeomNode.addGeom(circleGeom)   
            self.numPrimitives += numVertices * 2
            self.bodies.attachNewNode(circleGeomNode)
   
    #this draws leafs when we reach an end       
    def drawLeaf(self, pos=Vec3(0, 0, 0), quat=None, scale=0.125):
        #use the vectors that describe the direction the branch grows to make the right
        #rotation matrix
        newCs = Mat4()#0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
#         newCs.setRow(0, vecList[2]) #right
#         newCs.setRow(1, vecList[1]) #up
#         newCs.setRow(2, vecList[0]) #forward
#         newCs.setRow(3, Vec3(0, 0, 0))
#         newCs.setCol(3, Vec4(0, 0, 0, 1))   
        quat.extractToMatrix(newCs)
        axisAdj = Mat4.scaleMat(scale) * newCs * Mat4.translateMat(pos)       
        leafModel = NodePath("leaf")
        self.leafModel.instanceTo(leafModel)
        leafModel.reparentTo(self.leaves)
        leafModel.setTransform(TransformState.makeMat(axisAdj))

       
    def grow(self, num=1, removeLeaves=0, leavesScale=0, trunkRate = 0):
        self.iterations += num
        while num > 0:
            self.setScale(self, 1+trunkRate/100)
            self.leafModel.setScale(self.leafModel, (1+leavesScale/100) / (1+trunkRate/100) )
            if removeLeaves:
                for i,c in enumerate(self.leaves.getChildren()):
#                    print self.numCopiesList[i]
                    c.removeNode()
            self.makeFromStack()
            self.bodies.setTexture(self.barkTexture)         
            num -= 1

FractalTree.makeFMT()

class sTree(FractalTree):
    def __init__(self, numIterations=1,branchEvery=20,numBranches=2,maxAngle=None,maxBend=None,lenScale=None,radScale=None):       
        if maxAngle: self.maxAngle = maxAngle
        if maxBend: self.maxBend = maxBend
        barkTexture = base.loader.loadTexture(_BarkTex_)
        leafModel = base.loader.loadModel('../resources/models/shrubbery')
        leafModel.clearModelNodes()
        leafModel.flattenStrong()
        leafTexture = base.loader.loadTexture(_LeafTex_)
        leafModel.setTexture(leafTexture, 1) 
        leafModel.setScale(0.1)
        leafModel.setTransparency(1)
        
        lengthList = self.makeLengthList(1, numIterations,lenScale or None)
        numCopiesList = self.makeNumCopiesList(numBranches, branchEvery, numIterations)
        radiusList = self.makeRadiusList(0.25, numIterations, numCopiesList,radScale)
        
        FractalTree.__init__(self, barkTexture, leafModel, lengthList, numCopiesList, radiusList)
       
    def branchFromNodes(self,nodeList):
#        endNode = nodeList.pop() # need to set keepDraw False on last node
        for node in nodeList:
            self.drawBody(node.pos, node.quat, node.radius)
#        self.drawBody(endNode.pos,endNode.quat,endNode.radius,False) # tell drawBody this is the end of the branch

        

    @staticmethod
    def makeRadiusList(radius, iterations, numCopiesList, scale=1.5):
        l = [radius]
        for i in xrange(1, iterations):
            #if i % 3 == 0:
            if i != 1 and numCopiesList[i - 2]:
                radius /= numCopiesList[i - 2] ** 0.5
            else:
                radius /= scale ** (1.0 / 3)
            l.append(radius)
        return l
   
    @staticmethod
    def makeLengthList(length, iterations, sz=1.0):
        l = [length]
        for i in xrange(1, iterations):
            #if i % 3 == 0:
                #decrease dimensions when we branch
                #length = Vec3(length.getX() / 2, length.getY() / 2, length.getZ() / 1.1)
            length = length / sz ** (1.0 / 3)
            l.append(length)
        return l
   
    @staticmethod
    def makeNumCopiesList(numCopies, branchAt, iterations):
        nBranch = int( iterations / branchAt )
        l = [0]*iterations
        for b in xrange(nBranch):
            l[b] = numCopies
#            
#        l = list()
#        for i in xrange(iterations):
#            if i % int(branchAt) == 0:
##            if random.random() <= branchAt:    # go with a probability of a branching occuring 
##                l.append(random.randint(2,numCopies))
#                l.append(numCopies)
#            else:
#                l.append(0)
        return l


if __name__ == "__main__":
#    random.seed(11*math.pi)
    from direct.showbase.ShowBase import ShowBase
    base = ShowBase()
    base.cam.setPos(0, -10, 2)
#    base.cam.lookAt(base.render)
    base.setFrameRateMeter(1)
    tree = sTree(numIterations=64,branchEvery=600,numBranches=2,maxAngle=40, maxBend=5, lenScale = 2,radScale=3)
    tree.reparentTo(base.render)
    #make an optimized snapshot of the current tree
#    np = t.getStatic()
#    np.setPos(2, -10, 0)
#    np.reparentTo(base.render)

    numGens = 8
    thisBranch = [BranchNode._make([Vec3(0,0,0),Quat(),.1,0])] # initial node      # make a starting node flat at 0,0,0
    for b in range(3):

        L=1.0
        for i in range(1,numGens+1):
#            print [x.quat for x in thisBranch] # DEBUG        
            curQ = thisBranch[i-1].quat
            curP = thisBranch[i-1].pos
            
            quat = Quat()
            quat.setHpr(Vec3(0,random.randint(-10,10),random.randint(-10,10)))
            quat *= curQ
            pos = curP + quat.getUp() * L 
            radius = .8*thisBranch[i-1].radius
            L *= 0.7
            newNode = BranchNode._make([pos,quat,radius,0])
            thisBranch.append(newNode)        
    
        tree.branchFromNodes(thisBranch[0:])
        thisBranch = [thisBranch[1]] # test just walk up 1 node and start over
        numGens -= 1

#
#
#    #demonstrate growing
#    last = [0] # a bit hacky
#    dt = .01
#    def grow(task):
#        if task.time > last[0] + dt:
#            t.grow(removeLeaves=1,leavesScale=1.0,trunkRate = 0)
#            last[0] = task.time
#            #t.leaves.detachNode()
#        if last[0] > _Nstep*dt:
#            print('grow done')
#            t.setScale(1)
#            t.flattenStrong()
#            t.write_bam_file('sampleTree.bam')
#            return task.done
#        return task.cont
#    base.taskMgr.add(grow, "growTask")

#    t.grow(_Nstep,removeLeaves=1,leavesScale=1.0,trunkRate = 1.0)
    base.toggleWireframe()
    base.accept('escape',sys.exit)
    base.accept('z',base.toggleWireframe)
    base.run()