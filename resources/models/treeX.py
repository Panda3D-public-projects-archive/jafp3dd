# -*- coding: utf-8 -*-
'''
Created on 11.12.2010
Based on Kwasi Mensah's (kmensah@andrew.cmu.edu) "The Fractal Plants Sample Program" from 8/05/2005
@author: Praios

Edited by Craig Macomber

Created on Thu Nov 24 19:35:08 2011
based on the above authors and editors
@author: Shawn Updegraff
'''

import sys

from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, Geom, GeomNode, GeomVertexArrayFormat, TransformState, GeomVertexWriter, GeomTristrips, GeomVertexRewriter, GeomVertexReader, GeomVertexData, GeomVertexFormat, InternalName
from panda3d.core import Mat4, Vec4, Vec3, CollisionNode, CollisionTube, Point3, Quat
from math import sin,cos,pi, sqrt
import random
from collections import namedtuple

#from panda3d.core import PStatClient
#PStatClient.connect()

_polySize = 8

#def _randomBend(inQuat, maxAngle=20):
#    q=Quat()
#    theta = random.randint(-maxAngle,maxAngle)
#    phi = random.randint(-maxAngle,maxAngle)
#   
#    #power of 2 here makes distrobution even withint a circle
#    # (makes larger bends are more likley as they are further spread)
##    ammount=(random.random()**2)*maxAngle
#    q.setHpr((0,theta,phi))
#    return inQuat*q
#
#
## TODO : This needs to get updated to work with quat. Using tmp hack.
#def _angleRandomAxis(quat, angle):
##     fwd = quat.getUp()
##     perp1 = quat.getRight()   
##     perp2 = quat.getForward() 
##     nangle = angle + math.pi * (0.125 * random.random() - 0.0625)
##     nfwd = fwd * (0.5 + 2 * random.random()) + perp1 * math.sin(nangle) + perp2 * math.cos(nangle)
##     nfwd.normalize()
##     nperp2 = nfwd.cross(perp1)
##     nperp2.normalize()
##     nperp1 = nfwd.cross(nperp2)
##     nperp1.normalize()
#    return _randomBend(quat,angle)
#
#
#
#
#class Fractaltrunk(NodePath):
#    __format = None
#    def __init__(self, barkTexture, leafModel, lengthList, numCopiesList, radiusList):
#        NodePath.__init__(self, "Tree Holder")
#        self.numPrimitives = 0
#        self.leafModel = leafModel
#        self.barkTexture = barkTexture
#        self.bodies = NodePath("Bodies")
#        self.leaves = NodePath("Leaves")
#        self.coll = self.attachNewNode(CollisionNode("Collision"))   
#        self.bodydata = GeomVertexData("body vertices", self.__format, Geom.UHStatic)
#        self.numCopiesList = list(numCopiesList)   
#        self.radiusList = list(radiusList) 
#        self.lengthList = list(lengthList) 
#        self.iterations = 1
#        
##        self.makeEnds()
##        self.makeFromStack(True)
#        self.coll.show()       
#        self.bodies.setTexture(barkTexture)
#        self.coll.reparentTo(self)
#        self.bodies.reparentTo(self)
#        self.leaves.reparentTo(self)
#       
#    #this makes a flattened version of the tree for faster rendering...
#    def getStatic(self):
#        np = NodePath(self.node().copySubgraph())
#        np.flattenStrong()
#        return np       
#   
#    #this should make only one instance
#    @classmethod
#    def makeFMT(cls):
#        if cls.__format is not None:
#            return
#        formatArray = GeomVertexArrayFormat()
#        formatArray.addColumn(InternalName.make("drawFlag"), 1, Geom.NTUint8, Geom.COther)   
#        format = GeomVertexFormat(GeomVertexFormat.getV3n3t2())
#        format.addArray(formatArray)
#        cls.__format = GeomVertexFormat.registerFormat(format)
#   
#    def makeEnds(self, pos=Vec3(0, 0, 0), quat=None):
#        if quat is None: quat=Quat()
#        self.ends = [(pos, quat, 0)]
#       
#    def makeFromStack(self, makeColl=False):
#        stack = self.ends
#        to = self.iterations
#        lengthList = self.lengthList
#        numCopiesList = self.numCopiesList
#        radiusList = self.radiusList
#        ends = []
#        while stack:
#            pos, quat, depth = stack.pop()
#            print depth
#            length = lengthList[depth]
#            if depth != to and depth + 1 < len(lengthList):
#                self.drawBody(pos, quat, radiusList[depth])     
#                #move foward along the right axis
#                newPos = pos + quat.getUp() * length
#                if makeColl:
#                    self.makeColl(pos, newPos, radiusList[depth])
#                numCopies = numCopiesList[depth] 
#                if numCopies:       
#                    for i in xrange(numCopies):
##                        stack.append((newPos, _angleRandomAxis(quat, 2 * math.pi * i / numCopies), depth + 1))
#                        stack.append((newPos, _randomBend(quat, self.maxAngle), depth + 1))
#                        # 
#                        #stack.append((newPos, _randomAxis(vecList,3), depth + 1))
#                else:
#                    #just make another branch connected to this one with a small variation in direction
#                    stack.append((newPos, _randomBend(quat, self.maxBend), depth + 1))
#            else:
#                self.drawBody(pos, quat, radiusList[depth], False)
#                if _DoLeaves_: self.drawLeaf(pos, quat)
#                ends.append((pos, quat, depth))
#        self.ends = ends
#        
#       
#    def makeColl(self, pos, newPos, radius):
#        tube = CollisionTube(Point3(pos), Point3(newPos), radius)
#        self.coll.node().addSolid(tube)
#         
#    #this draws the body of the tree. This draws a ring of vertices and connects the rings with
#    #triangles to form the body.
#    #this keepDrawing paramter tells the function wheter or not we're at an end
#    #if the vertices before you were an end, dont draw branches to it
#    def drawBody(self, pos, quat, radius=1,UVcoord=(1,1), keepDrawing=True, numVertices=_polySize):
#        vdata = self.bodydata
#        circleGeom = Geom(vdata)
#        vertWriter = GeomVertexWriter(vdata, "vertex")
#        #colorWriter = GeomVertexWriter(vdata, "color")
#        normalWriter = GeomVertexWriter(vdata, "normal")
##        drawReWriter = GeomVertexRewriter(vdata, "drawFlag")
#        texReWriter = GeomVertexRewriter(vdata, "texcoord")
#
#        startRow = vdata.getNumRows()
#        vertWriter.setRow(startRow)
#        #colorWriter.setRow(startRow)
#        normalWriter.setRow(startRow)       
#
##        sCoord = 0   
##        if (startRow != 0):
##            texReWriter.setRow(startRow - numVertices) #go back numVert in the vert list
##            sCoord = texReWriter.getData2f().getX() + _Vscale           # UV SCALE HERE!
##            print sCoord
##            drawReWriter.setRow(startRow - numVertices)
##            if(drawReWriter.getData1f() == False):
##                sCoord -= _Vscale                                # UV SCALE HERE!
##        drawReWriter.setRow(startRow)
#        texReWriter.setRow(startRow)   
#       
#        angleSlice = 2 * pi / numVertices
#        currAngle = 0
#        #axisAdj=Mat4.rotateMat(45, axis)*Mat4.scaleMat(radius)*Mat4.translateMat(pos)
#        perp1 = quat.getRight()
#        perp2 = quat.getForward()   
#        #vertex information is written here
#        for i in xrange(numVertices): 
#            adjCircle = pos + (perp1 * cos(currAngle) + perp2 * sin(currAngle)) * radius
#            normal = perp1 * cos(currAngle) + perp2 * sin(currAngle)       
#            normalWriter.addData3f(normal)
#            vertWriter.addData3f(adjCircle)
#            texReWriter.addData2f(float(UVcoord[0]*i) / numVertices,UVcoord[1])            # UV SCALE HERE!
#            print UVcoord
#            #colorWriter.addData4f(0.5, 0.5, 0.5, 1)
##            drawReWriter.addData1f(keepDrawing)
#            currAngle += angleSlice 
#        drawReader = GeomVertexReader(vdata, "drawFlag")
#        drawReader.setRow(startRow - numVertices)   
#        
#        #we cant draw quads directly so we use Tristrips
#        if (startRow != 0) and (keepDrawing == False):
#            lines = GeomTristrips(Geom.UHStatic)         
#            for i in xrange(numVertices):
#                lines.addVertex(i + startRow)
#                lines.addVertex(i + startRow - numVertices)
#            lines.addVertex(startRow)
#            lines.addVertex(startRow - numVertices)
#            lines.closePrimitive()
#            #lines.decompose()
#            circleGeom.addPrimitive(lines)           
#            circleGeomNode = GeomNode("Debug")
#            circleGeomNode.addGeom(circleGeom)   
#            self.numPrimitives += numVertices * 2
#            self.bodies.attachNewNode(circleGeomNode)
#   
#    #this draws leafs when we reach an end       
#    def drawLeaf(self, pos=Vec3(0, 0, 0), quat=None, scale=0.125):
#        #use the vectors that describe the direction the branch grows to make the right
#        #rotation matrix
#        #0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
##         newCs.setRow(0, vecList[2]) #right
##         newCs.setRow(1, vecList[1]) #up
##         newCs.setRow(2, vecList[0]) #forward
##         newCs.setRow(3, Vec3(0, 0, 0))
##         newCs.setCol(3, Vec4(0, 0, 0, 1))   
#        newCs = Mat4()
#        quat.extractToMatrix(newCs)
#        axisAdj = Mat4.scaleMat(scale) * newCs * Mat4.translateMat(pos)       
#        leafModel = NodePath("leaf")
#        self.leafModel.instanceTo(leafModel)
#        leafModel.reparentTo(self.leaves)
#        leafModel.setTransform(TransformState.makeMat(axisAdj))
#
#       
#    def grow(self, num=1, removeLeaves=0, leavesScale=0, trunkRate = 0):
#        self.iterations += num
#        while num > 0:
#            self.setScale(self, 1+trunkRate/100)
#            self.leafModel.setScale(self.leafModel, (1+leavesScale/100) / (1+trunkRate/100) )
#            if removeLeaves:
#                for i,c in enumerate(self.leaves.getChildren()):
##                    print self.numCopiesList[i]
#                    c.removeNode()
#            self.makeFromStack()
#            self.bodies.setTexture(self.barkTexture)         
#            num -= 1
#FractalTree.makeFMT()


