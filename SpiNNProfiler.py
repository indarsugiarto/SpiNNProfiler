#!/usr/bin/env python
"""
SYNOPSIS
    Simple framework to do experiment with core frequency, utilization, and chip temperature. 
Created on 2 Nov 2015

@author: indi
"""
import sys
from PyQt4 import Qt
from myTools import mainWidget

if __name__=="__main__":
    myApp = Qt.QApplication(sys.argv)
    mGUI = mainWidget()
    mGUI.show()
    sys.exit(myApp.exec_())
    