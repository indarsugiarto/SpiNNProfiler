import struct
from PyQt4 import Qt, QtGui, QtCore, QtNetwork
import PyQt4.Qwt5 as Qwt
from PyQt4.Qwt5.anynumpy import *
import constDef as DEF

class Uwidget(QtGui.QWidget):
    """
    Temperature plot
    """
    def __init__(self, nChip, parent=None):
        """
        Layout: top : Dropbox Sensor and Mode
                bottom: QwtPlot 
        """
        QtGui.QWidget.__init__(self, parent)

        # Initialize GUI
        CPUlabel = QtGui.QLabel("CPU", self)
        CHIPlabel = QtGui.QLabel("Chip", self)
        MODElabel = QtGui.QLabel("Mode", self)
        
        self.cbCPU = QtGui.QComboBox(self)
        items = list()
        for i in range(18):
            coreStr = "core-%d" % i
            items.append(coreStr)
        self.cbCPU.addItems(items)
        self.cbCPU.addItem("All")
        self.cbCPU.setCurrentIndex(18)
        self.cbCPU.currentIndexChanged.connect(self.changeCPU)

        self.cbChip = QtGui.QComboBox(self)
        self.cbChip.addItem("chip<0,0>")
        self.cbChip.addItem("chip<0,1>")
        self.cbChip.addItem("chip<1,0>")
        self.cbChip.addItem("chip<1,1>")
        self.cbChip.setCurrentIndex(0)
        self.cbChip.currentIndexChanged.connect(self.changeChip)
        
        self.cbMode = QtGui.QComboBox(self)
        self.cbMode.addItem("Absolute")
        self.cbMode.addItem("Relative")
        self.cbMode.setCurrentIndex(0)
        self.cbMode.currentIndexChanged.connect(self.changeMode)
        
        self.qwtU = UPlot(nChip)
        self.qwtU.cpuChanged(self.cbCPU.currentIndex())
        self.qwtU.chipChanged(self.cbChip.currentIndex())
       
        hLayout = QtGui.QHBoxLayout()
        hLayout.addWidget(CPUlabel)
        hLayout.addWidget(self.cbCPU)
        hLayout.addSpacing(100)
        hLayout.addWidget(CHIPlabel)
        hLayout.addWidget(self.cbChip)
        hLayout.addSpacing(100)
        hLayout.addWidget(MODElabel)
        hLayout.addWidget(self.cbMode)
        hLayout.addStretch()
        vLayout = QtGui.QVBoxLayout()
        vLayout.addLayout(hLayout)
        vLayout.addWidget(self.qwtU)
        self.setLayout(vLayout)
        self.setWindowTitle("CPU Utilization Report")
        
    def changeCPU(self, idx):
        self.qwtU.cpuChanged(idx)
        
    def changeChip(self, idx):
        self.qwtU.chipChanged(idx)
        
    def changeMode(self, idx):
        self.qwtU.modeChanged(idx)

    def newData(self, datagram):
        self.qwtU.readSDP(datagram)

    def saveToFileTriggered(self, state, dirName):
        self.qwtU.saveToFileTriggered(state, dirName)

