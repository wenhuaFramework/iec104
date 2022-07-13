#modbus_tk 读取浮点数的处理
#https://blog.csdn.net/u010161190/article/details/84730035?share_token=318af2c5-011e-4991-afef-36d27c974022&tt_from=copy_link&utm_source=copy_link&utm_medium=toutiao_android&utm_campaign=client_share?=modbus_tk
#用modbus_tk读取实物PLC的浮点数值，发现数据不正常。经分析后发现modbus_tk只是把PLC的返回值的两个字存储器按低位在前，高位在后的顺序转成浮点数(ABCD)。而实物PLC(信捷)，返回的数据是高位在前，低位在后(CDAB)。所以需要把高低位互换一下位置再转换。
#https://blog.csdn.net/lzl640/article/details/118722675

import struct
from ctypes import *

def ReadFloat(*args, reverse=False):
    for n,m in args:
        n,m = '%04x'%n,'%04x'%m    #%04x是一个格式说明符，它只对%运算符有意义。它指定要格式化的数字（在本例中，n）应该被格式化为十六进制
    if reverse:
        v = n + m
    else:
        v = m + n
    y_bytes = bytes.fromhex(v)   #fromhex函数，用来将16进制字符付串hexstr导入bytes对象（以二进制字节序列的形式记录的对象）
    y = struct.unpack('!f',y_bytes)[0] #按一定的格式取出某字符串中的子字符串，!表示我们要使用网络字节顺序解析，因为我们的数据是从网络中接收到的，在网络上传送的时候它是网络字节顺序的, unpack返回的是tuple
    y = round(y,6)  #方法返回浮点数y的四舍五入值，6表示从小数点位数
    return y

def WriteFloat(value,reverse=False):
    y_bytes = struct.pack('!f',value)
    # y_hex = bytes.hex(y_bytes)
    y_hex = ''.join(['%02x' % i for i in y_bytes])   #%02x表示宽度为2的16进制整数   %x是16进制，%02x是%x的补充，宽度为2，不够位数补0
    n,m = y_hex[:-4],y_hex[-4:]
    n,m = int(n,16),int(m,16)
    if reverse:
        v = [n,m]
    else:
        v = [m,n]
    return v

def ReadDint(*args,reverse=False):
    for n,m in args:
        n,m = '%04x'%n,'%04x'%m
    if reverse:
        v = n + m
    else:
        v = m + n
    y_bytes = bytes.fromhex(v)
    y = struct.unpack('!i',y_bytes)[0]
    return y

def WriteDint(value,reverse=False):
    y_bytes = struct.pack('!i',value)
    # y_hex = bytes.hex(y_bytes)
    y_hex = ''.join(['%02x' % i for i in y_bytes])
    n,m = y_hex[:-4],y_hex[-4:]
    n,m = int(n,16),int(m,16)
    if reverse:
        v = [n,m]
    else:
        v = [m,n]
    return v

def hex2float(s):
    i = int(s, 16)                   # convert from hex to a Python int
    cp = pointer(c_int(i))           # make this into a c integer
    fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
    return fp.contents.value 

def f2h(s):
    fp = pointer(c_double(s))
    cp = cast(fp, POINTER(c_longlong))
    return hex(cp.contents.value)


if __name__ == "__main__":
    #print(ReadFloat((20480, 17562)))  #1234.5
    #print(ReadFloat((15729, 16458)))
    #print(WriteFloat(3.16))
    #print(ReadDint((1734, 6970)))
    #print(WriteDint(456787654))
    
    print(hex2float('4469f99a'))
    #print(f2h(935.900024))