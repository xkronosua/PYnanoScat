import time
import serial

# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
	#port='COM1',
	port='/dev/ttyS0',
	baudrate=19200,
	parity='N',
	stopbits=serial.STOPBITS_TWO,
	bytesize=8,
	timeout=3
)

#ser.open()
#ser.isOpen()
eol_1310=b"\r"
eol_3213=b" \r"
#print ('Enter your commands below.\r\nInsert "exit" to leave the application.')
ser.flush()

def vers(ser):
	r = ser.write(bytearray([32, 13]))
	#ser.write("VERS?\r".encode('ASCII'))
	#r = ser.read(3)
	r = ser.readline()
	return r

def autoset(ser):
	print("AUTOSET")
	ser.write("AUTOSET".encode('ASCII')+bytearray([13, 10]))
	r = ser.read(3)
	return r



def ypos1(ser, yp1):
	"""[0 30]"""
	print("Y1POS=")
	cyp1 = 0
	if yp1>15:
		cyp1 = yp1-15
	if yp1<=15:
		cyp1 = yp1+240
	c = [160, cyp1, 13]
	ser.write("Y1POS=".encode('ASCII')+bytearray(c))
	r = ser.read(3)
	return r

def ypos2(ser, yp2):
	"""[0 30]"""
	print("Y2POS=")
	cyp2 = 0
	if yp2>15:
		cyp2 = yp2-15
	if yp2<=15:
		cyp2 = yp2+240
	c = [160, cyp2, 13]
	ser.write("Y2POS=".encode('ASCII')+bytearray(c))
	r = ser.read(3)
	return r


def vdiv1(ser,vold1):
	"""[0 13]"""
	vold1 += 16 
	"""[16 28]"""
	print("CH1=")
	f = [round(vold1), 13]
	ser.write("CH1=".encode('ASCII')+bytearray(f))
	r = ser.read(3)
	return r

def vdiv2(ser,vold2):
	"""[0 13]"""
	vold2 += 16 
	"""[16 28]"""
	print("CH2=")
	f = [round(vold2), 13]
	ser.write("CH2=".encode('ASCII')+bytearray(f))
	r = ser.read(3)
	return r



def tdiv(ser,timed):
	"""[0 13]"""
	timed += 16 
	"""[16 28]"""
	print("TBA=")
	h = [round(timed), 13]
	ser.write("TBA=".encode('ASCII')+bytearray(h))
	r = ser.read(3)
	return r

def wtwf1(ser):
	print("RDWF1=")
	i=bytearray([88,13])
	ser.write("STRMODE=".encode('ASCII')+i)
	i1 = ser.read(3)
	j = bytearray([0,4,0,1]+list(range(256))+[13])
	print(j)
	ser.write("WRREF1=".encode('ASCII')+j)
	r = ser.read(3)

	return r

#r = wtwf1(ser)
#print(r)



def rdwf1(ser):
	print("RDWF1=")
	i=bytearray([16,13])
	#ser.write("STRMODE=".encode('ASCII')+i)
	#i1 = ser.read(3)
	j = bytearray([0,0,0,1,13])
	#j = b"\x00\x00\x00\x08"
	ser.write("RDWFM1=".encode('ASCII')+j)
	j1 = ser.read(267)
	#l=0
	#v = j1[12:267]
	return j1


def rdwf2(ser):
	print("RDWF2=")
	i=bytearray([16,13])	
	#ser.write("STRMODE=".encode('ASCII')+i)
	#i1 = ser.read(3)
	j = bytearray([0,0,0,1,13])
	#j = b"\x00\x00\x00\x08"
	ser.write("RDWFM2=".encode('ASCII')+j)
	j1 = ser.read(267)
	#l=0
	#v = j1[12:267]
	return j1

def trgval(ser):
	ser.write("TRGVAL?\r".encode('ASCII'))
	r = ser.read(15)
	return r



def discon(ser):
	ser.write("RM0".encode('ASCII')+bytearray([13,10]))
	r = ser.read(3)
	return r


def get_vdiv1(ser):
	print("CH1?")
	ser.write("CH1?".encode('ASCII')+bytearray([13,10]))
	#s = b""
	#while s != b":":
	#	print(s)
	#	s = ser.read(1)
	r = ser.read(8)
	val = r.split(b'CH1:')[-1]
	res = int.from_bytes(val, byteorder='big') - 16
	return res

def get_vdiv2(ser):
	print("CH2?")
	ser.write("CH2?".encode('ASCII')+bytearray([13,10]))
	#s = b""
	#while s != b":":
	#	s = ser.read(1)
	r = ser.read(8)
	val = r.split(b'CH2:')[-1]
	res = int.from_bytes(val, byteorder='big') - 16
	return res

def get_tdiv(ser):
	print("TBA?")
	ser.write("TBA?".encode('ASCII')+bytearray([13,10]))
	#s = b""
	#while s != b":":
	#	s = ser.read(1)
	r = ser.read(8)
	val = r.split(b'TBA:')[-1]
	res = int.from_bytes(val, byteorder='big') -16
	return res

import time



r = vers(ser)
print(r)

#r = autoset(ser)
#print(r)

r = vdiv1(ser,8)
print(r)
r = vdiv2(ser,8)
print(r)


r = tdiv(ser,7)
print(r)

r = ypos1(ser,15)
print(r)
r = ypos2(ser,15)
print(r)

res1 = rdwf1(ser)
print(res1)
k1 = [int(i) for i in res1[50:]]

res2 = rdwf2(ser)
print(res2)
k2 = [int(i) for i in res2[50:]]



rt = trgval(ser)
print(rt)


ch1_v = get_vdiv1(ser)
print(ch1_v)

ch2_v = get_vdiv2(ser)
print(ch2_v)

td = get_tdiv(ser)
print(td)

#time.sleep(5)
r = discon(ser)
print(r)




'''
input=1
while 1 :
	# get keyboard input
	input_ = input(">> ")
        # Python 3 users
        # input = input(">> ")
	if input_ == 'exit':
		ser.close()
		exit()
	else:
		# send the character to the device
		# (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
		ser.write(input_ + '\r\n')
		out = ''
		# let's wait one second before reading output (let's give device time to answer)
		time.sleep(1)
		while ser.inWaiting() > 0:
			out += ser.read(1)
			
		if out != '':
			print (">>" + out)
'''