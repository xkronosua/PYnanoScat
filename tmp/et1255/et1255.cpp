
#include "et1255.h"
#include <iostream>
#include <vector>
#include <sys\timeb.h>
#include <windows.h>								// for Windows APIs
#include <time.h>
#include <sstream>
#include <stdio.h>
#include <cstdlib>
#include <math.h> 
using namespace std;

ET1255::ET1255()
{
	hHandle = INVALID_HANDLE_VALUE;
}

void ET1255::ET_StopDrv() {
	CloseHandle(hHandle);

}

char* ET1255::ET_StartDrv() {
	char *dwResult = (char*)"ET1255:";
//GUID MID;
//LPTSTR CLASS_STR = L"{20CBE45F-F6F7-4f4a-8F2F-DBB6BF82A46C}";
//UuidFromString((RPC_WSTR)CLASS_STR, &MID);
	cout << "Start...";

	HDEVINFO hDevInfo = SetupDiGetClassDevs( &_GUID_MID, NULL, 0, DIGCF_DEVICEINTERFACE | DIGCF_PRESENT | DIGCF_ALLCLASSES);
	if (hDevInfo == INVALID_HANDLE_VALUE)
	{
		return (char*)"ERR_FAIL";
	}

	std::vector<SP_INTERFACE_DEVICE_DATA> interfaces;

	for (DWORD i = 0; true; ++i)
	{
		SP_DEVINFO_DATA devInfo;
		devInfo.cbSize = sizeof(SP_DEVINFO_DATA);
		BOOL succ = SetupDiEnumDeviceInfo(hDevInfo, i, &devInfo);
		if (GetLastError() == ERROR_NO_MORE_ITEMS)
			break;
		if (!succ) continue;

		SP_INTERFACE_DEVICE_DATA ifInfo;
		ifInfo.cbSize = sizeof(SP_INTERFACE_DEVICE_DATA);
		if (TRUE != SetupDiEnumDeviceInterfaces(hDevInfo, &devInfo,	&(_GUID_MID), 0, &ifInfo))
		{
			if (GetLastError() != ERROR_NO_MORE_ITEMS)
				break;
		}
		interfaces.push_back(ifInfo);
	}

	std::vector<SP_INTERFACE_DEVICE_DETAIL_DATA*> devicePaths;
	for (size_t i = 0; i < interfaces.size(); ++i)
	{
		DWORD requiredSize = 0;
		SetupDiGetDeviceInterfaceDetail(hDevInfo, &(interfaces.at(i)), NULL, 0, &requiredSize, NULL);
		SP_INTERFACE_DEVICE_DETAIL_DATA* data = (SP_INTERFACE_DEVICE_DETAIL_DATA*) malloc(requiredSize);
		//Q_ASSERT(data);
		data->cbSize = sizeof(SP_INTERFACE_DEVICE_DETAIL_DATA);

		if (!SetupDiGetDeviceInterfaceDetail(hDevInfo, &(interfaces.at(i)), data, requiredSize, NULL, NULL))
		{
			continue;
		}
		devicePaths.push_back(data);
		//QString s;
		//TCHAR* t = data->DevicePath;
		//s = (LPSTR)(t);

		//cout<<"data: "<<t[1];
		hHandle = CreateFile(data->DevicePath,
			GENERIC_READ | GENERIC_WRITE,
			FILE_SHARE_READ | FILE_SHARE_WRITE,
			NULL,
			OPEN_EXISTING,
			FILE_ATTRIBUTE_NORMAL,
			0);
		if (hHandle == INVALID_HANDLE_VALUE) {
			cout << GetLastError();
			//return "ERR";
		}
		else {
			//	QString s = QString::fromWCharArray(data->DevicePath);
			//	cout<<s;
			break;
		}
	}

	//cout<<hHandle;
	return dwResult;
}
//void ET1255:Get_

void ET1255::ET_SetStrob() {
	DWORD BytesReturned = 0;
	int result = 0;
	result =	DeviceIoControl(hHandle, ioctl_ADC_STROB,
		NULL, 0, NULL, 0,
		&BytesReturned,
		(LPOVERLAPPED)NULL);
	if (!result)
		cout << "Error in <ET_SetStrob> =" << GetLastError();

}

