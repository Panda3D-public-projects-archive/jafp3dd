# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 09:47:48 2011

@author: shawn
"""
import random
from panda3d.core import Vec3, Quat

class BranchNode():
    def __init__(self,l=1,rad=1,Q=Quat(),pos=Vec3(0,0,0)):
        self.length = l            # MOVE TO GENERATION ROUTINE. DON'T NEED LENGTHS, ONLY POSITIONS
        self.radius = rad            # radius of child end (parent end will obvious have it's radius)
        self.quat = Q         # orientation quaternion; which way am I pointing?
        self.pos = pos     # center point of this branch node
        self.children = []         # list of children from THIS branch's end
        self.gen = 0               # generation ID
#        
    
def getChildren(numSib=2,gen=1):
    print gen
    children = []
    if gen < 4:
        for i in range(numSib):
            sib = BranchNode()
            sib.children = getChildren(numSib,gen+1)
            sib.gen = gen
            children.append(sib)
        return children
    else:
        return []
        
    # parent is a list of N generations  
    # each generation will split into numSibdren
    # children of generation n+1

def selectGen(gen,Tree):
    for child in Tree:
        if child.gen == gen: print child.length
        
if __name__ == '__main__':
    numGens = 3    
#    T = BranchNode() #1st gen (trunk)
#    T.children = getChildren() #2nd gen
    thisBranch = [BranchNode()] # make a starting node flat at 0,0,0
    for i in range(numGens):
        newNode = BranchNode()
        newNode.pos += newNode.quat.getUp() * (1/(i+1))
        newNode.quat.setHpr((0,0,15))
        newNode.radius = 1/(i+1)
        thisBranch.append(newNode)
 
        
    
        