class Branch(NodePath):
    def __init__(self, nodeName):
        NodePath.__init__(self, nodeName)
        self.numPrimitives = 0
        self.bodydata = GeomVertexData("body vertices", GeomVertexFormat.getV3n3t2(), Geom.UHStatic)        
        self.bodies = NodePath("Bodies")
        self.coll = self.attachNewNode(CollisionNode("Collision"))       
        self.coll.show()       
        self.coll.reparentTo(self)
        self.bodies.reparentTo(self)

    #this draws the body of the tree. This draws a ring of vertices and connects the rings with
    #triangles to form the body.
    #this keepDrawing paramter tells the function wheter or not we're at an end
    #if the vertices before you were an end, dont draw branches to it
    def drawBody(self, pos, quat, radius=1,UVcoord=(1,1), numVertices=_polySize):
#        if isRoot:
#            self.bodydata = GeomVertexData("body vertices", GeomVertexFormat.getV3n3t2(), Geom.UHStatic)
        vdata = self.bodydata
        circleGeom = Geom(vdata) # this was originally a copy of all previous geom in vdata...
        vertWriter = GeomVertexWriter(vdata, "vertex")
        #colorWriter = GeomVertexWriter(vdata, "color")
        normalWriter = GeomVertexWriter(vdata, "normal")