float ET1255::ET_ReadADC() {
	int rdata;
	DWORD BytesReturned;

	if (!DeviceIoControl(hHandle, ioctl_ADC_READ, NULL, 0, &rdata, sizeof(rdata), &BytesReturned, (LPOVERLAPPED)NULL))
	{
		cout << "Error in <ET_ReadADC> =" << GetLastError();
		 return 0;
	}
	else {
		//cout<<rdata<<" "<<BytesReturned;
		return CodeToVolt(rdata & 0x0FFF);
		//return (rdata[0]+rdata[1] >> 8) & 0x0FFF;

	}
}
/*var
	ioctlCode, BytesReturned: cardinal;
	rdata: array[0..1] of byte;
begin
	ioctlCode:=Get_CTL_CODE($804);
	DeviceIoControl(hHandle, ioctlCode, nil, 0, @rdata, sizeof(rdata), BytesReturned, nil);
	Result := (rdata[0] + rdata[1] shl 8) and $0FFF;
end;
Здесь: Result
*/
float ET1255::ET_ReadMem() {
	int rdata;
	DWORD BytesReturned;

	if (!DeviceIoControl(hHandle, ioctl_SCAN_READ, NULL, 0, &rdata, sizeof(rdata), &BytesReturned, (LPOVERLAPPED)NULL))
	{
		cout << "Error in <ET_ReadMem> =" << GetLastError();
		return 0;
	}
	else {
		//cout<<rdata<<" "<<BytesReturned;
		return CodeToVolt(rdata & 0x0FFF);
	}
}



float ET1255::ET_ReadADC(int n) {
	float res = 0;
	for (int i = 0; i < n; i++) {
		res += this->ET_ReadADC();
	}
	return res / n;
}


void ET1255::ET_SetAddr(int wdata) {
	DWORD BytesReturned = 0;
	int result = 0;
	result =	DeviceIoControl(hHandle, ioctl_MEM_START_WRITE, &(wdata), sizeof(wdata), NULL, 0, &BytesReturned,	(LPOVERLAPPED)NULL);
	if ( !result)	cout << "Error in <ET_SetAddr> =" << GetLastError();

}


void ET1255::ET_SetADCChnl(int chnl) {
	DWORD BytesReturned = 0;
	int result = 0;
	result =	DeviceIoControl(hHandle, ioctl_ADC_WRITE, &(chnl), sizeof(chnl), NULL, 0, &BytesReturned,	(LPOVERLAPPED)NULL);
	if ( !result)	cout << "Error in <ET_SetADCChnl> =" << GetLastError();

}


float ET1255::CodeToVolt(int w) {

	float result = 1;
	int p = 0;
	for (int i = 0; i < 11; i++) {

		p = 11 - 2 * i;
		if (p > 0) result = result + ((w & (1 << i)) << p);
		else		 result = result + ((w & (1 << i)) >> abs(p));
	}
	result = (float)(-2.5 + 5 * result / 0xFFF);
	return result;
}

void ET1255::ET_SetScanMode(int ChCount, bool ScanEnable) {

	DWORD BytesReturned = 0;
	int wdata;

	if (ChCount > 16) ChCount = 16;
	wdata = ChCount;
	if (ScanEnable) wdata = wdata | 0x20;
	if (!DeviceIoControl(hHandle, ioctl_SCAN_WRITE, &wdata, sizeof(wdata), NULL, 0, &BytesReturned, (LPOVERLAPPED)NULL)) {
		cout << "Error in <ET_SetScanMode> =" << GetLastError();
	}

}

void	ET1255::ET_SetADCMode(int Frq, bool PrgrmStart, bool IntTackt, bool MemEnable) {
	DWORD BytesReturned = 0;
	WORD wdata = 0;

	if (Frq > 3) Frq = 3;
	wdata = Frq;
	if (!PrgrmStart) wdata = wdata | 0x04;
	if (!IntTackt)	 wdata = wdata | 0x08;
	if (!MemEnable)	wdata = wdata | 0x10;

	if (!DeviceIoControl(hHandle, ioctl_CTRL_WRITE, &wdata, sizeof(wdata), NULL, 0, &BytesReturned, (LPOVERLAPPED)NULL)) {
		cout << "Error in <ET_SetADCMode> =" << GetLastError();
	}
}

