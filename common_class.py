# coding=utf-8
# 一些公用类


class Device:
    def __init__(self):
        self.irmsList = []
        self.vrmsList = []
        self.powerList = []
        self.status = -1 # 0异常  1 正常
        self.minSquareValue = 10000 # 最小二乘法值
        self.data = ''
