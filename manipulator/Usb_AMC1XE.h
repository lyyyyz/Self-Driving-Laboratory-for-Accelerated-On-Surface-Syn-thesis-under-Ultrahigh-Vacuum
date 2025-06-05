// 下列 ifdef 块是创建使从 DLL 导出更简单的
// 宏的标准方法。此 DLL 中的所有文件都是用命令行上定义的 USB_DAQ_V52_DLL_EXPORTS
// 符号编译的。在使用此 DLL 的
// 任何其他项目上不应定义此符号。这样，源文件中包含此文件的任何其他项目都会将
// USB_DAQ_V52_DLL_API 函数视为是从 DLL 导入的，而此 DLL 则将用此宏定义的
// 符号视为是被导出的。
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
