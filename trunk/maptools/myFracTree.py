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
#import pycallgraph
#pycallgraph.start_trace()

_polySize = 7


class Bud(object):
    # still need bud objects to pack info by name; easier that way
    def __init__(self,position=Vec3(0,0,0),Hpr=Vec3(0,0,0),length=0,rad=0):
        self.pos = position
        self.Hpr = Hpr
        self.maxL = length
        self.maxRad = rad
        
class Branch(NodePath):
    def __init__(self, nodeName, L, initRadius, nSeg):
        NodePath.__init__(self, nodeName)
        self.numPrimitives = 0
        self.nodeList = []    # for the branch geometry itself
        self.buds = []        # a list of children. "buds" for next gen of branchs
        self.length = L            # total length of this branch; note Node scaling will mess this up! 
        self.R0 = initRadius
        self.nSeg = nSeg
        self.gen = 0        # ID's generation of this branch (trunk = 0, 1 = primary branches, ...)
        # contains 2 Vec3:[ position, and Hpr]. Nominally these are set by the parent Tree class
        # with it's add children function(s)
        
        self.bodydata = GeomVertexData("body vertices", GeomVertexFormat.getV3n3t2(), Geom.UHStatic)        
        self.bodies = NodePath("Bodies")
        self.bodies.reparentTo(self)
        
        self.coll = self.attachNewNode(CollisionNode("Collision"))       
        self.coll.show()       
        self.coll.reparentTo(self)

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
        
#TODO: PROPERLY IMPLEMENT RADIAL NOISE        
        #vertex information is written here
        angleSlice = 2 * pi / numVertices
        currAngle = 0
        for i in xrange(numVertices+1): 
            adjCircle = pos + (perp1 * cos(currAngle) + perp2 * sin(currAngle)) * radius * (.5+bNodeRadNoise*random.random())
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
        
    def generate(self, Params,baseFlair=[]):
        # defines a "branch" as a list of BranchNodes and then calls branchfromNodes
        # Creates a scaled length,width, height geometry to be later
        # otherwise can not maintain UV per unit length (if that's desired)
        # returns non-rotated, unpositioned geom node
        
#        branchlen = Params['L']
#        branchSegs = Params['nSegs']
        Params.update({'iSeg':0})
        # Base flair: nice to flair out the first segment on a "trunk" branch sometimes
        if baseFlair:
            bff = baseFlair
        else:
            bff = 1
        rootPos = Vec3(0,0,0) # + self.PositionFunc(**Params) #add noise to root node; same as others in loop
        rootNode = BranchNode._make([rootPos,bff*self.R0,Vec3(0,0,0),Quat(),_uvScale,0,self.length]) # initial node      # make a starting node flat at 0,0,0        
        self.nodeList = [rootNode] # start new branch list with newly created rootNode
        prevNode = rootNode
        
        for i in range(1,self.nSeg+1): # start a 1, 0 is root node, now previous
            Params.update({'iSeg':i})
            newPos = self.PositionFunc(**Params)
            fromVec = newPos - prevNode.pos # point
            dL = (prevNode.deltaL + fromVec.length()) # cumulative length accounts for off axis node lengths; percent of total branch length
            radius = self.RadiusFunc(position=dL/self.length,**Params) # pos.length() wrt to root. if really curvy branch, may want the sum of segment lengths instead..

# MOVE TO UVfunc
#            perim = 2*_polySize*radius*sin(pi/_polySize) # use perimeter to calc texture length/scale
            # if going to use above perim calc, probably want a high number of BranchNodes to minimuze the Ushift at the nodes
            perim = 1 # integer tiling of uScale; looks better; avoids U shifts at nodes     
            UVcoord = (_uvScale[0]*perim, rootNode.texUV[1] + dL*float(_uvScale[1]) ) # This will keep the texture scale per unit length constant
##

            newNode = BranchNode._make([newPos,radius,fromVec,rootNode.quat,UVcoord,dL,self.length-dL]) # i*Lseg = distance from root
            self.nodeList.append(newNode)
            prevNode = newNode # this is now the starting point on the next iteration

        # sends the BranchNode list to the drawBody function to generate the 
        # actual geometry
        for i,node in enumerate(self.nodeList):
