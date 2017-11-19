# -*- coding: utf-8 -*-
"""
This example demonstrates many of the 2D plotting capabilities
in pyqtgraph. All of the plots may be panned/scaled by dragging with 
the left/right mouse buttons. Right click on any plot to show a context menu.
"""

#import initExample ## Add path to library (just for examples; you do not need this)


from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg

#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
#mw = QtGui.QMainWindow()
#mw.resize(800,800)

win = pg.GraphicsWindow(title="Basic plotting examples")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph example: Plotting')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)






data2 = np.loadtxt('ref_PD_signal_PICO_20mV_500mks')
x2 = np.arange(len(data2))
p8 = win.addPlot(title="Region Selection")
p8.plot(data2, pen=(255,255,255,200))
w = x2[data2>data2.max()/2]
lr = pg.LinearRegionItem([w.min()-100,w.max()+100])
lr.setZValue(-10)
p8.addItem(lr)

p9 = win.addPlot(title="Zoom on selected region")
p9.plot(data2)

dx=(500e-6*10)/2048
def updatePlot():
    p9.setXRange(*lr.getRegion(), padding=0)
def updateRegion():
    lr.setRegion(p9.getViewBox().viewRange()[0])
    b = data2[int(lr.getRegion()[0]):int(lr.getRegion()[1])]
    integr=np.trapz(b-np.median(data2),dx=dx)
    print(integr,np.median(data2))
lr.sigRegionChanged.connect(updatePlot)
p9.sigXRangeChanged.connect(updateRegion)
updatePlot()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
