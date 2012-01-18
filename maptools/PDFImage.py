# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 13:19:19 2011

@author: us997259
"""

from PIL import Image
import numpy as np
from random import uniform


class PDFImage():
# TODO: INCorporate the Grid concept + random displacements into this pdf version
# This amounts to modifying the underlying PDF image map
    
    Sx = 1
    Sy = 1 # scaling factors
    def __init__(self,filename,Xmax=None, Ymax=None):
        self.A = np.array(Image.open(filename),dtype='float') # raw data array
        if Xmax: 
            self.Sx = float(Xmax) / self.A.shape[1]
            self.Sy = self.Sx        # assume square first
        if Ymax: self.Sy = float(Ymax) / self.A.shape[0] # set separate if available
        mdf = self.A.sum(0)
        mdf /= mdf.sum()
        self.inv = mdf.cumsum() # used to calculate newX from the X pdf
        
    def getNewLocation(self):
        newX, newY = [],[]
        while not newX or not newY:
            rx = uniform(0,1)
            tmpx = (self.inv<=rx).nonzero()
            # right. ok. find inv < rx percetile then find all the nozero (true) element
            # indexes the [0] delistifies the list from nonzero and max()
            # takes the largest index in that non-zero list
            # This essentially rounds down to the nearest integer location
            if tmpx[0] !=[]: 
                newX =tmpx[0].max()  #invert the cdf        
            else:
                print rx,tmpx
#            plot(self.inv)
#            plot(newX, rx,'r.')
#            show();
                   
            normX = self.A[:,newX].sum()
            if normX > 0:
                cdf = self.A[:,newX].cumsum() / normX # normalized cum pdf a column X
                ry = uniform(0,1)   # randome percentile in y dimension
                tmp =  (cdf<=ry).nonzero()
    #            print tmp[0]
                if tmp[0] !=[]: 
                    newY =tmp[0].max()  #invert the cdf        
                    newY = self.A.shape[1] - newY # INVERT Y axis to match a 0,0 origin at lower left; match panda3d grid later
                else:
                    print ry,tmp[0]
        #        plot(cdf)
        #        plot(newY, ry,'g.')            
        #        show()   

        newY = self.Sy * newY
        newX = self.Sx * newX
        return [newX, newY]
        
        
        
#from pylab import plot,show
#TM = PDFImage(fn)
#nTree = 2500
#x = np.array(np.zeros(nTree),dtype=float)
#y = np.array(np.zeros(nTree),dtype=float)
#
#for i in range(nTree):
##    print i
#    a,b = TM.getNewLocation()
##    if a and b:
#    x[i] = a
#    y[i] = b
#plot(x, y,'x')
#show()