#            if i == 0: isRoot = True
#            else: isRoot = False
#            if i == len(nodeList)-1: keepDrawing = True
#            else: 
            self.drawBody(node.pos, node.quat, node.radius,node.texUV)
        return self.nodeList
        
    def addNewBuds(self): 
#TODO: GENERALIZE THIS SECTION
#        budPos = budHpr = []
#        rad = maxL = 0
            
        [gH,gP,gR] = self.getHpr(base.render) # get this branch global Hpr for later
#        nbud = budPerLen * self.length
#        budPosArr = [x*minBudSpacing for x in range(self.length/minBudSpacing)]
#        sampList = random.choice(budPosArr,nbud)
        
#        sampList = random.sample(self.nodeList[_skipChildren:-1],5)
        sampList = [self.nodeList[-1]]
        for nd in sampList: # just use nodes for now
            budPos = nd.pos
            maxL = lfact*self.length
            rad = rfact*nd.radius # NEW GEN RADIUS - THIS SHOULD BE A PARAMETER!!!
    
            #Child branch Ang func - orient the node after creation
            # trunk bud multiple variables
            budsPerNode = random.randint(1,3) +1    # +1 since 1 branch will always "continue"
            hdg = range(0,360,360/budsPerNode)
#            budRot = random.randint(-hdg[1],hdg[1]) # add some noise to the trunk bud angles
            for i,h in enumerate(hdg):                        
                angP = random.gauss(budP0,budPnoise)
                angR = random.randint(-45,45)
                if i==0:
                    budHpr = Vec3(gH,gP,gR) # at least 1 branch continues on current heading                    
                else:
                    budHpr = Vec3(gH+h,angP,angR)
                self.buds.append([budPos,rad,budHpr,maxL])
                
    def interpLen(self,inLen):
#BranchNode = namedtuple('BranchNode','pos radius fromVector quat texUV deltaL d2t') 
        outLen = []        
        for node in self.nodeList:
            if node.deltaL >= inLen: 
                prevNode = node
                break
        delta = inLen - prevNode.deltaL
        outLen = prevNode.pos + prevNode.fromVector*delta 
#TODO: TOVECTORS ARE WRONG> THEY ARE REALLY FROM VECTORS...need To's        
        return outLen
        
    def UVfunc(*args,**kwargs):
        pass # STUB
    def Circumfunc(*args,**kwargs):
        pass # STUB

    def PositionFunc(self,*args,**kwargs):
        upVector = kwargs['upVector']
        iSeg = kwargs['iSeg']
        nAmp = kwargs['Anoise']    
#        branchSegs = kwargs['nSegs']
        cXfactors = kwargs['cXfactors']
        cYfactors = kwargs['cYfactors']
        
        Lseg = float(self.length)/self.nSeg # self.length set at init()
        relPos = Lseg*iSeg / self.length
   
        dX = sum([term[0]*sin(2*pi*term[1]*relPos+term[2]) for term in cXfactors])
        dY = sum([term[0]*sin(2*pi*term[1]*relPos+term[2]) for term in cYfactors])
        noise = Vec3(-1+2*random.random(),-1+2*random.random(),0)*nAmp 
        newPos = Vec3(0,0,0) + upVector*Lseg*iSeg  + noise + Vec3(dX,dY,0)
        return newPos
        
#    def PositionFunc(self,*args,**kwargs):
#        upVector = kwargs['upVector']
#        iSeg = kwargs['iSeg']
#        nAmp = kwargs['Anoise']    
##        branchlen = kwargs['L']
#        branchSegs = kwargs['nSegs']
#    
#        Lseg = float(self.length)/branchSegs # self.length set at init()
#        noise = Vec3(-1+2*random.random(),-1+2*random.random(),0)*nAmp 
#        newPos = Vec3(0,0,0) + upVector*Lseg*iSeg  + noise 
#        return newPos
        
    def RadiusFunc(self,*args,**kwargs):
        # radius proportional to length from root of this branch to some power
        rTaper = kwargs['rTaper']
        relPos = kwargs['position']
#        R0 = kwargs['R0']
        newRad = self.R0*(1 - (1-rTaper)*relPos) # linear taper Vs length. pretty typical        
        return newRad

