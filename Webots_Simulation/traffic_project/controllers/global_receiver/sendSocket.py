'''
Author: lu 2231625449@qq.com
Date: 2024-04-26 02:23:13
LastEditors: lu 2231625449@qq.com
LastEditTime: 2024-04-27 01:57:47
FilePath: /webots_autodriving_drone/traffic_project_bridge/controllers/global_receiver/sendSocket.py
Description: 

Copyright (c) 2024 by ${git_name_email}, All Rights Reserved. 
'''
import socket
import os

class SocketPort():
    def __init__(self, ip, id):
        command = 'ifconfig enp108s0 192.168.1.1 netmask 255.255.255.0'
        sudo_password = '1210'
        sudo_command = f'echo {sudo_password} | sudo -S {command}'
        os.system(sudo_command)
        self.udp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sendAddress = (ip,id)
        
    def send(self, state):
        b = bytes(str(state)[1:-1] + "\n", 'utf-8')
        self.udp_socket.sendto(b,self.sendAddress)
        
    def sendStr(self, stateStr):
        b = bytes(stateStr, 'utf-8')
        self.udp_socket.sendto(b,self.sendAddress)

