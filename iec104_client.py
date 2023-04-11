import socket
import struct
import binascii
import requests
import json
import configparser
import os
import time
import threading

# 上报数据线程
class updataThreading(threading.Thread):
    def __init__(self, url, data, server_ip, server_port):
        super(updataThreading, self).__init__()
        self.url = url
        self.data = data
        self.server_ip = server_ip
        self.server_port = server_port

    # 线程要运行的代码
    def run(self):
        # response = requests.post(self.url, data=self.data)
        # json_data = json.loads(response.text)
        # if json_data and json_data['message']:
        #     print(json_data['message'])
        # else:
        #     print('未知错误')

        self.udp_to_server()
        print('==========上报结束==========')
    
    #将数据通过udp协议传输到网闸外的udp server
    def udp_to_server(self):
        server_addr = (self.server_ip, self.server_port)
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        json_string = json.dumps(self.data)
        udp.sendto(json_string.encode(), server_addr)
        time.sleep(1)
        udp.close()

        #print('==========所占的字节数============')
        #print(len(json_string.encode()))


#104协议获取数据封装类
class iec104_tcp_client():
    Tx = 0
    Rx = 0
    _socket = ''

    #结构函数初始化
    def __init__(self, type='master'):
        self.is_begin = False      #是否开始
        self.is_over = False       #是否结束
        self.type = type           #是主站还是从站
        self.info_list = {}        #接收到的信息
        self.cf = self.load_ini()  #配置分解
        self.connect()

    #建立连接
    def connect(self):
        #获取参数
        if self.type == 'master':
            self.targetip = self.get_value('SETUP', 'nari_master_ip')  #主IP
        else:
            self.targetip = self.get_value('SETUP', 'nari_slave_ip')  #备IP
        self.port = int(self.get_value('SETUP', 'port'))    #端口

        # socket.AF_INET服务器之间网络通信
        # socket.SOCK_STREAM 流式socket , for TCP
        # 协议编号（默认为0）
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)  # 创建套接字
        self._socket.settimeout(30)  # 设置套接字操作的超时期
        l_onoff = 1
        l_linger = 0

        # 设置给定套接字选项的值
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', l_onoff, l_linger))  # level,optname,value

        # 连接到address处的套接字
        self._socket.connect((self.targetip, self.port))

    #开始执行
    def start(self):
        self.is_begin = True
        while not self.is_over:
            if self.is_begin:
                # 1、发送启动帧，首次握手（U帧）680407000000
                cmd = "68 04 07 00 00 00"
                packet = self.buildpacket(cmd, 'U')
                self.send(packet, 'U')
                self.is_begin = False
                print('=========发送启动帧68 04 07 00 00 00=========')

            output = self._socket.recv(1024)
            hex_str = binascii.b2a_hex(output).decode('unicode_escape')  # 二进制（bytes）转换为十六进制（hex）
            #print('=========收到16进制报文=========')
            #print(hex_str)

            pkgs = self.package(hex_str)  #递归解析报文 并解决可能粘包问题  返回报文列表
            for item in pkgs:
                print('返回报文：')
                print(item)
                # 2、接收服务端响应的启动确认帧 68040B000000
                if len(item) == 12:
                    #U帧和S帧
                    if item.find('68040100') != -1:
                        #S帧
                        self.s_frame(item)
                    else:
                        #U帧
                        self.u_frame(item)
                else:
                    #I帧
                    self.i_frame(item)
        self.quit()

    #退出
    def quit(self):
        self._socket.close()

    #创建包
    def buildpacket(self, cmd, type='S'):
        iec104_list = cmd.split(' ')
        iec104_hex_list = []  # [104, 4, 7, 0, 0, 0]  命令数组
        for item in iec104_list:
            temp = int(item, 16)
            iec104_hex_list.append(temp)

        packet = struct.pack("%dB" % (len(iec104_hex_list)), *iec104_hex_list)  # 通过struct转换成发送的十六进制串
        return packet

    # 十进制接收序号
    def setRx(self):
        self.Rx = self.Rx+1
        if self.Rx > 65534:
            self.Rx = 1

    # 十进制发送序号
    def setTx(self):
        self.Tx = self.Tx + 1
        if self.Tx > 65534:
            self.Tx = 1
        return self.Tx

    #发送序号重新组合
    def getHexTx(self):
        byte_tx = bin(self.Tx<<1)[2:]  #转换为2进制
        str_len = len(byte_tx)
        if str_len < 16:
            diff = 16 - str_len   #补0个数

        zero_str = ''
        for i in range(diff):
            zero_str = zero_str + '0'
        final_str = zero_str + byte_tx   #16位，不足补0

        max_bin = final_str[0:8] #高8位
        low_bin = final_str[8:]  #低8位

        low_sixteen = (hex(int(low_bin, 2)))[2:]  #低8位转为16进制
        max_sixteen = (hex(int(max_bin, 2)))[2:]  #高8位转为16进制
        if len(low_sixteen) != 2:
            low_sixteen = '0' + low_sixteen
        if len(max_sixteen) != 2:
            max_sixteen = '0' + max_sixteen
        grp = low_sixteen + ' ' + max_sixteen
        #print(grp)
        return grp

    #接收序号重新组合
    def getHexRx(self):
        byte_rx = bin(self.Rx<<1)[2:]  #转换为2进制
        str_len = len(byte_rx)
        if str_len < 16:
            diff = 16 - str_len   #补0个数

        zero_str = ''
        for i in range(diff):
            zero_str = zero_str + '0'
        final_str = zero_str + byte_rx   #16位，不足补0

        max_bin = final_str[0:8] #高8位
        low_bin = final_str[8:]  #低8位

        low_sixteen = (hex(int(low_bin, 2)))[2:]  #低8位转为16进制
        max_sixteen = (hex(int(max_bin, 2)))[2:]  #高8位转为16进制
        if len(low_sixteen) != 2:
            low_sixteen = '0' + low_sixteen
        if len(max_sixteen) != 2:
            max_sixteen = '0' + max_sixteen
        grp = low_sixteen + ' ' + max_sixteen
        #print(grp)
        return grp

    #S帧回调
    def s_frame(self, hex_str):
        pass

    #U帧回调
    def u_frame(self, hex_str):
        if hex_str == '680443000000':
            #接收U帧 测试帧  超过一定时间没有下发和上报时
            cmd = '68 04 83 00 00 00'  #应答U帧
            packet = self.buildpacket(cmd, 'U')
            self.send(packet, 'U')
            print('======收到测试帧，应答U帧=======')
        elif hex_str == '68040b000000':
            print('=========收到启动确认帧68 04 0b 00 00 00==========')
            #3、68（启动符）0E（长度）04  00（发送序号）0E  00（接收序号）65（类型标示）01（可变结构限定词）06  00（传输原因）01  00（公共地址）00 00 00（信息体地址）45（QCC）
            tx = self.getHexTx()  #发送序号
            rx = self.getHexRx()  #接收序号
            cmd = '68 0e ' + tx + ' ' + rx + ' 65 01 06 00 01 00 00 00 00 45'
            print('=========发送电度总召帧' + cmd + '==========')
            packet = self.buildpacket(cmd, 'I')
            self.send(packet, 'I')
        else:
            pass

    #I帧回调
    def i_frame(self, hex_str):
        self.setRx() #设置接收序号
        len = hex_str[2:4]  #长度
        type = hex_str[12:14] #类型
        cause = hex_str[16:20] #原因
        if len == '0e' and type == '65' and cause == '0700':
            #接收电度总召唤确认
            #68（启动符）0E（长度）10  00（发送序号）06  00（接收序号）65（类型标示）01（可变结构限定词）07  00（传输原因）01  00（公共地址）00 00 00（信息体地址）45（QCC）
            print('=========接收电度总召唤确认=========')
            # rx = self.getHexRx()  #接收序号
            # cmd = '68 04 01 00 ' + rx  #应答S帧
            # packet = self.buildpacket(cmd, 'S')
            # print('========应答S帧=========>' + cmd)
            # self.send(packet, 'S')
            # time.sleep(0.2)
            #print('-------------------')
        elif len == '0e' and type == '65' and cause == '0a00':
            #接收结束电度总召唤帧
            #68（启动符）0E（长度）14  00（发送序号）06  00（接收序号）65（类型标示）01（可变结构限定词）0a  00（传输原因）01  00（公共地址）00 00 00（信息体地址）45（QCC）
            print('======接收结束电度总召唤帧=========')
            rx = self.getHexRx()  #接收序号
            cmd = '68 04 01 00 ' + rx  #应答S帧
            packet = self.buildpacket(cmd, 'S')
            print('========应答S帧=========>' + cmd)
            self.send(packet, 'S')
            self.is_over = True
            time.sleep(1)
            self.submit()  #收到电度总召结束帧后再提交数据到服务器
        elif type == '0f':
            print('======接收电度数据=========')
            self.parse_data(hex_str)

            # rx = self.getHexRx()  #接收序号
            # cmd = '68 04 01 00 ' + rx  #应答S帧
            # packet = self.buildpacket(cmd, 'S')
            # print('========应答S帧=========>' + cmd)
            # self.send(packet, 'S')
            # time.sleep(0.2)
            print('-------------------')

    #递归解析报文 解决可能粘包问题
    def package(self, hex_str):
        rtn = self.str_substr(hex_str)
        pkgs = []
        pkgs.append(rtn[0])
        if rtn[1]:
            arr = self.package(rtn[1])
            pkgs = pkgs + arr
        return pkgs

    #截取字符串中第一个完整的报文
    def str_substr(self, hex_str):
        tmp = []
        if hex_str.find('68') != -1 and hex_str.find('68') == 0:
            length = int(hex_str[2:4], 16)
            if len(hex_str) > (length * 2 + 4):
                end = length * 2 + 4
                str = hex_str[0:end]
                other_str = hex_str[end:]
                tmp.append(str)
                tmp.append(other_str)
            else:
                str = hex_str[0:]
                other_str = ''
                tmp.append(str)
                tmp.append(other_str)
        return tmp

    #发送报文
    def send(self, packet, type='S'):
        time.sleep(0.1)
        self._socket.send(packet)
        if type == 'I':
            self.setTx() #发送完之后，发送序号加1

    #将低位在前高位在后的16进制报文转换为十进制数
    def bw_info_to_int(self, params):
        i = 0
        hex_str = ''
        while i < len(params):
            hex_str = params[i:i+2] + hex_str
            i = i + 2
        return int(hex_str, 16)

    #转换报文为真实数据
    def parse_data(self, hex_str):
        info_len = hex_str[2:4]  #长度
        type = hex_str[12:14] #类型
        cause = hex_str[16:20] #原因
        if type == '0f':
            data = hex_str[24:]
            i = 0
            while i < len(data):
                addr = self.bw_info_to_int(data[i:i+6])
                value = self.bw_info_to_int(data[i+6:i+6+8])  #信息站四字节
                quality = int(data[i+6+8:i+6+8+2], 16)  #信息描述1字节
                self.info_list[addr] = {
                    'addr': addr,
                    'value': value,
                    'quality': quality
                }
                i = i + 16

    #加载配置文件
    def load_ini(self):
        file_name = os.path.dirname(__file__) + '\\config.ini'
        cf = configparser.ConfigParser()
        cf.read(file_name, encoding='utf-8')
        return cf

    #获取配置文件某项的值
    def get_value(self, section='SETUP', key='ip'):
        data = self.cf.get(section, key)
        return data

    #获取配置文件某个section的键值对
    def get_key_values(self, section='SETUP'):
        return self.cf.items(section)

    #提交到远程服务器
    def submit(self):
        url = self.get_value('SETUP', 'url')

        #配置文件读取相应中文名和系数
        cn_names = []
        key_values = self.get_key_values('TAGS') 
        for item in key_values:
            tmp = item[1].split('|')
            cn_names.append({
                'name': tmp[0],
                'factor': tmp[1]
            })

        #排序读取到的数据
        sorted_keys = sorted(self.info_list)
        sorted_values = []
        if len(key_values) == len(sorted_keys):
            for i in sorted_keys:
                sorted_values.append(self.info_list[i])
                
            i = 0
            params = {}
            input = []
            for item in sorted_values:
                temp = {}
                #temp['cn_name'] = cn_names[i]['name']
                temp['address'] = item['addr']
                temp['value'] = item['value']
                #temp['actual_value'] = item['value'] * float(cn_names[i]['factor'])
                #temp['quality'] = item['quality']
                #temp['factor'] = cn_names[i]['factor']
                input.append(temp)
                i = i + 1

            print('----------------------------')
            params['data'] = json.dumps(input)
            params['type'] = 'iec104'

            server_ip = self.get_value('UDP', 'server_ip')
            server_port = int(self.get_value('UDP', 'server_port'))
            t1 = updataThreading(url, params, server_ip, server_port)
            t1.start()
            
        else:
            print('数据匹配不上')
        

if __name__ == "__main__":
    try:
        client = iec104_tcp_client('master') #主机
        client.start()
    except Exception as e:
        client = iec104_tcp_client('slave')  #备机
        client.start()
        pass