class GeneralTree(NodePath):
    
    def __init__(self,L0,R0,numSegs,bark,nodeName):
        NodePath.__init__(self,nodeName)        
        self.L0 = L0
        self.R0 = R0
        self.numSegs = numSegs
        self.trunk = Branch("Trunk",L0,R0,2*numSegs)
        self.trunk.reparentTo(self)
        self.trunk.setTexture(bark)
    
    def generate(self,*args,**kwargs):
#        lfact = kwargs['lfact']
        bff = kwargs['baseflair']
        self.trunk.generate(Params,baseFlair=bff)
        self.trunk.addNewBuds()
        children = [self.trunk] # each node in the trunk will span a branch 
        nextChildren = []
        leafNodes = []
        
        for gen in range(1,numGens+1):
            Lgen = self.L0*lfact**gen
            print "Calculating branches..."
#            print "Generation: ", gen, " children: ", len(children), "Gen Len: ", Lgen
            for thisBranch in children:
                for ib,bud in enumerate(thisBranch.buds):
                    # Create Child NodePath instance
                    
                    # experimental curvature terms
                    Params.update(cXfactors = [(.1*bud[3]*random.gauss(0,.333),0.25,0),
                                                  (.1*bud[3]*random.gauss(0,.333),.5,0),
                                                    (.1*bud[3]*random.gauss(0,.333),.75,0),
                                                    (.1*bud[3]*random.gauss(0,.333),1,0)])
                    Params.update(cYfactors = [(.1*bud[3]*random.gauss(0,.333),0.25,0),
                                                  (.1*bud[3]*random.gauss(0,.333),.5,0),
                                                    (.1*bud[3]*random.gauss(0,.333),.75,0),
                                                    (.0*bud[3]*random.gauss(0,.333),1,0)])
                    
                                                    
                    newBr = Branch("Branch1",bud[3],bud[1],self.numSegs+1-gen) 
                    newBr.reparentTo(thisBranch)
    #                newBr.setTexture(bark) # If you wanted to do each branch with a unqiue texture
                    newBr.gen = gen
                    
                    # Child branch Radius func 
    #                Rparams['R0']= bud[1]
    
                    # Child branch position Func
                    newBr.setPos(bud[0])                
                    lFunc = Lgen*(1-Lnoise/2 - Lnoise*random.random())
                    Params['Anoise'] = bud[1]*posNoise    # noise func of tree or branch?
                    Params.update({'L':lFunc,'nSegs':self.numSegs+1-gen})
                    Params.update({'rTaper':rTaper**gen})
                    newBr.setHpr(base.render,bud[2]) 
                    
                    #Create the actual geometry now
                    newBr.generate(Params)
    
                    # Create New Children Function
                    newBr.addNewBuds()
                    # just add this branch to the new Children;
                    nextChildren.append(newBr)                 
                    # use it's bud List for new children branches.                
            children = nextChildren # assign Children for the next iteration
            nextChildren = []

        if _DoLeaves:
            print "adding foliage...hack adding to nodes, not buds!"
            for thisBranch in children:
    #            for node in thisBranch.nodeList[_skipChildren:]:
                self.drawLeaf(thisBranch,thisBranch.nodeList[-1].pos,_LeafScale)


    #this draws leafs when we reach an end       
    def drawLeaf(self,parent,pos, scale=0.125):
        leafNode = NodePath("leaf")
        leafNode.setTwoSided(1)
        leafMod.instanceTo(leafNode)
        leafNode.reparentTo(parent)
        leafNode.setPos(pos)
        leafNode.setScale(scale)
        leafNode.setHpr(0,0,0)


    
BranchNode = namedtuple('BranchNode','pos radius fromVector quat texUV deltaL d2t') 
# fromVector is TO next node (delta of pos vectors)
# deltaL is cumulative distance from the branch root (sum of node lengths)

if __name__ == "__main__":
    base = ShowBase()    