#        drawReWriter = GeomVertexRewriter(vdata, "drawFlag")
        texReWriter = GeomVertexRewriter(vdata, "texcoord")

        startRow = vdata.getNumRows()
        vertWriter.setRow(startRow)
        #colorWriter.setRow(startRow)
        normalWriter.setRow(startRow)       
        texReWriter.setRow(startRow)   
       
        #axisAdj=Mat4.rotateMat(45, axis)*Mat4.scaleMat(radius)*Mat4.translateMat(pos)
        perp1 = quat.getRight()
        perp2 = quat.getForward()   
        
        dr = 0.25 # EXPERIMENTAL: ADDING RADIAL NOISE
#        print "Experimental noise off"
        #vertex information is written here
        angleSlice = 2 * pi / numVertices
        currAngle = 0
        for i in xrange(numVertices+1): 
            adjCircle = pos + (perp1 * cos(currAngle) + perp2 * sin(currAngle)) * radius * (.5+dr*random.random())
            normal = perp1 * cos(currAngle) + perp2 * sin(currAngle)       

            normalWriter.addData3f(normal)
            vertWriter.addData3f(adjCircle)
            texReWriter.addData2f(float(UVcoord[0]*i) / numVertices,UVcoord[1])            # UV SCALE HERE!
            #colorWriter.addData4f(0.5, 0.5, 0.5, 1)
            currAngle += angleSlice 
        
        #we cant draw quads directly so we use Tristrips
        if (startRow != 0):
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
            return circleGeomNode
 
    
