import serial  #pyserial-3.0 for XP
import time
import codecs
import base64
import threading
import traceback

class SMD004():
	ser = None
	def __init__(self, parent=None):
		self.eInit()
		ser = None
	def eInit(self):
		pass
		#self.ser = serial.Serial("COM3", baudrate=19200, timeout=0.1, bytesize=serial.EIGHTBITS)
		#print(self.write_(b'\xFF\x07\x03\x01\x04\x01'))#b"FF0703010101")
		#print(self.write_(b'\xFF\x06\x02\x01\x01'))#b"FF06020101")
		#print(self.write_(b'\xFF\x03\x05\x01\x60\x00\x00\x00'))#b"FF03050132000000")
		#print(self.write_(b"\xFF\x04\x00"))
		#print(self.write_(b"\xFF\x08\x02\x01\x01"))

	def eOpenCOMPort(self,port=1):
		self.ser = serial.Serial('COM'+str(port), baudrate=19200, parity=serial.PARITY_ODD, timeout=0.05, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
		self.ser.flush()
		self.ser.flushInput()
		self.ser.flushOutput()
		r = self.write_(b"000000")
		r = self.ser.readline()
		return("Info:",r)
	def eStop(self, stepper=3):

		#self.write(b"FF010101")
		self.write(b"FF01010"+ str(stepper).encode())

	
	def eStart(self, stepper=1):	
		self.write(b"FF00010" + str(stepper).encode())

	def eSetParams(self,stepper=1,mode='ccw_step',steps=0):
		m = {'ccw_step' : b'\x01',
			 'ccw2stop' : b'\x00',
			 'cw_step'  : b'\x81',
			 'cw2stop'  : b'\x80',

		}
		s = bytearray(self.int2B(steps))#[str(i) for i in int(steps).to_bytes(2,'little')]
		
		#if len(s)<4:
		#	if len(s[0])<len(s[1]): s[0] = '0'+s[0]
		#	elif len(s[0])>len(s[1]): s[1] = '0'+s[1]
		
		self.write_(b"\xFF\x02\x04"+bytearray([stepper]) + m[mode]+s)
	def eSetTactFreq(self, stepper=1, freq=68):
		print(self.write_(b'\xFF\x03\x05'+bytearray([stepper])+(freq).to_bytes(4,'little')))

	def isConnected(self):
		try:
			self.ser.inWaiting()
			return 1
		except:
			print ("Lost connection!")
			return 0
	def eClearStep(self, stepper=3):
		print(self.write_(b'\xFF\x05\x01'+bytearray([stepper])))
	def eSetMulty(self,stepper=1, multy=1):
		print(self.write_(b'\xFF\x06\x02'+bytearray([stepper])+bytearray([multy])))
	def eWriteMarchIHoldICode(self,stepper, Im=0, Is=0):
		print(self.write_(b'\xFF\x07\x03'+bytearray([stepper])+bytearray([Im])+bytearray([Is])))
	def eSetPhaseMode(self, stepper, mode='1x'):
		#m = {'00':}
		print(self.write_(b'\xFF\x08\x02'+bytearray([stepper])+b'\x10'))
		print(self.write_(b'\xFF\x08\x02'+bytearray([stepper])+bytearray([mode])))
	def makeStepCCW(self, stepper=1, steps=0, waitUntilReady=True):
		
		#state = self.eGetState(0.02)
		#print('State', state)
		#def f():
			self.eSetParams(stepper,'ccw_step',steps)
			self.eStart(stepper)
		#if state[3] == 0:
		#	f()
		#else:
		#	threading.Timer(1, f).start()

	def makeStepCW(self, stepper=1, steps=0, waitUntilReady=True):
		#state = self.eGetState(0.02)

		#print('State', state)
		#def f():
			self.eSetParams(stepper,'cw_step',steps)
			self.eStart(stepper)
		#if state[3] == 0:
		#	f()
		#else:
		#	threading.Timer(1, f).start()
			
	def moveCCW(self, stepper=1, steps=0):
		self.eSetParams(stepper,'ccw2stop',steps)
		self.eStart(stepper)
	def moveCW(self, stepper=1, steps=0):
		self.eSetParams(stepper,'cw2stop',steps)
		self.eStart(stepper)

	def eGetState(self,delay=0.01):
		r = self.write_(b"FF0400",delay)
		#time.sleep(0.5)
		#r = self.ser.readline(12)
		return r
	def getState(self, ATrtAddr=255, motor=0):
		return [0,0,0]

	def write(self, data,sleep=0.01):
		s = data
		s = self.cSum(s)
	
		# s = s.replace('\x','')
		
		print( data, s, self.str2hex(s),type(s), '='*10)
		#s = bytes(s, 'utf-8')
		#self.ser.baudrate = 19200
		#self.ser.parity = serial.PARITY_MARK
		#self.ser.bytesize = serial.EIGHTBITS
		#self.ser.stopbits = serial.STOPBITS_ONE
		self.ser.write(s[:2])
		print(self.str2hex(s[:2]))
		
		#self.ser.baudrate = 19200
		#self.ser.parity = serial.PARITY_SPACE
		#self.ser.bytesize = serial.EIGHTBITS
		#self.ser.stopbits = serial.STOPBITS_ONE
		self.ser.write(s[2:])
		print(self.str2hex(s[2:]))
		#self.ser.read() 
		time.sleep(sleep)
		r = self.ser.readline(12)
		print(">"*10,codecs.encode(r,'hex'), r)
		return r
	def write_(self, data,sleep=0.01):
		s = data
		s = self.cSum(s,bytesA=True)
	
		# s = s.replace('\x','')
		
		print( data, s, self.str2hex(s),type(s), '='*10)
		#s = bytes(s, 'utf-8')
		#self.ser.baudrate = 19200
		self.ser.parity = serial.PARITY_MARK
		#self.ser.bytesize = serial.EIGHTBITS
		#self.ser.stopbits = serial.STOPBITS_ONE
		self.ser.write(s[:2])
		print(self.str2hex(s[:2]))
		
		#self.ser.baudrate = 19200
		#self.ser.parity = serial.PARITY_SPACE
		#self.ser.bytesize = serial.EIGHTBITS
		#self.ser.stopbits = serial.STOPBITS_ONE
		self.ser.write(s[2:-2])
		print(self.str2hex(s[2:-2]))
		self.ser.write(s[-2:])
		print(self.str2hex(s[-2:]))

		#self.ser.read() 
		time.sleep(sleep)
		r = self.ser.readline(12)
		print(">"*10,codecs.encode(r,'hex'), r)
		return r
	def int2B(self, b):
		return (b&0xff, (b&0xff00)>>8)


	def str2hex(self, InputString):
		InputString = base64.b16encode(InputString)
		return InputString#''.join('{:02x}'.format(ord(c)) for c in InputString)
	
	def cSum(self, string, bytesA=False):
		if not bytesA:
			bb = base64.b16decode(string)
		else: bb = string
		s = sum(bb[:-1])
		print(s)
		if s > 255:
			s = bytearray((s).to_bytes(2, 'little'))[1]
		string = bb + chr(s).encode('utf-8')

		return string


if __name__ == "__main__":
	e = SMD004()
	e.eOpenCOMPort('1')
	print(e.str2hex(b"Hello"))
	print(e.str2hex(b"\n\r"))
	#print(''.join('{:02x}'.format(ord(c)) for c in 'Hello'))
	
	try:
		#e.eStartLeft()
		f = lambda : e.eStop()
		import time
		#time.sleep(2)
		#e.eStop()
		e.eSetTactFreq(1,160)
		e.eClearStep(3)
		e.eSetMulty(1,1)
		#e.makeStepCCW(steps=600)
		#e.makeStepCW(steps=300)
		#e.eStartLeft()
		#time.sleep(4)
		#e.makeStepCW(steps=600)

		#e.eStartRight()
		#e.eGetState()
		#time.sleep(2)
		#e.eStop()
		#e.eGetState()
		#print('+'*10,e.isConnected())
		print('-'*50)
		e.eWriteMarchIHoldICode(1,1,0)
		e.eSetPhaseMode(1,1)
		e.moveCW(1)

		threading.Timer(5,f).start()
		time.sleep(10)
		#e.moveCW(1)
		threading.Timer(5,f).start()
		#time.sleep(5)
		e.eStop()
		#e.makeStepCW(1,50,True)
		#e.makeStepCCW(1,50,True)
	except:
		traceback.print_exc()
		e.ser.close()	
	e.ser.close()
	print(e.isConnected())