#    random.seed(11*math.pi)
    _UP_ = Vec3(0,0,1) # General axis of the model as a whole

    # TRUNK AND BRANCH PARAMETERS
    numGens = 2    # number of branch generations to calculate (0=trunk only), usually don't want much more than 4-6..if that!
    print numGens
    
    L0 = 6      # initial length
    R0 = 1        # initial radius
    numSegs = 6    # number of nodes per branch; +1 root = 7 total BranchNodes per branch
    taper0 = 1    # Initial taper; 1= same diam end to end
    
    _skipChildren = 0 # how many nodes in from the base to exclude from children list; +1 to always exclude base
    lfact = 0.8   # length ratio between branch generations
    # often skipChildren works best as a function of total lenggth, not just node count        
    rfact = 1     # radius ratio between generations
    rTaper = .65 # taper factor; % reduction in radius between tip and base ends of branch
    budP0 = 45    # a new bud's nominal pitch angle
    
    budPnoise = 10 # variation in bud's pitch angle
    bNodeRadNoise = 0.1 # EXPERIMENTAL: ADDING Vertex RADIAL NOISE for shape interest
    posNoise = 0.0    # random noise in The XY plane around the growth axis of a branch
    Lnoise = 3    # percent(0-1) length variation of new branches

    _uvScale = (2,1.0/3) #repeats per unit length (around perimeter, along the tree axis) 
    _BarkTex_ = "barkTexture.jpg"
#    _BarkTex_ ='./resources/models/barkTexture-1z.jpg'
    

    # LEAF PARAMETERS
#    _LeafTex = 'Green Leaf.png'
    _LeafModel = 'myLeafModel8.x'
#    _LeafModel = 'shrubbery'
#    _LeafTex = 'material-10-cl.png'
    
#    leafTex = base.loader.loadTexture('./resources/models/'+ _LeafTex)
    leafMod = base.loader.loadModel('./resources/models/'+ _LeafModel)
#    leafMod.setScale(.01)
    leafMod.setZ(-.5)
#    leafMod.setScale(2,2,1)
    leafMod.flattenStrong()
    _LeafScale = 3
    _DoLeaves = 1 # not ready for prime time; need to add drawLeaf to Tree Class
 
    bark = base.loader.loadTexture(_BarkTex_)    

    Params = {'L':L0,'nSegs':numSegs,'Anoise':posNoise*R0,'upVector':_UP_}
    Params.update({'rTaper':rTaper,'R0':R0})
    Params.update(cXfactors = [(.05*R0,1,0),(.05*R0,2,0)],cYfactors = [(.05*R0,1,pi/2),(.05*R0,2,pi/2)])

    np = 6
    plts = range(np**2) # 6x6 array
    ds = 5.0
    for it in range(10):
        tree = GeneralTree(L0,R0,numSegs,bark,"my tree")    
        tree.generate(Params,baseflair=1.45)
        tree.reparentTo(base.render)

        # DONE GENERATING. WRITE OUT UNSCALED MODEL
        print "writing out file"
        tree.setScale(1) 
        tree.setH(180)
        tree.setZ(-0.1)
        tree.flattenStrong()
        tree.writeBamFile('./resources/models/sampleTree'+str(it)+'.bam')

        p = random.choice(plts)
        tx = ds*(p/np)
        ty = ds*(p%np)
        tree.setPos(tx,ty,0)

##############################

    ruler = base.loader.loadModel('./resources/models/plane')
    ruler.setPos(-(R0+.25),0,1) # z = .5 *2scale
    ruler.setScale(.05,1,2) #2 unit tall board
    ruler.setTwoSided(1)
    ruler.reparentTo(base.render)
    
    def rotateTree(task):
        phi = 10*task.time
        tree.setH(phi)
        return task.cont
    base.taskMgr.add(rotateTree,"merrygoround")

    base.cam.setPos(0,-4*L0, L0/2)    
    base.render.setShaderAuto()
    base.setFrameRateMeter(1)    
#    base.toggleWireframe()
    base.accept('escape',sys.exit)
    base.accept('z',base.toggleWireframe)
#    pycallgraph.make_dot_graph('treeXpcg.png')
    base.setBackgroundColor((.0,.5,.9))
    base.render.analyze()
    base.run()

#TODO: 
#   - clean up: move branch Hpr out of bud and into child branch property
#    - choose "bud" locations other than branch nodes and random circumfrentially.
#    - numSegs to parameter into branch; numSegs = f(generation), fewer on younger
#        prob set a buds per length var
#    - COULD do a render to texture for the last limbs and leaves; define multiple plane 
        # cross sections, create them, then append them to the last real node before RTT
#     make parameters: probably still need a good Lfunc. 
#     Distribute branches uniform around radius. 
#     "Crown" the trunk; possibly branches. - single point; no rad func and connect all previous nodes to point
#     define circumference function (pull out of drawBody())
# 