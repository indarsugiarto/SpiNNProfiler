import struct
from PyQt4 import Qt, QtGui, QtCore, QtNetwork
import PyQt4.Qwt5 as Qwt
from PyQt4.Qwt5.anynumpy import *
import constDef as DEF

class Tubwidget(QtGui.QWidget):
    """
    Temperature plot
    """
    def __init__(self, parent=None):
        """
        Layout: top : Dropbox Sensor and Mode
                bottom: QwtPlot 
        """
        QtGui.QWidget.__init__(self, parent)
        
        self.console = QtGui.QPlainTextEdit(self)

        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255,255,255,255))
        brush.setStyle(Qt.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
        brush1 = QtGui.QBrush(QtGui.QColor(0,0,0,255))
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush1);
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush);
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush1);
        brush2 = QtGui.QBrush(QtGui.QColor(128,128,128,255))
        brush2.setStyle(Qt.Qt.SolidPattern);
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush2);
        brush3 = QtGui.QBrush(QtGui.QColor(247,247,247,255))
        brush3.setStyle(Qt.Qt.SolidPattern);
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush3);
        self.console.setPalette(palette)
        x = self.x()
        y = self.y()
        w = 400
        h = 800
        self.setGeometry(x, y, w, h)

    def paintEvent(self, e):
        w = self.width()
        h = self.height()
        self.console.setMaximumSize(w, h)
        self.console.setMinimumSize(w, h)        
        
        
    def newData(self, datagram):
        """
        This is a slot that will be called by the mainGUI
        """
        nonstr = struct.calcsize('H4B4H')
        txtlen = len(datagram) - nonstr
        fmt = "H4BH2B2H%ds" % txtlen
        pad, flags, tag, dp, sp, da, sax, say, cmd, cf, text = struct.unpack(fmt, datagram)
        core = sp & 0x1f
        port = sp >> 5
        str = "[%d,%d,%d:%d] %s" % (sax,say,core,port,text)        
        self.console.insertPlainText(str)

