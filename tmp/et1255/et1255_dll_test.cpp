#include <iostream>
#include "et1255.h"
#include <windows.h>
#include <vector>
#include <numeric>

#include <time.h>   

using namespace std;

int main(int argc, char* argv[] )
{
  	
    ET1255 et;
    char* aa = et.ET_StartDrv();


    cout<<"aaa<<"<<aa;
    et.ET_StopDrv();
    aa = et.ET_StartDrv();


    cout<<"aaa<<"<<aa;

    //et.ET_SetStrob();
    //et.ET_SetStrob();
    //et.ET_SetADCChnl(0);
    et.ET_SetAmplif(1);
    //et.ET_SetScanMode(0, false);
    et.ET_SetADCMode(4, 0, 1, 0);


    float r = 0;
    int ch = 1;
    //delay(5000);
    int strob=0;
    int j=0;
    bool state=false;
   // for (int i=0;i<1000;i++){
    //	printf("%d\n",et.ET_ReadDGT());
   // }
    //et.ET_WriteDGT(3);
   // et.openSerialPort(port);

    //printf("\n%f\n",et.getAngle());
      
    //et.ET_StrobDataRead(port, 500);
    //et.ET_FStrobDataRead(port,"test.dat",500);
    int chanels[] = {2,4};
    int n = sizeof(chanels)/sizeof(chanels[0]);
    float data[n];
    //et.getDataProc(300,1,&ch1,&ch2,&ch3,&ch4);
     int clo = clock();       
    printf("%d\n",n);
    for(int j =0; j<100;j++){
        et.getDataProcN(2,300,chanels,n,data, false);
        for(int i=0;i<n;i++)
        printf("%f\t", data[i]);
        printf("\n");
    }
    // do something

    cout << (clock() - clo) << endl;
        return 0;
}