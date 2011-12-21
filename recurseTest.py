# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 09:47:48 2011

@author: shawn
"""


class Branch():
    def __init__(self,l=0,ang1=0,ang2=0,clist=[]):
        self.length = l
        self.theta = ang1
        self.phi = ang2
        self.children = clist
        
def getChildren(numChil=2):
    return [Branch()]*numChil
    
    
    
    # parent is a list of N generations  
    # each generation will split into numChildren
    # children of generation n+1

if __name__ == '__main__':
    numChildren = 2
    B = Branch(1,0,0,[])
    B.children = getChildren()
    for sib in B.children:
        sib.children = getChildren()
        
    
        

