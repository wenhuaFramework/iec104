# IEC104TCP
IEC104 client simulator

在前人的基础上  我自己写了一个类

获取南瑞远动电表的累计数据

其他YX YC数据没有写进逻辑


打包备注：（配置文件夹打包进EXE）
1、pyi-makespec -F -w iec104_client.py
     生成 iec104_client.spec文件
     修改其中datas的值，原来值为datas=[]，修改的值datas=[('config.ini', '.')]
2、pyinstaller -F -w iec104_client.spec
     打包生成EXE文件
