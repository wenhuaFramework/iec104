import time
import socket
import struct
import binascii

class iec104_tcp_client():
	_targetip = ''
	Tx=0
	Rx=0
	_port = 2404
	_socket = ''

	def __init__(self,targetip):
		self._targetip=targetip
		self.is_begin = False
		self.connect()
		self.start()

	def connect(self):
		#socket.AF_INET服务器之间网络通信
		#socket.SOCK_STREAM 流式socket , for TCP
		#协议编号（默认为0）
		self._socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)   #创建套接字
		self._socket.settimeout(5)  #设置套接字操作的超时期
		l_onoff=1          
		l_linger = 0	

		#设置给定套接字选项的值
		self._socket.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER, struct.pack('ii', l_onoff, l_linger))  #level,optname,value

		#连接到address处的套接字
		self._socket.connect((self._targetip,self._port))

	def quit(self):
		self._socket.close()

	def buildpacket(self, cmd):
		iec104_list = cmd.split(' ')
		iec104_hex_list = []   #[104, 4, 7, 0, 0, 0]  命令数组
		for item in iec104_list:
			temp = int(item, 16)
			iec104_hex_list.append(temp)

		packet = struct.pack("%dB" % (len(iec104_hex_list)), *iec104_hex_list) #通过struct转换成发送的十六进制串
		return packet

	def send(self, cmd):
		packet = self.buildpacket(cmd)
		self._socket.send(packet)
		time.sleep(0.015)
		try:
			print('000000000000000')
			output = self._socket.recv(1024)
			print('555555555555')
			print(output)
		except Exception as e:
			print('1111111111111')
			print(e)
			if (str(e).find('[Errno 104]')!=-1):
				#self._socket.close()
				print('2222222222222')
				return 'RST'
			else:
				#self._socket.close()
				print('333333333333')
				return 'Drop'
		#self._socket.close()
		return output

	#十进制接收序号
	def setRx(self):
		self.Rx=self.Rx+1
		if self.Rx > 65534:
			self.Rx = 1

	#十进制发送序号
	def getTx(self):
		self.Tx = self.Tx + 1
		if self.Tx > 65534:
			self.Tx = 1
		return self.Tx

	def start(self):
		self.is_begin = True
		while True:
			if self.is_begin:
				#1、发送启动帧，首次握手（U帧）680407000000
				cmd = "68 04 07 00 00 00"
				packet = self.buildpacket(cmd)
				self._socket.send(packet)
				#time.sleep(0.015)
				self.is_begin = False
				print('========发送启动帧68 04 07 00 00 00=========')
				
			try:
				#print('========try=========')
				output = self._socket.recv(1024)
				#print('5555555===output===55555')
				#print(output)
				hex_str = binascii.b2a_hex(output).decode('unicode_escape') #二进制（bytes）转换为十六进制（hex）
				print('========收到16进制报文=========')
				print(hex_str)

				#2、接收服务端响应的启动确认帧 68040B000000
				if hex_str == '68040b000000':
					print('connected')
					print('=========收到启动确认帧68 04 0b 00 00 00==========')
					print('=========发送总召帧68 0e 00 00 00 00 64 01 06 00 01 00 00 00 00 14==========')
					#3、发送总召帧 68 0E 00 00 00 00 64 01 06 00 01 00 00 00 00 14
					cmd = '68 0e 00 00 00 00 64 01 06 00 01 00 00 00 00 14'
					packet = self.buildpacket(cmd)
					self._socket.send(packet)
					#time.sleep(0.015)

				elif hex_str == '680e0000020064010700010000000014':
					#接收服务端返回的总召响应帧，跟总召帧只有传送原因不同
					print('========收到总召确认帧=========')
					#发送S帧
					#cmd = '68 04 01 00 02 00'  #应答
					#packet = self.buildpacket(cmd)
					#self._socket.send(packet)
				elif hex_str == '680443000000':
					print('ping')
					#接收U帧 测试帧  超过一定时间没有下发和上报时
					cmd = '68 04 83 00 00 00'  #应答U帧
					packet = self.buildpacket(cmd)
					self._socket.send(packet)
					print('======收到测试帧，应答U帧=======')
				elif hex_str == '680401000200':
					#接收S帧
					print('======接收到S帧======')
				elif hex_str == '681306000200098214000100010700A11000891500':  #类型9为例 68启动 13长度 06 00发送序号 02 00接收序号 09类型标识 82可变结构限定词 14 00传输原因（响应总召唤） 01 00公共地址 01 07 00信息体地址 A1 10遥测值（10A1） 00品质描述 89 15遥测值（1589） 00品质描述
					#接收YC帧
					print('======接收YC帧======')
					cmd = '680401000800'  #应答S帧
					packet = self.buildpacket(cmd)
					self._socket.send(packet)
					print('======应答S帧=======')
				elif hex_str == '680e0200020064010a00010000000014':
					#接收总召激活结束帧
					print('======接收总召激活结束帧=========')
					cmd = '68 04 01 00 04 00'  #应答S帧
					packet = self.buildpacket(cmd)
					self._socket.send(packet)
					print('========应答S帧=========')
				elif hex_str == '680e1000060065010700010000000045':
					#接收电度总召唤确认
					#68（启动符）0E（长度）10  00（发送序号）06  00（接收序号）65（类型标示）01（可变结构限定词）07  00（传输原因）01  00（公共地址）00 00 00（信息体地址）45（QCC）
					print('======接收电度总召唤确认=========')
					cmd = '68 04 01 00 04 00'  #应答S帧
					packet = self.buildpacket(cmd)
					self._socket.send(packet)
					print('========应答S帧=========')
				elif hex_str == '681a120006000f0205000100010c000000000000020c000000000001':
					#接收电度数据
					#68（启动符）1A（长度）12  00（发送序号）06  00（接收序号）0F（类型标示）02（可变结构限定词,有两个电度量上送）05  00（传输原因）01  00（公共地址）01 0C 00（信息体地址，从0X0C01开始第0号电度）00 00 00 00（电度值）00（描述信息）02 0C 00（信息体地址，从0X0C01开始第1号电度）00 00 00 00（电度值）01（描述信息）
					cmd = '68 04 01 00 04 00'  #应答S帧
					packet = self.buildpacket(cmd)
					self._socket.send(packet)
				elif hex_str == '680e1000060065010a00010000000045':
					#接收结束总召唤帧
					#68（启动符）0E（长度）14  00（发送序号）06  00（接收序号）65（类型标示）01（可变结构限定词）0a  00（传输原因）01  00（公共地址）00 00 00（信息体地址）45（QCC）
					print('======接收结束总召唤帧=========')
					cmd = '68 04 01 00 04 00'  #应答S帧
					packet = self.buildpacket(cmd)
					self._socket.send(packet)
					print('========应答S帧=========')
				else:
					print('=======接收其他帧=======')
					pass

			except Exception as e:
				print('111111=====Exception=====1111111')
				print(str(e))

	def stop(self):
		cmd = '68 04 13 00 00 00' #U帧停止 主站发送  子站回复：68 04 23 00 00 00

	def dianduTotal(self): #电度总召唤
		#68（启动符）0E（长度）04  00（发送序号）0E  00（接收序号）65（类型标示）01（可变结构限定词）06  00（传输原因）01  00（公共地址）00 00 00（信息体地址）45（QCC）
		cmd = '68 0e 04 00 0e 00 65 01 06 00 01 00 00 00 00 45'
		return cmd

			