void ET1255::ET_SetAmplif(int Value) {
	this->amplif = Value;
	DWORD BytesReturned = 0;
	if (Value > 15) Value = 15;
	if (!DeviceIoControl(hHandle, ioctl_AMPL_SET, &Value, sizeof(Value), NULL, 0, &BytesReturned, (LPOVERLAPPED)NULL)) {
		cout << "Error in <ET_SetAmplif> =" << GetLastError();
	}
}

void ET1255::ET_WriteDGT(int Value) {
	DWORD BytesReturned = 0;

	if (!DeviceIoControl(hHandle, ioctl_DGT_WRITE, &Value, sizeof(Value), NULL, 0, &BytesReturned, (LPOVERLAPPED)NULL)) {
		cout << "Error in <ET_WriteDGT> =" << GetLastError();
	}
}


int ET1255::ET_ReadDGT() {
	DWORD BytesReturned = 0;
	int rdata;
	if (!DeviceIoControl(hHandle, ioctl_DGT_READ, NULL, 0, &rdata, sizeof(rdata), &BytesReturned, (LPOVERLAPPED)NULL)) {
		cout << "Error in <ET_ReadDGT> =" << GetLastError();
		return -1;
	}
	else return rdata & 0xFF;
}



int ET1255::ET_MeasEnd() {
	DWORD BytesReturned = 0;
	int rdata;



	if (!DeviceIoControl(hHandle, ioctl_CTRL_READ, NULL, 0, &rdata, sizeof(rdata), &BytesReturned, (LPOVERLAPPED)NULL)) {
		cout << "Error in <ET_MeasEnd> =" << GetLastError();
		return 0;
	}
	else return (rdata & 0x0001) == 0x0001;
}



void ET1255::getDataRAW(int N,float *ch1, float *ch2, float *ch3, float *ch4) {
	
	float data[5];
	float r=0;
	for (int i=0; i<N; i++){
		int ch = 0;
		ET_SetADCChnl(ch);
		int m=0;
			for (ch=0; ch < 5; ) {
							
							r = ET_ReadADC() ;
							data[ch] = (r + data[ch]*i)/(i+1);
							m++;
							if (ET_MeasEnd()&&m>50) {ET_SetStrob(); ch++; ET_SetADCChnl(ch); m=0;}
						}
					}
	*ch1 = data[0];
	*ch2 = data[1];
	*ch3 = data[2];
	*ch4 = data[4];
	//printf("\n%d\t%.4f\t%.4f\t%.4f\t%.4f\n", N,*ch1,*ch2,*ch3,*ch4);
}


float* ET1255::getDataProcN(int refChanel,int NIter,int chanels[],int chanels_N, float data[], bool print)
{
	float* out = new float[chanels_N];
 float *tmp_r= new float[chanels_N];
	printf("\n");
	for(int i=0;i<chanels_N;i++) {
		if (print) printf("i:%d-%d\t", i,chanels[i]);
		tmp_r[i]=0;
	}
		if (print) printf("\n");

	int NAver = 10;
	if(print) NAver = 1;


    vector< vector<float> > arr;
   

    for(int i=0;i<NIter;i++) {
    	vector<float> tmp;
    	ET_SetADCChnl(chanels[0]);
		for(int i=0;i<chanels_N;i++) {tmp_r[i]=0;}
		for (int m=0;m<NAver;m++){
			for (int ch=0; ch < chanels_N; ch++ ) {
				float r = 0;
				for(int k=0;k<=chanels[ch];k++){
					ET_SetADCChnl(k);
					r = ET_ReadADC();
					if(ET_MeasEnd()){ET_SetStrob();}
				}
				
				
				
				tmp_r[ch] = (tmp_r[ch]*m+r)/(m+1);
				
			}
		}
		for(int i=0;i<chanels_N;i++) {
			tmp.push_back(tmp_r[i]);
			if(print) printf("%d:%.4f\t",chanels[i], tmp[i]);
		}

        arr.push_back(tmp);
		if(print) printf("\n");
        
    }

double ref_mean = 0;
for (int i = 0; i < (int)arr.size(); i++){
	ref_mean += arr[i][refChanel];
}
ref_mean /= arr.size();

//printf("\nR_M:%f",ref_mean);
float *res_high=new float[chanels_N];
int n_high =0;
float *res_low = new float[chanels_N];
int n_low =0;
for(int i=0;i<chanels_N;i++){
res_high[i]=0;
res_low[i]=0;
}

for (int i = 0; i < (int)arr.size(); i++)
{
	if (arr[i][refChanel]>ref_mean)
	{
	    for(int j=0;j<chanels_N;j++){
	    	res_high[j] = (res_high[j]*n_high +arr[i][j])/(n_high+1);
	    }

	    n_high++;
    }
    else{
    	for(int j=0;j<chanels_N;j++){
	    	res_low[j] = (res_low[j]*n_low +arr[i][j])/(n_low+1);
	    }
	    
	    n_low++;

    }
}

if (print) 
	printf("\n");
	for(int i=0;i<chanels_N;i++){
		data[i] = res_high[i]-res_low[i];
		if (print) printf("%.4f\n", data[i]);
		out[i] = data[i];}
	printf("\n");
	
	delete tmp_r;
	delete res_low;
	delete res_high;
	return out;
}