#    def genBranch(self, rootNode,  angFunc, aParam, radFunc, rParam, branchlen,branchSegs):
#        # defines a "branch" as a list of BranchNodes and then calls branchfromNodes        
#        
#        # other notes: a tree cares about absolute "up" and left and right are
#        # relateive to abs "up" cross product branches "up" (forward along the branch)
#            
#        rootPos,rootRad,rootL,rootQuat,rootUV, rootDL = rootNode
##        radius = rfact*radius # SHOULD BE radFunc CALL HERE
#        quat = angFunc(rootQuat,**aParam) #rotate branch to a new direction
##        quat = rootQuat
##        quat.setFromAxisAngle(random.randint(0,30),Vec3(0,sqrt(.5),sqrt(.5)))
#        prevNode = BranchNode._make([rootPos,.5*rootRad,rootL,quat,rootUV,0]) # COULD SUM FROM BASE OF TRY BY USING rootDL instead of 0
#        thisBranch = [prevNode] # start new branch list with newly created rootNode
#
#        Lseg = float(branchlen/branchSegs)   
#        for i in range(1,branchSegs+1): # start a 1, 0 is root node, now previous
#            aParam = {'H':0,'dh':0,'P':0,'dp':5.0,'R':0,'dr':5}        
#            quat = angFunc(prevNode.quat,**aParam) #rotate branch to a new direction
#
#            pos = prevNode.pos + quat.getUp() * Lseg
#            radius = radFunc(prevNode,**rParam)
##            perim = 2*_polySize*radius*sin(pi/_polySize) # use perimeter to calc texture length/scale
#            perim = 1 # integer tiling of uScale; looks better
#            
#            UVcoord = (_uvScale[0]*perim, prevNode.texUV[1] + Lseg*float(_uvScale[1]) ) # This will keep the texture scale per unit length constant
#            newNode = BranchNode._make([pos,radius,Lseg,quat,UVcoord,branchlen-i*Lseg]) # i*Lseg = distance from root
#            thisBranch.append(newNode)
#            prevNode = newNode # this is now the starting point on the next iteration
#        self.branchFromNodes(thisBranch) 
#        return thisBranch
        
    def generate(self, posFunc, pParam, radFunc, rParam, branchlen,branchSegs):
        # defines a "branch" as a list of BranchNodes and then calls branchfromNodes
        # Creates a scaled length,width, height geometry to be later
        # otherwise can not maintain UV per unit length (if that's desired)
        # returns non-rotated, unpositioned geom node
        
        rootNode = BranchNode._make([Vec3(0,0,0),rParam['R0'],branchlen,Quat(),_uvScale,0]) # initial node      # make a starting node flat at 0,0,0        
        thisBranch = [rootNode] # start new branch list with newly created rootNode
        prevNode = rootNode
        _UP_ = Vec3(0,0,1) # grow along Z axis
        
        Lseg = branchlen/branchSegs
        for i in range(1,branchSegs+1): # start a 1, 0 is root node, now previous
            nAmp = .05
            noise = Vec3(-1+2*random.random(),-1+2*random.random(),0)*nAmp 
            pos = Vec3(0,0,0) + _UP_ * Lseg * i  +noise
            dL = prevNode.deltaL + (pos-prevNode.pos).length() # cumulative length accounts for off axis node lengths
            radius = radFunc(position=dL/branchlen,**rParam) # pos.length() wrt to root. if really curvy branch, may want the sum of segment lengths instead..

#            perim = 2*_polySize*radius*sin(pi/_polySize) # use perimeter to calc texture length/scale
            perim = 1 # integer tiling of uScale; looks better            
            UVcoord = (_uvScale[0]*perim, rootNode.texUV[1] + dL*float(_uvScale[1]) ) # This will keep the texture scale per unit length constant
            
            newNode = BranchNode._make([pos,radius,Lseg,rootNode.quat,UVcoord,dL]) # i*Lseg = distance from root
            thisBranch.append(newNode)
            prevNode = newNode # this is now the starting point on the next iteration

        # sends the BranchNode list to the drawBody function to generate the 
        # actual geometry
        for i,node in enumerate(thisBranch):
