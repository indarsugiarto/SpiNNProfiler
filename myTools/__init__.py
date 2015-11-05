import sys
from PyQt4 import Qt, QtCore, QtGui, QtNetwork
from myTools.myPlotterT import Twidget
from myTools.myPlotterU import Uwidget
from myTools.myTub import Tubwidget

import constDef as DEF

import os
from datetime import datetime

class mainWidget(QtGui.QWidget):
    sdpUpdate = QtCore.pyqtSignal('QByteArray')     # This signal MUST defined here, NOT in the init()
    tubUpdate = QtCore.pyqtSignal('QByteArray')
    
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        ## GUI-stuff
        self.pbTub = QtGui.QPushButton("Tubotron", self)
        self.pbPltT = QtGui.QPushButton("Temperature Plotter", self)
        self.pbPltU = QtGui.QPushButton("Utilization Plotter", self)
        self.cbSave = QtGui.QCheckBox("Save Data to Disk", self)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.pbTub)
        self.layout.addWidget(self.pbPltT)
        self.layout.addWidget(self.pbPltU)
        self.layout.addWidget(self.cbSave)
        self.setLayout(self.layout)
        self.setMaximumSize(250, 200)
        self.setMinimumSize(250, 200)
        self.setWindowTitle("SpiNNProfiler")
        
        ## Data sources
        self.initRptSock(DEF.RECV_PORT)
        self.initTubSock(DEF.TUBO_PORT)
        
        
        ## Modules
        self.tw = Twidget(4); self.pbPltTClicked()  # let's try with 4 chips
        self.uw = Uwidget(4); self.pbPltUClicked()
        self.tub = Tubwidget(); self.pbTubClicked()
        
        ## Signal-slot connection
        #self.sdpUpdate = QtCore.pyqtSignal([Qt.QByteArray])
        
        self.connect(self.pbTub, QtCore.SIGNAL("clicked()"), QtCore.SLOT("pbTubClicked()"))
        self.connect(self.pbPltT, QtCore.SIGNAL("clicked()"), QtCore.SLOT("pbPltTClicked()"))
        self.pbPltU.clicked.connect(self.pbPltUClicked)
        self.cbSave.stateChanged.connect(self.cbSaveToggled)
        
        #self.connect(self, QtCore.SIGNAL("sdpUpdate"), self.tw.newData)
        #self.connect(self, QtCore.SIGNAL("sdpUpdate"), self.uw.newData)
        self.sdpUpdate.connect(self.tw.newData)     # when defining signal-slot in pyqt, the type can be omitted
        self.sdpUpdate.connect(self.uw.newData)
        self.tubUpdate.connect(self.tub.newData)
        
        #final touch, let's display the celcius and percent
        self.tw.cbMode.setCurrentIndex(1)
        self.uw.cbMode.setCurrentIndex(1) 

    def initRptSock(self, port):
        print "Try opening port-{} for Profiler Report...".format(port),
        self.RptSock = QtNetwork.QUdpSocket(self)
        #result = self.sock.bind(QtNetwork.QHostAddress.LocalHost, DEF.RECV_PORT) --> problematik dengan penggunaan LocalHost
        result = self.RptSock.bind(port)
        if result is False:
            print 'Cannot open UDP port-{}'.format(port)
            #sys.exit(1)
            self.RptInitialized = False
            return
        else:
            print 'done!'
        #self.connect(self.sock, Qt.SIGNAL("readyRead()"), self, Qt.SLOT("readSDP()"))
        #self.udpSocket.readyRead.connect(self.processPendingDatagrams)
        self.RptSock.readyRead.connect(self.readRptSDP)
        
    @QtCore.pyqtSlot()
    def readRptSDP(self):
        while self.RptSock.hasPendingDatagrams():
            szData = self.RptSock.pendingDatagramSize()
            datagram, host, port = self.RptSock.readDatagram(szData)
            self.sdpUpdate.emit(datagram)
            

    def initTubSock(self, port):
        print "Try opening port-{} for Tubotron...".format(port),
        self.TubSock = QtNetwork.QUdpSocket(self)
        #result = self.sock.bind(QtNetwork.QHostAddress.LocalHost, DEF.RECV_PORT) --> problematik dengan penggunaan LocalHost
        result = self.TubSock.bind(port)
        if result is False:
            print 'Cannot open UDP port-{}'.format(port)
            #sys.exit(1)
            self.TubInitialized = False
            return
        else:
            print 'done!'
        #self.connect(self.sock, Qt.SIGNAL("readyRead()"), self, Qt.SLOT("readSDP()"))
        #self.udpSocket.readyRead.connect(self.processPendingDatagrams)
        self.TubSock.readyRead.connect(self.readTubSDP)
    
    @QtCore.pyqtSlot()
    def readTubSDP(self):
        """
        """
        while self.TubSock.hasPendingDatagrams():
            szData = self.TubSock.pendingDatagramSize()
            datagram, host, port = self.TubSock.readDatagram(szData)
            self.tubUpdate.emit(datagram)
        
    @QtCore.pyqtSlot()
    def pbTubClicked(self):
        self.tub.show()

    @QtCore.pyqtSlot()
    def pbPltTClicked(self):
        self.tw.show()
        
    @QtCore.pyqtSlot()
    def pbPltUClicked(self):
        self.uw.show()

    def closeEvent(self, e):
        self.tw.close()
        self.uw.close()
        self.tub.close()

    def cbSaveToggled(self):
        dt = datetime.now() #Profiler-14.8.2015-22.10
        dirName = "../experiments/Profiler-%d.%d.%d-%d.%d" % (dt.day, dt.month, dt.year, dt.hour, dt.minute)
        dirName = "experiments/Profiler-%d.%d.%d-%d.%d" % (dt.day, dt.month, dt.year, dt.hour, dt.minute)
        if self.cbSave.isChecked():
            os.mkdir(dirName, 0755)
            self.tw.saveToFileTriggered(True, dirName)
            self.uw.saveToFileTriggered(True, dirName)
        else:
            self.tw.saveToFileTriggered(False, None)
            self.uw.saveToFileTriggered(False, None)
        
