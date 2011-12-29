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
import pycallgraph
pycallgraph.start_trace()

_polySize = 8

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
    numGens = 2
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
    pycallgraph.make_dot_graph('treeXpcg.png')
    base.run()
