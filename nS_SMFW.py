import time
import traceback
from serial.tools import list_ports
import queue
import serial
import re
from com_monitor import ComMonitorThread
class nS_SMFW():
	data_q = None
	error_q = None
	com_monitor = None
	port = None

	def __init__(self, parent=None):
		self.data_q = queue.Queue()
		self.error_q = queue.Queue()

	def open(self):
		self.port = list(list_ports.grep("0403:0000"))[0][0]#'/dev/ttyUSB'+str(self.ui.angleSensorPort.value())
		self.com_monitor = ComMonitorThread(self.data_q,self.error_q,self.port,9600)
		self.com_monitor.daemon = True
		self.com_monitor.start()

	def close(self):
		self.com_monitor.stop()

	def getData(self):
		prev_data = []
		while not self.data_q.empty():
			prev_data.append(self.data_q.get())
		return prev_data

	def insertToSerialFlow(function_to_decorate):
		out = None
		def wrapper(*args, **kw):
			self = args[0]
			print('Readout locked')
			self.com_monitor.lock_readout()
			try:
				#self.getData()
				out = function_to_decorate(*args, **kw)
			except serial.SerialException as e:
				self.error_q.put(e)
			self.com_monitor.release_readout()
			print('Readout released')
			return out
		return wrapper

	@insertToSerialFlow
	def setFilter(self, filterIndex):
		#try:
			self.com_monitor.serial_port.write(b"FW:"+str(filterIndex).encode('utf-8')+b"\n")
			r = self.com_monitor.read()
			print(r,'@@@')
			return r
		#except AttributeError:
			#return None


	@insertToSerialFlow
	def getNanoScatInfo(self,keys=['angle']):
		outDict = {}
		self.com_monitor.serial_port.write(b"STATE?\n")
		data = self.getData()
		#if data[-1][0].decode()
		#print(data)
		line = ''
		for i in data:
			tmp = i[0].decode()
			#if not '>' in tmp and not '<' in tmp:
			line += tmp
		line = re.sub('>.*?<', '', line)
		print(">",line)
		line = line.split('\t\r\n')
		#print(">>",line)
		if len(line)<2: return None
		else: line = line[-2]
		print(">>>",line)
		if 'angle' in keys:
			try:
				outDict['angle'] = float(line.split('A:')[-1].split('\t')[0])
				#self.updateAngle(outDict['angle'])
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

	@insertToSerialFlow
	def setStepperSpeed(self,speed):
		#speed = self.ui.stepperSpeed.value()
		self.com_monitor.serial_port.write(b"SPEED:"+str(speed).encode('utf-8')+b"\n")
		r = self.com_monitor.read()
		print(r)


if __name__ == "__main__":
	ns = nS_SMFW()
	ns.open()
	time.sleep(2)
	#ns.com_monitor.serial_port.write(b"STATE?\n")

	#r = ns.com_monitor.read()
	#print('|'*5,r)
	time.sleep(2)
	for i in range(60):
		print(ns.getNanoScatInfo())
		#print(ns.getData())
		#print("->",ns.setFilter(i),'<-')
		#time.sleep(1)
		#print(ns.setStepperSpeed(512))
		time.sleep(0.1)

	ns.close()
