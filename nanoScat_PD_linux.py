#!/usr/bin/python3
# _*_ coding: utf-8 _*_

#from ET1255 import *
#from smd004b import *
#from SMD_test2 import *
from HAMEG import HAMEG
import signal
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
from scipy.signal import medfilt, find_peaks_cwt
import pyqtgraph as pg
import signal
import re
from serial.tools import list_ports
import serial
import configparser
import threading
from multiprocessing import Process

import sys
from PyQt4 import uic
import time
from PyQt4.QtCore import QTimer, QThread, SIGNAL
from PyQt4.QtGui import QApplication, QMessageBox, QTableWidgetItem, QFileDialog

import subprocess
import sys, os
import threading
import time
import signal
import struct

from datetime import datetime


 



def sigint_handler(*args):
	"""Handler for the SIGINT signal."""
	sys.stderr.write('\r')
	QApplication.quit()


"""
import csv
with open('eggs.csv', 'w', newline='') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=' ',
							quotechar='|', quoting=csv.QUOTE_MINIMAL)
	spamwriter.writerow(['Spam'] * 5 + ['Baked Beans'])
	spamwriter.writerow(['Spam', 'Lovely Spam', 'Wonderful Spam'])

"""
def calc_peaks(y,width=np.arange(20,40)):
	#y=medfilt(y)
	g = find_peaks_cwt(y, width)
	l = find_peaks_cwt(-y, width)
	return g,l

def freq_calc(y_mask):
	HIGH = 0
	LOW = 0
	prev = None
	T = []
	duty_cycle = []
	start = y_mask[0]==0
	for i in y_mask:
		#print(i,HIGH,LOW)
		if prev == int(start) and i==int(not start):
			if HIGH>5 and LOW>5:
				T.append(HIGH+LOW)
				duty_cycle.append(HIGH/(HIGH+LOW))
				HIGH=0
				LOW=1
				#print(T,duty_cycle)
		elif i==0:
			LOW+=1
		elif i==1:
			HIGH+=1
		prev = i
	#print("T:",T,duty_cycle)
	T_mean = np.mean(T[1:])
	duty_cycle_mean = np.mean(duty_cycle[1:	])
	return 1/T_mean, duty_cycle_mean

def peak2peak(ref,signal,smooth_ref=3,mean_calc=np.median, ref_mode='triangle'):
	if ref_mode == 'triangle':
		y_df1 = np.insert(np.diff(medfilt(ref,smooth_ref)), 0, 0)
	else:
		d = ref.max()-ref.mean()
		y_df1 = ref-ref.mean()+d/10
	#print(y_df1,type(y_df1))
	HIGH=np.mean(signal[y_df1>0])
	LOW=np.mean(signal[y_df1<0])
	res = abs(mean_calc(HIGH)-mean_calc(LOW))
	STD = np.sqrt(np.std(signal[y_df1>0])**2 )#+ np.std(signal[y_df1<0])**2)
	f,duty_cycle = freq_calc(y_df1>0)
	#print(STD)
	return res,HIGH,LOW,STD,f,duty_cycle


