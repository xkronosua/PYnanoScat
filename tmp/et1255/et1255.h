#ifndef ET1255_DLL_H
#define ET1255_DLL_H


#ifdef __cplusplus
extern "C" {
#endif

#ifdef BUILDING_ET1255_DLL_H
#define ET1255_DLL __declspec(dllexport)
#else
#define ET1255_DLL __declspec(dllimport)
#endif



#ifdef __cplusplus
}
#endif

#include <windows.h>
#include <winioctl.h>
//#include <hidsdi.h>
#include <SetupAPI.h>




#include <stdio.h>
#include <stdlib.h>


#define Get_CTL_CODE(Function) (CTL_CODE(FILE_DEVICE_UNKNOWN, Function, METHOD_BUFFERED, FILE_ANY_ACCESS))
#define ioctl_ADC_WRITE    Get_CTL_CODE(0x801)
#define ioctl_ADC_READ     Get_CTL_CODE(0x802)
#define ioctl_SCAN_WRITE   Get_CTL_CODE(0x803)
#define ioctl_SCAN_READ    Get_CTL_CODE(0x804)
#define ioctl_CTRL_WRITE   Get_CTL_CODE(0x805)
#define ioctl_CTRL_READ    Get_CTL_CODE(0x806)
#define ioctl_ADC_STROB    Get_CTL_CODE(0x807)
#define ioctl_MEM_START_WRITE   Get_CTL_CODE(0x808)
#define ioctl_AMPL_SET     Get_CTL_CODE(0x809)
#define ioctl_DAC_WRITE    Get_CTL_CODE(0x810)
#define ioctl_DGT_WRITE    Get_CTL_CODE(0x811)
#define ioctl_DGT_READ     Get_CTL_CODE(0x812)



const GUID _GUID_MID =
{
   0x20CBE45F,0xF6F7,0x4f4a,{0x8F,0x2F,0xDB,0xB6,0xBF,0x82,0xA4,0x6C}
};
/*
//c671678c-82c1-43f3-d700-0049433e9a4b
const GUID _GUID_MID =
{
   0xc671678c,0x82c1,0x43f3,{0xd7,0x00,0x00,0x49,0x43,0x3e,0x9a,0x4b}
};
*/






//extern "C" class ET1255_API ET1255

class ET1255_DLL ET1255
{
HDEVINFO hdev;
GUID GUID_ET1255;
HANDLE hHandle;
int amplif;

public:
    ET1255();
    //ET1255(LPTSTR MONITOR_CLASS_STR);

    char* ET_StartDrv();
    void ET_SetStrob();
    float ET_ReadADC();
    float ET_ReadADC(int n);
    void ET_StopDrv();
    void ET_SetADCChnl(int chnl);
    float CodeToVolt(int w);
    void ET_SetScanMode(int ChCount, bool ScanEnable);
    void ET_SetADCMode(int Frq, bool PrgrmStart, bool IntTackt, bool MemEnable);
    void ET_SetAmplif(int Value);
    int ET_MeasEnd();
    void ET_WriteDGT(int Value);
    float ET_ReadMem();
    void ET_SetAddr(int Addr);
    int ET_ReadDGT();
    void getDataRAW(int NAver, float *ch1, float *ch2, float *ch3, float *ch4);
    void getDataProc(int NIter, int NAver, float *ch1, float *ch2, float *ch3, float *ch4);
    float* getDataProcN(int refChanel, int NIter, int chanels[], int chanels_N, float data[], bool print=false);

    //unsigned Get_CTL_CODE(int code);
};

extern "C" {
ET1255* ET1255_new(){return new ET1255(); }
char * ET1255_ET_StartDrv(ET1255* et){ return et->ET_StartDrv(); }

    void ET1255_ET_SetStrob(ET1255* et){ return et->ET_SetStrob(); }
    float ET1255_ET_ReadADC(ET1255* et){ return et->ET_ReadADC(); }
    float ET1255_ET_ReadADC_n(ET1255* et, int n){ return et->ET_ReadADC(n); }
    void ET1255_ET_StopDrv(ET1255* et){ return et->ET_StopDrv(); }
    void ET1255_ET_SetADCChnl(ET1255* et, int chnl){return et->ET_SetADCChnl(chnl);}
    float ET1255_CodeToVolt(ET1255* et, int w){return et->CodeToVolt(w);}
    void ET1255_ET_SetScanMode(ET1255* et, int ChCount, bool ScanEnable){
        return et->ET_SetScanMode( ChCount,  ScanEnable);}
    void ET1255_ET_SetADCMode(ET1255* et, int Frq, bool PrgrmStart, bool IntTackt, bool MemEnable){
        return et->ET_SetADCMode( Frq,  PrgrmStart,  IntTackt,  MemEnable);}
    void ET1255_ET_SetAmplif(ET1255* et, int Value){return et->ET_SetAmplif(Value);}
    void ET1255_ET_WriteDGT(ET1255* et, int Value){return et->ET_WriteDGT(Value);}
    int ET1255_ET_ReadDGT(ET1255* et){return et->ET_ReadDGT();}
    int ET1255_ET_MeasEnd(ET1255* et){ return et->ET_MeasEnd(); }

    void ET1255_getDataRAW(ET1255* et, int N, float *ch1, float *ch2, float *ch3, float *ch4){
        return et->getDataRAW(N, ch1, ch2, ch3, ch4);
    }
    void ET1255_getDataProc(ET1255* et, int NIter,int NAver, float *ch1, float *ch2, float *ch3, float *ch4){
        return et->getDataProc(NIter, NAver, ch1, ch2, ch3, ch4);
    }
    float* ET1255_getDataProcN(ET1255* et, int refChanel, int NIter, int chanels[], int chanels_N, float data[], bool print){
        return et->getDataProcN(refChanel, NIter, chanels, chanels_N, data, print);
    }
}









#endif // ET1255_DLL_H