#            if i == 0: isRoot = True
#            else: isRoot = False
#            if i == len(nodeList)-1: keepDrawing = True
#            else: 
            self.drawBody(node.pos, node.quat, node.radius,node.texUV)
            
        return thisBranch


def RadiusFunc(*args,**kwargs):
    # radius proportional to length from root of this branch to some power
    rfact = kwargs['rfact']
#    power = kwargs['power']
#    curNode = kwargs['curNode']
#    newRad = rfact*curNode.radius
    relPos = kwargs['position']
    R0 = kwargs['R0']
    newRad = R0*(1 - relPos*rfact)
#    if curNode.deltaL > 0:
#        newRad = rfact*(-curNode.deltaL**power)
#    else:
#        newRad = curNode.radius
#    print curNode.deltaL, newRad
    return newRad

BranchNode = namedtuple('BranchNode','pos radius len quat texUV deltaL') # len is TO next node (delta pos vectors)
# deltaL is cumulative distance from the branch root (sum of node lengths)

if __name__ == "__main__":
#    random.seed(11*math.pi)
    numGens = 1
    numSegs = 8 # number of nodes per branch; 2 ends and n-2 body nodes
    _skipChildren = 2 # how many nodes in from the base; including the base, to exclude from children list

    L0 = 5.0 # initial length
    lfact = .3    # length ratio between branch generations

    R0 = .5 #initial radius
#    Rf = .1 # final radius
#    rfact = (Rf/R0)**(1.0/numSegs) # fixed start and end radii
    rfact = .9
  
    _uvScale = (1,.4) #repeats per unit length (around perimeter, along the tree axis) 
    _BarkTex_ = "barkTexture.jpg"
    
    _LeafTex_ = 'Green Leaf.png'
    _LeafModel = 'myLeafModel.x'
    _LeafScale = .75
    _DoLeaves = 0
 
    base = ShowBase()
    base.cam.setPos(0, -2*L0, L0/2)
    base.setFrameRateMeter(1)
    bark = base.loader.loadTexture(_BarkTex_)    
#TODO: make parameters: probably still need a good Lfunc. 
# need angle picking# such that branchs tend to lie flat, slight "up" and out. 
# Distribute branches uniform around radius. 
# "Crown" the trunk; possibly branches. 
# choose "bud" locations other than branch nodes.
# define circumference function (pull out of drawBody())

    Aparams = {'H':0,'dh':0,'P':0,'dp':0,'R':0,'dr':0}  
    Rparams = {'rfact':rfact,'R0':R0}

    trunk = Branch("Trunk")
    trunk.setTwoSided(1)    
    trunk.reparentTo(base.render)
    B0 = trunk.generate(cos, Aparams, RadiusFunc, Rparams, L0, numSegs)
    trunk.setTexture(bark)
    
    children = B0[_skipChildren:-1]*2 # each node in the trunk will span a branch # poor man's multiple branch/node
    nextChildren = []
    leafNodes = []
    for gen in range(1,numGens+1):
        print "Calculating branches..."
        print "Generation: ", gen, " children: ", len(children)
        for bud in children:
            Aparams = {'H':180,'dh':180,'P':67,'dp':22,'R':0,'dr':0}
            B = Branch("Branch1")
            Rparams['R0']= .8*bud.radius
            curBr = B.generate(cos, Aparams, RadiusFunc, Rparams, L0*lfact**gen, numSegs+1-gen) # return the current branch node list
#            B.setTexture(bark)
            B.setHpr(random.randint(-180,180),60,0)
            B.setPos(bud.pos)
            B.reparentTo(trunk)
            
            nextChildren += curBr[_skipChildren:-1] # don'tinclude the root
        children = nextChildren 
        nextChildren = []
#        if gen==numGens-1:
    leafNodes = children
    
    if _DoLeaves:
        print "adding foliage"
        for node in leafNodes:
            trunk.drawLeaf(node.pos,node.quat,_LeafScale)

    trunk.setScale(1)        
    trunk.flattenStrong()
    trunk.write_bam_file('sampleTree.bam')
    
    def rotateTree(task):
        phi = 15*task.time
        trunk.setH(phi)
        return task.cont
#    base.taskMgr.add(rotateTree,"merrygoround")
    
#    base.toggleWireframe()
    base.accept('escape',sys.exit)
    base.accept('z',base.toggleWireframe)
    base.run()
