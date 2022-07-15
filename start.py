from iec104client import *
import struct
import binascii
import requests
import json
import configparser
import os

#server_ip = '198.122.0.199'
server_ip = '127.0.0.1'
#client = iec104_tcp_client(server_ip)
#加载文件
def load_ini():
    file_name = os.path.dirname(__file__) + '\\config.ini'
    cf = configparser.ConfigParser()
    cf.read(file_name, encoding='utf-8')
    return cf

#获取value得值
def get_value(cf, section='SETUP', key='ip'):
    data = cf.get(section, key)
    return data

#获取键值对
def get_key_values(cf, section='SETUP'):
    return cf.items(section)
    
def bw_info_to_int(params):
    i = 0
    hex_str = ''
    while i < len(params):
        hex_str = params[i:i+2] + hex_str
        i = i + 2
    return int(hex_str, 16)

def parse_data(hex_str):
    info_len = hex_str[2:4]  #长度
    type = hex_str[12:14] #类型
    cause = hex_str[16:20] #原因
    info_list = {}
    if type == '0f':
        data = hex_str[24:]
        i = 0
        while i < len(data):
            addr = bw_info_to_int(data[i:i+6])
            value = bw_info_to_int(data[i+6:i+6+8])  #信息站四字节
            quality = int(data[i+6+8:i+6+8+2], 16)  #信息描述1字节
            info_list[addr] = {
                'addr': addr,
                'value': value,
                'quality': quality
            }
            i = i + 16
    return info_list

def submit_multi(lists, cn_names):
    url = 'http://wmmis-data.com/api/electricity/store_multi'
    i = 0
    params = {}
    input = []
    for item in lists:
        temp = {}
        temp['cn_name'] = cn_names[i]['name']
        temp['address'] = item['addr']
        temp['value'] = item['value']
        temp['actual_value'] = item['value'] * float(cn_names[i]['factor'])
        temp['quality'] = item['quality']
        temp['factor'] = cn_names[i]['factor']
        input.append(temp)
        i = i + 1

    params['input'] = json.dumps(input)
    response = requests.post(url, data=params)
    print('0000000000000')
    print(response.text)
    json_data = json.loads(response.text)
    
    print('111111111111')
    print(json_data)

hex_str = '68ca060004000f182500010001640065bb13000002640001000000010364000e000800020464000900000003056400b8570c00040664001a0000000507640075530500060864002600000007096400b8d31300080a640020000000090b64006e0908000a0c6400160000000b0d6400b8e401000c0e6400000000000d0f6400d2f000000e106400000000000f11640098460100101264000000000011136400cc9700001214640000000000131564006d750100141664000000000015176400f7b00000161864000000000017'
rtn1 = parse_data(hex_str)

hex_str = '682a080004000f04250001001964001ea60000001a640000000000011b6400ac3a0000021c64000000000003'
rtn2 = parse_data(hex_str)
key_values = rtn1 | rtn2
print(key_values)

sorted_keys = sorted(key_values)
sorted_values = []
for i in sorted_keys:
    sorted_values.append(key_values[i])
print(sorted_values)
cn_names = []
            
cf = load_ini()
tag = get_value(cf, 'TAGS', 'tag2')
#print(tag.split('|'))

k_v_s = get_key_values(cf, 'TAGS') 
#print(k_v_s)
for item in k_v_s:
    tmp = item[1].split('|')
    cn_names.append({
        'name': tmp[0],
        'factor': tmp[1]
    })

submit_multi(sorted_values, cn_names)
#print(cn_names)