class nanoScat_PD(QtGui.QMainWindow):
	ui = None
	stepperCOMPort = None
	ATrtAddr = 255
	currentAngle = 0
	prevMove = ([0, 0], [0, 0])
	line0, line1, line2, line3, line4, line5, line6, line7 = None, None, None, None, None, None, None, None
	lines = [line0, line1, line2, line3, line4, line5, line6, line7]
	steppingTimer = None
	calibrTimer = None
	measTimer = None
	stepperStateTimer = None
	FWCalibrationCounter = 0
	FWCalibrationCounterList = []

	angleSensorSerial = None
	angleUpdateTimer = None
	angleUpdateThread = None
	lastDirection = 1
	tmpData = None
	num = 10
	calibrData=np.array([])
	measData=np.array([])
	intStepCounter = 0
	moveFlag = 0
	extLaserStrob = None
	extDataBuffer = None

	oscillo = None
	oscReadTimerTimer = None
	lastFiltChTime = None
	lastDivChange = time.time()
	oscilloLastMaster = None
	oscilloLastIndex = [-1,-1]

	#et = ET1255()
	def __init__(self, parent=None):
		QtGui.QMainWindow.__init__(self, parent)
		self.ui = uic.loadUi("mainwindow.ui")
		self.ui.closeEvent = self.closeEvent
		self.steppingTimer = QtCore.QTimer()
		self.calibrTimer = QtCore.QTimer()
		self.calibrHomeTimer = QtCore.QTimer()
		self.calibrFWTimer = QtCore.QTimer()
		self.measTimer = QtCore.QTimer()
		self.angleUpdateTimer = QtCore.QTimer()

		self.stepperStateTimer = QtCore.QTimer()
		self.oscReadTimer = QtCore.QTimer()

		self.config = configparser.ConfigParser()
		self.config.read('settings.ini')
		print(sys.argv[0],self.config.sections())
		

		self.globalSettingsDict = self.config['GLOBAL']#.read('globalSettings.ini')
		self.updateSettingsTable()
		
		self.uiConnect()
		self.initUi()
		
		self.fileDialog = QFileDialog(self)

		#self.initET1255()
		self.tmpData = []#[[0,0,0]]
		self.calibrData = np.array([])#[0,0,0])
		#self.SMD = SMD004()
		#self.extLaserStrob = laserStrob(0.1)
		self.oscillo = HAMEG()
		self.oscilloLastMaster = 'HAMEG'
		
		#self.startLaserStrob(0.02)
	def updateSettingsTable(self):
		if 'GLOBAL' in self.config.sections():
			section = self.config['GLOBAL']
			self.ui.globalConfig.setVerticalHeaderLabels(list(section))
			for row,key in enumerate(section):
				print(row,key)
				for column,val in enumerate(section[key].split(',')):
					print(column,val)
					newitem = QTableWidgetItem(val)
					self.ui.globalConfig.setItem(row,column,newitem)

		if 'FILTERS' in self.config.sections():
			section = self.config['FILTERS']
			self.ui.filtersTab.setVerticalHeaderLabels(list(section))
			for row,key in enumerate(section):
				print(row,key)
				for column,val in enumerate(section[key].split(',')):
					print(column,val)
					newitem = QTableWidgetItem(val)
					self.ui.filtersTab.setItem(row,column,newitem)
		#for column, key in enumerate(section):
			#	newitem = QTableWidgetItem(item)
			#	for row, item in enumerate(self.data[key]):
			#		newitem = QTableWidgetItem(item)
			#		self.setItem(row, column, newitem)

			
	def saveConfig(self):
		if 'GLOBAL' in self.config.sections():
			section = self.config['GLOBAL']
			rows = self.ui.globalConfig.rowCount()
			columns = self.ui.globalConfig.columnCount()
			
			for row in range(rows):
				key = self.ui.globalConfig.verticalHeaderItem(row).text()
				val = []
				for column in range(columns):
					try:
						val.append(self.ui.globalConfig.item(row,column).text())
					except:
						break
				section[key] = ','.join(val)
				print(key,val)

		if 'FILTERS' in self.config.sections():
			section = self.config['FILTERS']
			rows = self.ui.filtersTab.rowCount()
			columns = self.ui.filtersTab.columnCount()
			
			for row in range(rows):
				key = self.ui.filtersTab.verticalHeaderItem(row).text()
				val = []
				for column in range(columns):
					try:
						val.append(self.ui.filtersTab.item(row,column).text())
					except:
						break
				section[key] = ','.join(val)
				print(key,val)

		with open('settings.ini', 'w') as configfile:
			self.config.write(configfile)
		'''	
			for row,key in enumerate(section):
				print(row,key)
				for column,val in enumerate(section[key].split(',')):
					print(column,val)
					newitem = QTableWidgetItem(val)
					self.ui.globalConfig.setItem(row,column,newitem)

		if 'FILTERS' in self.config.sections():
			section = self.config['FILTERS']
			self.ui.globalConfig.setVerticalHeaderLabels(list(section))
			for row,key in enumerate(section):
				print(row,key)
				newitem = QTableWidgetItem(key)
				self.ui.filtersTab.setItem(row,0,newitem)
				for column,val in enumerate(section[key].split(',')):
					print(column,val)
					newitem = QTableWidgetItem(val)
					self.ui.filtersTab.setItem(row,column+1,newitem)
		'''

	def initUi(self):
		self.pw = pg.PlotWidget(name='Plot1')  ## giving the plots names allows us to link their axes together
		self.ui.l.addWidget(self.pw)
		self.pw2 = pg.PlotWidget(name='Plot2')
		self.ui.l.addWidget(self.pw2)
		self.osc_pw = pg.PlotWidget(name='Plot3')
		self.ui.oscilloPlot.addWidget(self.osc_pw)
		#self.osc_pw.setXRange(0, 360)
		#self.osc_pw.showAxis('bottom', False)
		self.osc_pw.showGrid(x=True, y=True)
		self.pw.showGrid(x=True, y=True)
		self.pw2.showGrid(x=True, y=True)
		
		#self.osc_pw.showAxis('bottom', False)
		self.osc_pw.setYRange(0, 256)
		self.ui.show()


		## Create an empty plot curve to be filled later, set its pen
		colors = ['red', "green", 'blue', 'cyan', 'magenta', 'yellow', 'purple', 'olive']
		#for i in range(0,self.ui.channelsSettings.rowCount()):
		#   self.lines[i] = self.pw.plot()
		#   self.lines[i].setPen(QtGui.QColor(colors[i]))
		self.line0 = self.pw2.plot()
		print(self.line0)
		self.line0.setPen(QtGui.QColor('cyan'))
		self.line1 = self.pw.plot()
		self.line1.setPen(QtGui.QColor("orange"))
		self.line2 = self.osc_pw.plot()
		self.line2.setPen(QtGui.QColor("orange"))
		self.line3 = self.osc_pw.plot()
		self.line3.setPen(QtGui.QColor("cyan"))

		self.pw.setLabel('left', 'Signal', units='arb. un.')
		self.pw.setLabel('bottom', 'Angle', units='deg.')
		self.pw.setXRange(0, 360)
		self.pw.setYRange(0, 1e10)
		self.pw2.setMaximumHeight(300)

	def setStepperParam(self):
		pass

	def getCorrectedAngle(self):
		angle = self.ui.steppingAngle.value()
		#calibr = float(self.config['STEPPER1']['calibrationCoefficient']) #self.ui.steppingCalibr.value()
		#tmp_angle = int(angle*calibr)/calibr
		#self.ui.steppingAngle.setValue(tmp_angle)
		#return int(tmp_angle*calibr), tmp_angle
		return angle, angle

	def steps2angle(self, steps, motor=1):
		calibr = float(self.config['STEPPER'+str(motor)]['calibrationCoefficient']) #self.ui.steppingCalibr.value()
		return steps/calibr

	def prepInternCounter(self, direction):
		if direction != self.lastDirection:
			#self.SMD.eClearSteps()#SMD_ClearStep(self.ATrtAddr)
			self.lastDirection = direction

	def CCWSingleMove(self):
		steps, angle = self.getCorrectedAngle()
		self.angleSensorSerial.write(b"CCW:"+str(steps).encode('utf-8')+b"\n")
		r = self.angleSensorSerial.readline()   
		print(r)



	def CWSingleMove(self):
		steps, angle = self.getCorrectedAngle()
		self.angleSensorSerial.write(b"CW:"+str(steps).encode('utf-8')+b"\n")
		r = self.angleSensorSerial.readline()   
		print(r)
	
	def CCWMoveToStop(self):
		print("CCWMoveToStop")
		self.angleSensorSerial.write(b"CCW\n")
		r = self.angleSensorSerial.readline()
		print(r)
		
		
	def CWMoveToStop(self):
		print("CWMoveToStop")
		self.angleSensorSerial.write(b"CW\n")
		r = self.angleSensorSerial.readline()
		print(r)
		

	def CCWHome(self):
		print("CCWHome")
		self.angleSensorSerial.write(b"HOME:CCW\n")
		r = self.angleSensorSerial.readline()
		print(r)
		

	def CWHome(self):
		print("CWHome")
		self.angleSensorSerial.write(b"HOME:CW\n")
		r = self.angleSensorSerial.readline()
		print(r)

	def onCalibrHomeTimer(self):
		info = self.getNanoScatInfo(['zero','angle'])
		if info['zero'] == 1:
			print("Zero at:", info['angle'])
			self.stepperStop()
			self.updateAngle(0)
			self.setNanoScatState(angle=0)
			self.currentAngle = 0
			self.calibrHomeTimer.stop()
		else:
			print("angle:", info['angle'])
		

	def getCurrentFilter(self):
		row = self.ui.filtersTab.currentRow()
		try:
			name = self.ui.filtersTab.item(row,0).text()
		except:
			name = 'none'
		try:
			val = self.ui.filtersTab.item(row,1).text()
		except:
			val = 'none'
		#   return (None, None)
		return name, val, row



	def prevFilter(self):
		row = self.ui.filtersTab.currentRow()
		if row>0:
			print(b"FW:"+str(row-1).encode('utf-8')+b"\n")
			self.angleSensorSerial.write(b"FW:"+str(row-1).encode('utf-8')+b"\n")
			r = self.angleSensorSerial.readline()   
			print(r)
			self.ui.filtersTab.setCurrentCell(row-1,0)
			self.lastFiltChTime = datetime.now()
			#self.ui.oscilloVdiv2.setCurrentIndex(10)
			#self.oscillo.vdiv2(10)
			#ch2_v = self.oscillo.get_vdiv2()
			#print(ch2_v)
			return 1
		else:
			return 0

	def nextFilter(self):
		row = self.ui.filtersTab.currentRow()
		if row<5:
			print(b"FW:"+str(row+1).encode('utf-8')+b"\n")
			self.angleSensorSerial.write(b"FW:"+str(row+1).encode('utf-8')+b"\n")
			r = self.angleSensorSerial.readline()   
			print(r)
			self.lastFiltChTime = datetime.now()
			#self.ui.oscilloVdiv2.setCurrentIndex(3)
			#self.oscillo.vdiv2(3)
			#ch2_v = self.oscillo.get_vdiv2()
			#print(ch2_v)
			return 1
		else:
			return 0

		

	def stepperStop(self):
		self.angleSensorSerial.write(b"SM:STOP\n")
		r = self.angleSensorSerial.readline()   
		print(r)

	def stepperLock(self,state):
		if state:
			self.angleSensorSerial.write(b"SM:OFF\n")
		else:
			self.angleSensorSerial.write(b"SM:ON\n")
		r = self.angleSensorSerial.readline()   
		print(r)

	def setStepperSpeed(self):
		speed = self.ui.stepperSpeed.value()
		self.angleSensorSerial.write(b"SPEED:"+str(speed).encode('utf-8')+b"\n")
		r = self.angleSensorSerial.readline()   
		print(r)

	def updateAngle(self, new_angle=0, mode='None'):
		if self.sender().objectName() == "resetAngle": mode = "reset"
		if mode == "reset":
			self.currentAngle = 0
		elif mode == "set":
			self.currentAngle = new_angle  # in deg
			val = new_angle / float(self.config['GLOBAL']['anglecalibr'])
			self.angleSensorSerial.write(b"ANGLE:"+str(val).encode('utf-8')+b"\n")
			r = self.angleSensorSerial.readline()   
			print(r)
		else:
			try:
				self.currentAngle = new_angle*float(self.config['GLOBAL']['anglecalibr'])
			except:
				pass
		self.ui.currentAngle.setText(str(self.currentAngle))
		return self.currentAngle

	def setCustomAngle(self):
		dlg =  QtGui.QInputDialog(self)
		dlg.setInputMode( QtGui.QInputDialog.DoubleInput)
		dlg.setLabelText("Angle:")
		dlg.setDoubleDecimals(6)
		dlg.setDoubleRange(-999999,999999)
		ok = dlg.exec_()
		angle = dlg.doubleValue()
		if ok:
			self.updateAngle(angle, mode='set')
	def moveToAngle(self):
		dlg =  QtGui.QInputDialog(self)
		dlg.setInputMode( QtGui.QInputDialog.DoubleInput)
		dlg.setLabelText("Angle:")
		dlg.setDoubleDecimals(6)
		dlg.setDoubleRange(-999999,999999)
		ok = dlg.exec_()
		angle = dlg.doubleValue()
		if ok:
			if angle>self.currentAngle:
				pass



	def startMeasurement(self, state):
		if state:
			if self.isStepperConnected():
				self.steppingTimer.start()
				self.ui.startMeasurement.setText("Stop")
				self.getCurrentFilter(self)

			else:
				self.ui.startMeasurement.setChecked(False)
				self.ui.startMeasurement.setText("Start")
		else:
			self.steppingTimer.stop()
			self.ui.startMeasurement.setText("Start")
			self.num = 0
			self.calibrData = []


	def stepperOn(self):
		pass

	def getStepperState(self):
		state = [ i.value for i in getState(self.ATrtAddr, 1)]
		#if sum(state) == 0:
		#   state [0] = 1
		return state

	

	def startCalibr(self, state):
		if state:
			self.calibrTimer.start(self.ui.plotPeriod.value())
			
			direction = 1 if self.ui.measurementDirCW.isEnabled() else -1
			self.line0.setData(x=[],y=[])
			self.line1.setData(x=[],y=[])
			self.line2.setData(x=[],y=[])
			self.line3.setData(x=[],y=[])
			
		else:


			self.calibrTimer.stop()
			self.calibrData=np.array([])

			
	def onCalibrTimer(self):
		r=[]
		#chanels=[0,1,2]
		#####################################################################################
		#r=et.getDataProcN(2,100,chanels,True)
		name,tmp_filt,index = self.getCurrentFilter()
		print('Filter:',name,tmp_filt,index)
		r = self.oscilloGetData()
		y0 = r[1]
		y1 = r[0]/float(tmp_filt)
		


		if len(self.calibrData)>0:
			
			self.calibrData = np.vstack((self.calibrData,[y0,y1]))
		else:
			self.calibrData = np.array([y0,y1])
		data = self.calibrData

		
		self.line0.setData(x=np.arange(len(data)), y=data[:,0])
		self.line1.setData(x=np.arange(len(data)), y=data[:,1])
		self.updateAngle(len(data))
		app.processEvents()  

	def startContMeas(self, state):
		if state:
			self.angleUpdateTimer.stop()

			with open(self.ui.saveToPath.text(), 'a') as f:
				f.write("\n#$Filter:"+self.getCurrentFilter()[0]+"\n")
				for row in range(6):
					name = self.ui.filtersTab.item(row,0).text()
					val = self.ui.filtersTab.item(row,1).text()
					f.write("#$\t"+str(row)+"\t"+name+"\t"+val+'\n')
				f.write("#$POWER:"+self.config['GLOBAL']['power'].replace('\n','\t')+'\n')
				f.write("#$WAVELENGTH:"+self.config['GLOBAL']['wavelength'].replace('\n','\t')+'\n')
				f.write("#$OBJECT:"+self.config['GLOBAL']['object'].replace('\n','\t')+'\n')

				f.write("angle\tref\tsignal\tsignal_std\tfilter\tTime\tfreq\tduty_cycle\n")
			
			self.measTimer.start(self.ui.plotPeriod.value())
			
			direction = 1 if self.ui.measurementDirCW.isEnabled() else -1
			if direction == 1:
				self.CWMoveToStop()
			else:
				self.CCWMoveToStop()

			self.line0.setData(x=[],y=[])
			self.line1.setData(x=[],y=[])
			
		else:

			self.stepperStop()
			#et.ET_stopStrobData()
			#try:
			
			#   self.SMD.eStop()
			#except:
			#   print('Err')
			self.measTimer.stop()
			#self.openAngleSensorPort(True)
			self.angleUpdateTimer.start()
			self.calibrData=np.array([])
			#data = np.loadtxt(self.ui.saveToPath.text(),comments='#')
			#self.line2.setData(x=data[:,4], y=data[:,1])
			#self.line3.setData(x=data[:,-1], y=data[:,2])
			
			
	def onContMeasTimer(self):
		r=[]
		#chanels=[0,1,2]
		############################################################################
		r = self.oscilloGetData()
		y0 = r[1]
		y1 = r[0]
		y1_std = r[2]

		name,tmp_filt,index = self.getCurrentFilter()
		print('Filter:',name,float(tmp_filt),index)
		info = self.getNanoScatInfo(['angle', 'FW'])
		angle = float(self.ui.currentAngle.text())#info['angle']
		filt = info['FW']
		freq = float(self.ui.oscilloFreq.text())
		duty_cycle = float(self.ui.duty_cycle.text())
		#try:
			#self.currentAngle = angle#et.getAngle()
		#except:
		#   pass
		print("angle", angle)
		#self.ui.currentAngle.setText(str(self.currentAngle))

		x = angle
		

		with open(self.ui.saveToPath.text(), 'a') as f:
				f.write(str(x)+"\t"+str(y0)+"\t"+str(y1) + "\t"+ str(y1_std)+'\t' + str(filt)+"\t"+str(time.time())+"\t"+str(freq)+"\t"+str(duty_cycle) +"\n")

		#print(self.measData)
		if len(self.measData)>0:
			
			self.measData = np.vstack((self.measData,[x,y0,y1/float(tmp_filt)]))
		else:
			self.measData = np.array([x,y0,y1/float(tmp_filt)])
		data = self.measData
		#print(data)

		
		self.line0.setData(x=data[:,0], y=data[:,1])
		self.line1.setData(x=data[:,0], y=data[:,2])
		#self.updateAngle(x)
		app.processEvents()  

	def saveToBtn(self):
		filename = self.fileDialog.getSaveFileName(self)
		print(filename)
		self.ui.saveToPath.setText(filename)


	def openAngleSensorPort(self,state):
		if state:
			'''
			portNumber = self.ui.angleSensorPort.value()
			dev = serial.tools.list_ports.comports()
			print(dev)
			dev_list = []
			for d in dev:
				dev_list.append(d)
				
				try:
					com, info = dev_list[-1][0], dev_list[-1][2]
					m = re.search('1A86:7523',info)
					print(m,info)
					if m.group(0) == '1A86:7523':
						print(info,com)
						portNumber = int(com[3:])
						self.ui.angleSensorPort.setValue(portNumber)
				except: pass
			'''
			
			print(">>>>>>open")
			#et.openSerialPort('COM'+str(self.ui.angleSensorPort.value()))
			#self.angleSensorSerial = serial.Serial('COM'+str(self.ui.angleSensorPort.value()), baudrate=19200, dsrdtr=False)
			#self.angleSensorSerial = serial.Serial()
			port = '/dev/ttyUSB'+str(self.ui.angleSensorPort.value())
			self.angleSensorSerial = serial.Serial(port,baudrate=9600,timeout=5)#.port = port
			print(port)
			time.sleep(1)
			#self.angleSensorSerial.port = port
			#self.angleSensorSerial.baudrate = 19200
			#self.angleSensorSerial.timeout = 4
			#self.angleSensorSerial.open()
			#self.angleSensorSerial.setDTR(True)
			#self.angleSensorSerial.write(b'')
			#self.angleSensorSerial.flush()
			#self.angleSensorSerial.flushInput()
			#self.angleSensorSerial.flushOutput()
			a=self.angleSensorSerial.read(5)
			print("0>>",a)
			self.angleSensorSerial.write(b"STATE?\n")
			a=self.angleSensorSerial.readline()
			print("1>>",a)
			#self.angleSensorSerial.write(b'1')
			#self.setNanoScatState(frecMode=[20,20])
			#self.setNanoScatState(angleCalibrCoef=0.49)
			self.angleUpdateTimer.start(1000)
			#self.angleSensorSerial.write(b'2')
			

		else:
			self.angleUpdateTimer.stop()
			#self.angleSensorSerial.write(b'RM')
			self.angleSensorSerial.close()

	
	def getNanoScatInfo(self,keys=['angle']):
		if not self.angleSensorSerial.isOpen():
			self.openAngleSensorPort(True)
			return None
		else:
			outDict = {}
			self.angleSensorSerial.flush()
			self.angleSensorSerial.flushInput()
			self.angleSensorSerial.flushOutput()
			self.angleSensorSerial.write(b"STATE?\n")
			line = self.angleSensorSerial.readline().decode("utf-8")
			print(">>",line)
			if 'angle' in keys:
				try:
					outDict['angle'] = float(line.split('A:')[-1].split('\t')[0])
					self.updateAngle(outDict['angle'])
				except ValueError:
					outDict['angle'] = None
			if 'zero' in keys:
				try:
					outDict['zero'] = int(line.split('Z:')[-1].split('\t')[0])
				except ValueError:
					outDict['zero'] = None
			if 'FW' in keys:
				try:
					outDict['FW'] = int(line.split('FW:')[-1].split('\t')[0])
				except ValueError:
					outDict['FW'] = None

			if 'freqMode' in keys:
				try:
					outDict['freqMode'] = [float(i) for i in (line.split('\tFM:')[-1].split('\t')[0]).split('x')]
				except ValueError:
					outDict['freqMode'] = [None, None]
			return outDict

	def setNanoScatState(self,angle=None, frecMode=[None, None], angleCalibrCoef=None):
		if not self.angleSensorSerial.isOpen():
			self.openAngleSensorPort(True)
			return None
		else:
			res = None
			if not angle is None:
				res = self.angleSensorSerial.write(b'A'+str(angle).encode())
			if not angleCalibrCoef is None:
				res = self.angleSensorSerial.write(b'CC'+str(angleCalibrCoef).encode())

			if sum([i is None for i in frecMode]) != 2:
				res = self.angleSensorSerial.write(b'FM'+str(frecMode[0]).encode()+b'x'+str(frecMode[1]).encode())
			print(res)
			return 1

		

	def onAngleUpdateTimer(self):
		
		info = self.getNanoScatInfo(['angle','FW'])
		angle = info['angle']
		filt = info['FW'] 
		try:
			#self.currentAngle = angle#et.getAngle()
			self.ui.filtersTab.setCurrentCell(filt,0)
		except:
			pass
		print("angle", angle)
		self.updateAngle(angle)
		#self.ui.currentAngle.setText(str(self.currentAngle))

	def checkStepperState(self):
		pass
	#def setADCAmplif(self, value):
		#et.ET_SetAmplif(value)

	def cleanPlot(self):
		self.calibrData=np.array([])
		self.measData=np.array([])
		self.line0.setData(x=[], y=[])
		self.line1.setData(x=[], y=[])

	def setStrobMode(self, mode):
		#m = et.setStrobMode(mode)
		print('strobMode:%d'%(m))

	def setLaserFreq(self, value):
		print('SetLaserFreq:')
		#if not self.angleSensorSerial.inWaiting():
		
		#   self.angleSensorSerial = serial.Serial()
		#   self.angleSensorSerial.port = 'COM'+str(self.ui.angleSensorPort.value())
		#   self.angleSensorSerial.baudrate = 19200
		#   self.angleSensorSerial.timeout = 1
		#   self.angleSensorSerial.setDTR(False)
		#   self.angleSensorSerial.open()
		self.angleSensorSerial.write(b'f'+str(value).encode('ascii')+b'\n')

	def closeEvent(self, event):
		print("event")
		reply = QtGui.QMessageBox.question(self, 'Message',
			"Are you sure to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

		if reply == QtGui.QMessageBox.Yes:
			self.angleSensorSerial.close()
			self.oscillo.disconnect()
			self.oscillo.close()
			event.accept()
			#self.stopLaserStrob()
			#self.stopDataBuffering()
		else:
			event.ignore()

	def oscilloConnect(self, state):
		if state:
			self.oscillo.connect()
			r = self.oscillo.init()
			print(r)
			r = self.oscillo.vers()
			print(r)
			ch1_v = self.oscillo.get_vdiv1()
			print(ch1_v)
			self.ui.oscilloVdiv1.setCurrentIndex(ch1_v)
			yp1 = self.oscillo.get_ypos1()
			print(yp1)
			self.ui.oscilloYpos1.setValue(yp1)
			
			ch2_v = self.oscillo.get_vdiv2()
			print(ch2_v)
			self.ui.oscilloVdiv2.setCurrentIndex(ch2_v)
			yp2 = self.oscillo.get_ypos2()
			self.oscilloLastIndex = [ch1_v, ch2_v]
			print(yp2)
			self.ui.oscilloYpos2.setValue(yp2)

			td = self.oscillo.get_tdiv()
			print(td)
			self.ui.oscilloTdiv.setCurrentIndex(td)
			
			self.oscReadTimer.start(1000)

		else:
			self.oscReadTimer.stop()
			self.oscillo.disconnect()
			self.oscillo.close()

	def oscilloGetData(self):
		div = ( 0.001,0.002,0.005,
				0.01, 0.02, 0.05,
				0.1,  0.2,  0.5,
				1,    2,    5,
				10,   20)
		div_t = self.ui.oscilloTdiv.currentText()
		print(div_t)
		tdiv_val, t_order = div_t.split(' ')
		
		scales={'ns':1e-9,'mks':1e-3,'ms':1e-3,'s':1}
		tdiv_val = float(tdiv_val)*scales[t_order]

		res1 = self.oscillo.rdwf1()
		sig = np.array([int(i) for i in res1[50:]])
		self.line2.setData(x=np.arange(len(sig)),y=sig)
		index1 = self.ui.oscilloVdiv1.currentIndex()
		

		res2 = self.oscillo.rdwf2()
		ref = np.array([int(i) for i in res2[50:]])
		self.line3.setData(x=np.arange(len(ref)),y=ref)
		index2 = self.ui.oscilloVdiv2.currentIndex()
		
		
		Vpp1,HIGH,LOW,STD,f,duty_cycle = peak2peak(ref,sig,ref_mode='triangle')
		
		frequency = 1/(0.1/2048*10/f)
		self.ui.oscilloFreq.setText(str(frequency))
		self.ui.duty_cycle.setText(str(duty_cycle))
		
		val1 = self.oscillo.dig2Volts(Vpp1, div[index1])#(Vpp1)/256*(div[index1]*8)*1.333333
		STD1 = self.oscillo.dig2Volts(STD, div[index1])#(STD)/256*(div[index1]*8)*1.333333 
		self.ui.CH1Val.setText(str(val1))
		self.ui.CH1Val_std.setText(str(STD1))


		ref = medfilt(ref,5)
		Vpp2 = ref.max()-ref.min()
		print("Vpp1:",Vpp1,"Vpp2:",Vpp2)
		val2 = self.oscillo.dig2Volts(Vpp2, div[index2])#(Vpp2)/256*(div[index2]*8)*1.333333
		self.ui.CH2Val.setText(str(val2))

		if self.ui.oscilloAuto.isChecked() and (time.time()-self.lastDivChange)>1 :
			self.lastDivChange = time.time()
			if sig.min()<20:
				index1 = self.ui.oscilloVdiv1.currentIndex()
				if self.oscilloLastMaster == 'HAMEG':
					#if self.oscilloLastIndex[0] == index1+1:
					#   self.oscilloLastMaster = 'FM' 
					if index1<12:
						self.oscilloLastIndex[0] = index1
						self.oscillo.vdiv1(index1+1)
						self.ui.oscilloVdiv1.setCurrentIndex(index1+1)
						#self.oscilloAutoSet()
						#self.oscillo.tdiv(17)
						#self.ui.oscilloTdiv.setCurrentIndex(17)
					#else:
					#   self.oscilloLastMaster = 'FM'
				else:

					#self.nextFilter()
					#self.oscilloAutoSet()
					#self.oscillo.tdiv(17)
					#self.ui.oscilloTdiv.setCurrentIndex(17)
					self.oscilloLastIndex == 'HAMEG'

			elif sig.max()>230:
				index1 = self.ui.oscilloVdiv1.currentIndex()
				if self.oscilloLastMaster == 'HAMEG':
					#if self.oscilloLastIndex[0] == index1+1:
					#   self.oscilloLastMaster = 'FM' 
					if index1>1:
						self.oscilloLastIndex[0] = index1
						self.oscillo.vdiv1(index1-1)
						self.ui.oscilloVdiv1.setCurrentIndex(index1-1)
						
						#self.oscilloAutoSet()
						#self.oscillo.tdiv(17)
						#self.ui.oscilloTdiv.setCurrentIndex(17)
					#else:
					#   self.oscilloLastMaster = 'FM'
				else:

					#self.nextFilter()
					#self.oscilloAutoSet()
					#self.oscillo.tdiv(17)
					#self.ui.oscilloTdiv.setCurrentIndex(17)
					self.oscilloLastIndex == 'HAMEG'

			elif abs(Vpp1) < 20:
				index1 = self.ui.oscilloVdiv1.currentIndex()
				if self.oscilloLastMaster == 'HAMEG':
					#if self.oscilloLastIndex[0] == index1-1:
					#   self.oscilloLastMaster = 'FM'
					if index1>1:
						self.oscilloLastIndex[0] = index1
						self.ui.oscilloVdiv1.setCurrentIndex(index1-1)
						self.oscillo.vdiv1(index1-1)
						#self.oscilloAutoSet()
						#self.oscillo.tdiv(17)
						#self.ui.oscilloTdiv.setCurrentIndex(17)
					#else:
					#   self.oscilloLastMaster = 'FM'
				else:
					#self.prevFilter()
					#self.oscilloAutoSet()
					#self.oscillo.tdiv(17)
					#self.ui.oscilloTdiv.setCurrentIndex(17)
					self.oscilloLastIndex == 'HAMEG'
			
			
			print(Vpp1, self.oscilloLastMaster)
		return [val1,val2,STD1]
	

	def onOscReadTimer(self):
		res = self.oscilloGetData()
		print(res)

	def oscilloAutoSet(self):
		r = self.oscillo.autoset()
		print(r)
		ch1_v = self.oscillo.get_vdiv1()
		print(ch1_v)
		self.ui.oscilloVdiv1.setCurrentIndex(ch1_v)
		yp1 = self.oscillo.get_ypos1()
		print(yp1)
		self.ui.oscilloYpos1.setValue(yp1)
		
		ch2_v = self.oscillo.get_vdiv2()
		print(ch2_v)
		self.ui.oscilloVdiv2.setCurrentIndex(ch2_v)
		yp2 = self.oscillo.get_ypos2()
		print(yp2)
		self.ui.oscilloYpos2.setValue(yp2)

		td = self.oscillo.get_tdiv()
		print(td)
		self.ui.oscilloTdiv.setCurrentIndex(td)

	def oscilloSet(self):
		v1 = self.ui.oscilloVdiv1.currentIndex()
		r = self.oscillo.vdiv1(v1)
		print(r)
		v2 = self.ui.oscilloVdiv2.currentIndex()
		r = self.oscillo.vdiv2(v2)
		print(r)

		td = self.ui.oscilloTdiv.currentIndex()
		r = self.oscillo.tdiv(td)
		print(r)

		y1 = self.ui.oscilloYpos1.value()
		r = self.oscillo.ypos1(y1)
		print(r)

		y2 = self.ui.oscilloYpos2.value()
		r = self.oscillo.ypos2(y2)
		print(r)


	def uiConnect(self):
		#self.ui.btnExit.clicked.connect(self.closeAll)
		#self.ui.actionExit.triggered.connect(self.closeAll)
		self.ui.measurementDirCW.clicked.connect(lambda state: (self.ui.measurementDirCCW.setChecked(False), self.ui.measurementDirCW.setEnabled(False),self.ui.measurementDirCCW.setEnabled(True)))
		self.ui.measurementDirCCW.clicked.connect(lambda state: (self.ui.measurementDirCW.setChecked(False), self.ui.measurementDirCCW.setEnabled(False),self.ui.measurementDirCW.setEnabled(True)))

		self.ui.startCalibr.toggled[bool].connect(self.startCalibr)
		self.ui.startMeasurement.toggled[bool].connect(self.startContMeas)

		self.ui.oscilloConnect.toggled[bool].connect(self.oscilloConnect)
		self.ui.oscilloAutoSet.clicked.connect(self.oscilloAutoSet)
		self.ui.oscilloSet.clicked.connect(self.oscilloSet)
		#self.ui.ADCAmplif.valueChanged[int].connect(self.setADCAmplif)
		#self.ui.laserFreq.valueChanged[int].connect(self.setLaserFreq)
		
		#self.ui.pauseMeasurements.toggled[bool].connect(self.pauseMeasurements)
		#self.ui.openCOMPort_btn.toggled[bool].connect(self.Open_CloseStepperCOMPort)
		self.ui.openAngleSensorPort.toggled[bool].connect(self.openAngleSensorPort)
		self.ui.setCustomAngle.clicked.connect(self.setCustomAngle)
		self.ui.moveToAngle.clicked.connect(self.moveToAngle)
		
		#self.ui.editStepperSettings.clicked.connect(self.setStepperParam)
		#self.ui.CCWSingleMove.clicked.connect(self.CCWSingleMove)
		#self.ui.CWSingleMove.clicked.connect(self.CWSingleMove)
		self.ui.strobMode.toggled[bool].connect(self.setStrobMode)
		self.ui.cleanPlot.clicked.connect(self.cleanPlot)

		self.ui.CCWMoveToStop.clicked.connect(self.CCWMoveToStop)
		self.ui.CWMoveToStop.clicked.connect(self.CWMoveToStop)
		self.ui.CCWHome.clicked.connect(self.CCWHome)
		self.ui.CWHome.clicked.connect(self.CWHome)
		self.ui.setStepperSpeed.clicked.connect(self.setStepperSpeed)
		self.ui.stepperSpeed.valueChanged[int].connect(self.ui.stepperSpeedValue.setValue)
		self.ui.stepperSpeedValue.valueChanged[int].connect(self.ui.stepperSpeed.setValue)

		self.ui.nextFilter.clicked.connect(self.nextFilter)
		self.ui.prevFilter.clicked.connect(self.prevFilter)

		self.ui.stepperStop.clicked.connect(self.stepperStop)
		self.ui.stepperLock.toggled[bool].connect(self.stepperLock)

		self.ui.saveToBtn.clicked.connect(self.saveToBtn)
		#self.ui.resetAngle.clicked.connect(self.updateAngle)
		#self.ui.setCustomAngle.toggled[bool].connect(self.setCustomAngle)

		#self.ui.calibrFW.clicked.connect(self.calibrFW)

		#self.ui.startMeasurement.clicked.connect(self.startMeasurement)

		#self.steppingTimer.timeout.connect(self.stepMeasurement)
		self.calibrTimer.timeout.connect(self.onCalibrTimer)
		self.measTimer.timeout.connect(self.onContMeasTimer)
		self.angleUpdateTimer.timeout.connect(self.onAngleUpdateTimer)
		self.calibrHomeTimer.timeout.connect(self.onCalibrHomeTimer)
		self.oscReadTimer.timeout.connect(self.onOscReadTimer)
		#self.calibrFWTimer.timeout.connect(self.onCalibrFWTimer)
		#self.stepperStateTimer.timeout.connect(self.checkStepperState)
		#self.laserStrobTimer.timeout.connect(self.laserStrob)

		self.ui.saveConfig.clicked.connect(self.saveConfig)

		self.ui.actionClose.triggered.connect(self.close)
		#self.ui.actionExit.triggered.connect(self.close)



if __name__ == "__main__":
	signal.signal(signal.SIGINT, sigint_handler)
	app = QtGui.QApplication(sys.argv)
	myWindow = nanoScat_PD(None)
	app.exec_()
	#SMD_CloseComPort()
	print(":)")
	sys.exit(1)