class UPlot(Qwt.QwtPlot):
    def __init__(self, nChip, *args):
        Qwt.QwtPlot.__init__(self, *args)

        self.cpuIdx = 0
        self.chipIdx = 0
        self.modeIdx = 0
        self.nChip = nChip
        self.setCanvasBackground(Qt.Qt.white)
        self.alignScales()

        # Initialize data
        self.x = arange(0.0, 100.1, 0.5)

        # Initialize working parameters
        self.saveToFile = False
        self.Ufiles = list()
        for i in range(nChip):
            self.Ufiles.append(None)

        
        self.u = list()     # list of list, contains the utilization value
        self.c = list()     # contains the curve value
        for i in range(nChip):
            u = list()
            for j in range(18):
                y = zeros(len(self.x), Float)
                u.append(y)
            self.u.append(u)
        for i in range(18): # for all 18 cores in a chip
            cname = "Core-%d" % (i)
            self.c.append(Qwt.QwtPlotCurve(cname))

        ## Color contants
        clr = [Qt.Qt.red, Qt.Qt.green, Qt.Qt.blue, Qt.Qt.cyan, Qt.Qt.magenta, Qt.Qt.yellow, Qt.Qt.black, Qt.Qt.gray, 
               Qt.Qt.darkRed, Qt.Qt.darkGreen, Qt.Qt.darkBlue, Qt.Qt.darkCyan, Qt.Qt.darkMagenta, Qt.Qt.darkYellow, Qt.Qt.darkGray, Qt.Qt.lightGray, 
               Qt.Qt.red, Qt.Qt.green]
        
        for i in range(18):
            self.c[i].attach(self)
            self.c[i].setPen(Qt.QPen(clr[i], DEF.PEN_WIDTH))
            
        
        self.setTitle("Chip Utilization Report")
        
        self.insertLegend(Qwt.QwtLegend(), Qwt.QwtPlot.BottomLegend);       

        self.setAxisTitle(Qwt.QwtPlot.xBottom, "Time (seconds)")
        self.setAxisTitle(Qwt.QwtPlot.yLeft, "Counter Values")
    

    def alignScales(self):
        self.canvas().setFrameStyle(Qt.QFrame.Box | Qt.QFrame.Plain)
        self.canvas().setLineWidth(1)
        for i in range(Qwt.QwtPlot.axisCnt):
            scaleWidget = self.axisWidget(i)
            if scaleWidget:
                scaleWidget.setMargin(0)
            scaleDraw = self.axisScaleDraw(i)
            if scaleDraw:
                scaleDraw.enableComponent(
                    Qwt.QwtAbstractScaleDraw.Backbone, False)

    
    @QtCore.pyqtSlot()
    def readSDP(self, datagram):       
        fmt = "<HQ2H3I18I"
        pad, hdr, cmd, seq, temp1, temp2, temp3, cpu0, cpu1, cpu2, cpu3, cpu4, cpu5, cpu6, cpu7, cpu8, cpu9, cpu10, cpu11, cpu12, cpu13, cpu14, cpu15, cpu16, cpu17 = struct.unpack(fmt, datagram)
        sax = seq >> 8
        say = seq & 0xFF
        chipID = sax*2+say
        cpuVal = [cpu0, cpu1, cpu2, cpu3, cpu4, cpu5, cpu6, cpu7, cpu8, cpu9, cpu10, cpu11, cpu12, cpu13, cpu14, cpu15, cpu16, cpu17]
        #self.u[chipID] = concatenate((self.u[chipID][:1], self.u[chipID][:-1]), 1)
        if self.modeIdx==0: #use absolute values
            for i in range(18):
                self.u[chipID][i] = concatenate((self.u[chipID][i][:1], self.u[chipID][i][:-1]), 1)
                self.u[chipID][i][0] = cpuVal[i]
        else:
            ## TODO: change to relative 
            for i in range(18):
                self.u[chipID][i] = concatenate((self.u[chipID][i][:1], self.u[chipID][i][:-1]), 1)
                self.u[chipID][i][0] = (DEF.MAX_IDLE_CNTR - cpuVal[i]) * 100 / DEF.MAX_IDLE_CNTR

        for i in range(18):
            self.c[i].setData(self.x, self.u[self.chipIdx][i])
        self.replot()
        
        # save to files
        if self.saveToFile is True:
            iVal = str(seq)
            for i in range(18):
                cpuStr = ",%d" % cpuVal[i]
                iVal += cpuStr
            iVal += "\n"
            sax = seq >> 8
            say = seq & 0xFF
            self.Ufiles[sax*2+say].write(iVal)
        

    def cpuChanged(self, idx):
        # By default, all cores are displayed
        if idx < 18:
            # Detach all curves
            for i in range(18):
                self.c[i].detach()
            self.c[idx].attach(self)
            self.cpuIdx = idx   # so we know, which cpu is last attached
        else:
            # detach previous curve
            self.c[self.cpuIdx].detach()
            # attach all curves
            for i in range(18):
                self.c[i].attach(self)
        
    def chipChanged(self, idx):
        self.chipIdx = idx
        
    def modeChanged(self, idx):
        self.modeIdx = idx
        if idx==0:
            self.setAxisTitle(Qwt.QwtPlot.yLeft, "Counter Values")
            self.setAxisAutoScale(Qwt.QwtPlot.yLeft)
        else:
            self.setAxisTitle(Qwt.QwtPlot.yLeft, "Percent")
            self.setAxisScale(Qwt.QwtPlot.yLeft, 0, 100)
         

    def saveToFileTriggered(self, state, dirName):
        if state is True:
            for i in range(self.nChip):
                fName = dirName + '/temp.' + str(i)
                self.Ufiles[i] = open(fName, 'w')
            self.saveToFile = True

        else:
            self.saveToFile = False
            for i in range(self.nChip):
                if self.Ufiles[i] is not None:
                    self.Ufiles[i].close()
                    self.Ufiles[i] = None

# class DataPlot