void ET1255::getDataProc(int NIter, int NAver,float *ch1, float *ch2, float *ch3, float *ch4)
{
  
    vector< vector<float> > arr;


    for(int i=0;i<NIter;i++) {getDataRAW(NAver, &*ch1,&*ch2,&*ch3,&*ch4);
    	vector<float> tmp;
    	tmp.push_back(*ch1);
    	tmp.push_back(*ch2);
    	tmp.push_back(*ch3);
    	tmp.push_back(*ch4);
        arr.push_back(tmp);
        printf("\t%.4f\t%.4f\t%.4f\t%.4f\n", *ch1,*ch2,*ch3,*ch4);
        
    }

double ref_mean = 0;
int ref_chanel = 1;
for (int i = 0; i < (int)arr.size(); i++){
	ref_mean += arr[i][ref_chanel];
}
ref_mean /= arr.size();

//printf("\nR_M:%f",ref_mean);
float res_high[4] ={0,0,0,0};
int n_high =0;
float res_low[4] ={0,0,0,0};
int n_low =0;

for (int i = 0; i < (int)arr.size(); i++)
{
	if (arr[i][ref_chanel]>ref_mean)
	{
	    for(int j=0;j<4;j++){
	    	res_high[j] = (res_high[j]*n_high +arr[i][j])/(n_high+1);
	    }

	    n_high++;
    }
    else{
    	for(int j=0;j<4;j++){
	    	res_low[j] = (res_low[j]*n_low +arr[i][j])/(n_low+1);
	    }
	    
	    n_low++;

    }
}

*ch1 = res_high[0]-res_low[0];
*ch2 = res_high[1]-res_low[1];
*ch3 = res_high[2]-res_low[2];
*ch4 = res_high[3]-res_low[3];
printf("\n\t%.4f\t%.4f\t%.4f\t%.4f\n", *ch1,*ch2,*ch3,*ch4);


}




/*
int main(int argc, char *argv[])
{
	 // QCoreApplication a(argc, argv);


	ET1255 et;
	char* aa = et.ET_StartDrv();


	cout<<"aaa<<"<<aa;
	et.ET_StopDrv();
	aa = et.ET_StartDrv();


	cout<<"aaa<<"<<aa;

	//et.ET_SetStrob();
	//et.ET_SetStrob();
	et.ET_SetADCChnl(0);
	et.ET_SetAmplif(5);
	et.ET_SetScanMode(0, false);
	et.ET_SetADCMode(0, 1, 1, 0);


	float r = 0;
	int ch = 1;
	 // delay(5000);
	int strob=0;
	for (int i=0; i<20; i++){
		//delay(5);
		for (ch=0;ch<1;ch++){
		et.ET_SetADCChnl(ch);
		r = et.ET_ReadADC();
		cout<<r;
		strob = et.ET_MeasEnd();
		if(strob) et.ET_SetStrob();
		}
	}
	et.ET_StopDrv();
	 // return a.exec();
}
*/