// ���� ifdef ���Ǵ���ʹ�� DLL �������򵥵�
// ��ı�׼�������� DLL �е������ļ��������������϶���� USB_DAQ_V52_DLL_EXPORTS
// ���ű���ġ���ʹ�ô� DLL ��
// �κ�������Ŀ�ϲ�Ӧ����˷��š�������Դ�ļ��а������ļ����κ�������Ŀ���Ὣ
// USB_DAQ_V52_DLL_API ������Ϊ�Ǵ� DLL ����ģ����� DLL ���ô˺궨���
// ������Ϊ�Ǳ������ġ�
#ifdef USB_DAQ_V52_DLL_EXPORTS
#define USB_DAQ_V52_DLL_API extern "C" __declspec(dllexport)
#else
#define USB_DAQ_V52_DLL_API extern "C" __declspec(dllimport)
#endif

 USB_DAQ_V52_DLL_API int __stdcall  openUSB(void);
 USB_DAQ_V52_DLL_API int __stdcall  closeUSB(void);

 USB_DAQ_V52_DLL_API int __stdcall  get_device_num(void);
 USB_DAQ_V52_DLL_API int __stdcall  Reset_Usb_Device(int dev); 

 USB_DAQ_V52_DLL_API int __stdcall  Read_Port_In(int dev,unsigned char* in_port);
 USB_DAQ_V52_DLL_API int __stdcall  Read_Port_Out(int dev,unsigned char* out_port);
 USB_DAQ_V52_DLL_API int __stdcall  Write_Port_Out(int dev,unsigned char out_port);
 USB_DAQ_V52_DLL_API int __stdcall  Set_Port_Out(int dev,unsigned char out_port);
 USB_DAQ_V52_DLL_API int __stdcall  Reset_Port_Out(int dev,unsigned char out_port);
 USB_DAQ_V52_DLL_API  int __stdcall Read_Position(int dev,unsigned int Axs,unsigned int* Pos,unsigned char* RunState,unsigned char* IOState,unsigned char* SyncIO);
 USB_DAQ_V52_DLL_API  int __stdcall Read_Speed(int dev,unsigned int Axs,unsigned int* speed);
 USB_DAQ_V52_DLL_API   int __stdcall  Set_Axs(int dev,unsigned int Axs,unsigned int Run_EN);
  USB_DAQ_V52_DLL_API   int __stdcall  AxsStop(int dev,unsigned int Axs);
  USB_DAQ_V52_DLL_API   int __stdcall  MovToOrg(int dev,unsigned int Axs,unsigned int Dir,unsigned char Outmod,unsigned int Speed);
  USB_DAQ_V52_DLL_API   int __stdcall  FL_ContinueMov(int dev,unsigned int Axs,unsigned int Dir,unsigned char Outmod,unsigned int Vo,unsigned int Vt);
  USB_DAQ_V52_DLL_API   int __stdcall  FH_ContinueMov(int dev,unsigned int Axs,unsigned int Dir,unsigned char Outmod,unsigned int Vo,unsigned int Vt);
  USB_DAQ_V52_DLL_API   int __stdcall  FH_ContinueAdjustSpeed(int dev,unsigned int Axs,unsigned int Vo,unsigned int Vt);
  USB_DAQ_V52_DLL_API  int __stdcall DeltMov(int dev,unsigned int Axs,unsigned int curve,unsigned int Dir,unsigned char Outmod,unsigned int Vo,unsigned int Vt,unsigned int Length,unsigned int StartDec,unsigned int Acctime,unsigned int Dectime);
  USB_DAQ_V52_DLL_API   int __stdcall Set_Encorder(int dev,int Axs,int mod,int set8000,int enable);
  USB_DAQ_V52_DLL_API    int __stdcall  Read_Encorder(int dev,int Axs, unsigned int* Value);
