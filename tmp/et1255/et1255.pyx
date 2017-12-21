cdef extern from "et1255.h" namespace "ET1255_API":
	cdef cppclass ET1255:
		ET1255() except +
		int amplif
		char* ET_StartDrv()
		void ET_SetStrob()
		float ET_ReadADC()
		float ET_ReadADC(int n)
		void ET_StopDrv()
		void ET_SetADCChnl(int chnl)
		float CodeToVolt(int w)
		void ET_SetScanMode(int ChCount, bool ScanEnable)
		void ET_SetADCMode(int Frq, bool PrgrmStart, bool IntTackt, bool MemEnable)
		void ET_SetAmplif(int Value)
		int ET_MeasEnd()
		void ET_WriteDGT(int Value)
		float ET_ReadMem()
		void ET_SetAddr(int Addr)
		int ET_ReadDGT()
		void getDataRAW(int NAver, float *ch1, float *ch2, float *ch3, float *ch4)
		void getDataProc(int NIter, int NAver, float *ch1, float *ch2, float *ch3, float *ch4)
		void getDataProcN(int refChanel, int NIter, int chanels[], int chanels_N, float data[], bool Print)


cdef class ET1255:
	cdef ET1255 *thisptr
	def __cinit__(self):
		self.thisptr = new ET1255()
	def __dealloc__(self):
		del self.thisptr
	def ET_StartDrv():
		return self.thisptr.ET_StartDrv()
	def ET_ReadADC():
		return self.thisptr.ET_ReadADC()
	def ET_ReadADC(self,int n):
		return self.thisptr.ET_ReadADC(n)
	def ET_StopDrv(self):
		return self.thisptr.ET_StopDrv()
	def ET_SetADCChnl(self,int chnl):
		return self.thisptr.ET_SetADCChnl(chnl)
	#def CodeToVolt(self, int w):
	#	return self.thisptr.CodeToVolt(int w)
	def ET_SetScanMode(self,int ChCount, bool ScanEnable):
		return self.thisptr.ET_SetScanMode(ChCount, ScanEnable)
	def ET_SetADCMode(self,int Frq, bool PrgrmStart, bool IntTackt, bool MemEnable):
		return self.thisptr.ET_SetADCMode(Frq, PrgrmStart, IntTackt, MemEnable)
	def ET_SetAmplif(self,int Value):
		return self.thisptr.ET_SetAmplif(Value)
	def ET_MeasEnd(self):
		return self.thisptr.ET_MeasEnd()
	def ET_WriteDGT(self,int Value):
		return self.thisptr.ET_WriteDGT(Value)
	def ET_ReadMem(self,):
		return self.thisptr.ET_ReadMem()
	def ET_SetAddr(self,int Addr):
		return self.thisptr.ET_SetAddr(Addr)
	def ET_ReadDGT(self):
		return self.thisptr.ET_ReadDGT()
	#def getDataRAW(self,int NAver, float *ch1, float *ch2, float *ch3, float *ch4):
	#	self.thisptr.getDataRAW(NAver, &ch1, &ch2, &ch3, &ch4):
	#def getDataProc(self, int NIter, int NAver, float *ch1, float *ch2, float *ch3, float *ch4):
	#	return self.thisptr.getDataProc(int NIter, int NAver, float *ch1, float *ch2, float *ch3, float *ch4)


	def getDataProcN(self, int refChanel, int NIter, int *chanels,bool Print):
		cdef int N = len(chanels)
		cdef cpplist[] data[N]
		self.thisptr.getDataProcN( refChanel, NIter, chanels, N, data, Print):