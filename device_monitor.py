# coding=utf-8
# 设备异常监控
import datetime, time

import wx, threading
import wx.lib.pubsub.pub  # python3
from wx.lib.pubsub import pub
from wx.lib.pubsub import setupkwargs
import nilmd_utils, common_class

path = 'D:/Service/libview/ADSP-CM419F/Software-Development-Tools/IAR_setup/Analog Devices/ADSP-CM40x/CM403F_CM408F_EZ-KIT/examples/HAE/ADC_HAE_App/'
app = None
cacheFileName = '_cache_a.txt'  # 默认本地磁盘缓存文件名称
currentCache = cacheFileName
currentTime = ''
muityCache = True  # 多缓存
allData = False
debug = False


class MyTestEvent(wx.PyCommandEvent):  # 1 定义事件
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.eventArgs = ""

    def GetEventArgs(self):
        return self.eventArgs

    def SetEventArgs(self, args):
        self.eventArgs = args


myEVT_MY_TEST = wx.NewEventType()  # 2 创建一个事件类型
EVT_MY_TEST = wx.PyEventBinder(myEVT_MY_TEST, 1)  # 3 创建一个绑定器对象


def decode(msg):
    if 1:
        return msg
    return msg.decode('utf-8').encode('gbk')


class MyThread(threading.Thread):
    def __init__(self, frame, period):
        threading.Thread.__init__(self);
        self.frame = frame
        self.period = period  # 取40个周期的数据

    def getTotalData(self, period):  # 取得电压相位对齐后的电流电压数据
        global currentTime, currentCache, cacheFileName
        f = open(path + currentCache)
        line = f.readline()
        n = 0
        device = common_class.Device()
        datas = []  # 所有数据
        irmsList = []
        vrmsList = []
        while line:
            if len(str(line)) < 10:
                datas.append(float(str(line)))
            else:
                datas.append(float(str(line)[0]))  # 只保留次数
            line = f.readline()
        f.close()
        while n < period:
            try:
                if allData:  # 包含电流电压功率
                    power = datas[1280 * (n + 1) + 1 + n * 3]  # 取出电流 ,现为功率
                    device.powerList.append(power)
                    tempList = datas[1280 * n + 1 + n * 3: 1280 * (n + 1) + 1 + n * 3]  # 取出单次的电流电压
                else:
                    power = datas[1 + n * 3]  # 取出电流 ,现为功率
                    device.powerList.append(power)
            except Exception as e:
                if muityCache:
                    if cacheFileName == '_cache_a.txt':
                        cacheFileName = '_cache_b.txt'
                    elif cacheFileName == '_cache_b.txt':
                        cacheFileName = '_cache_c.txt'
                    elif cacheFileName == '_cache_c.txt':
                        cacheFileName = '_cache_a.txt'
                    currentCache = currentTime + cacheFileName
                else:
                    pass
                return None
            if allData:
                for i in range(len(tempList)):
                    if i % 2 == 0:
                        irmsList.append(tempList[i])
                    else:
                        vrmsList.append(tempList[i])
            n += 1
        if allData:
            size = len(irmsList)
            print('size = ', size)
            allIrms = []
            allVrms = []
            for number in range(int(size / 640)):
                point = nilmd_utils.getZeroPhase(vrmsList, 10, 320, number)
                v = vrmsList[640 * number:640 * (number + 1)]
                i = irmsList[640 * number:640 * (number + 1)]
                allIrms.extend(i[point:point + 320])
                allVrms.extend(v[point:point + 320])
            device.irmsList.extend(allIrms)
            device.vrmsList.extend(allVrms)
        return device

    def run(self):
        while True:
            try:
                device = self.getTotalData(self.period)
                if device is None:
                    self.frame.OnCallBack(0)
                    time.sleep(1)
                    continue
                result = nilmd_utils.zuixiaoerchen(device.powerList)
                device.minSquareValue = result[0]
                count = 0
                # 风扇档位变化,值会发生变化,切换时的变化
                resultList = device.powerList
                maxValue = max(resultList)
                minValue = min(resultList)
                middleValue = (maxValue + minValue) / 2  # 中位数
                frontFlag = 0
                size = 4
                for i in range(len(device.powerList)):
                    if device.powerList[i] < 5 and i > (self.period - 5 - 1):  # 最后5次功率均小于5
                        count += 1
                    if i in range(size):  # 前4个值
                        if device.powerList[i] > middleValue:
                            frontFlag += 1
                sortList = sorted(device.powerList)

                if maxValue != 0 and minValue != 0:
                    m = (maxValue - minValue) / maxValue
                    n = (maxValue - minValue) / minValue
                    m = float('%.6f' % m)
                    n = float('%.6f' % n)
                    device.data = ' ==> data: ' + str(m) + ' <==> ' + str(n)
                if count >= 5:
                    device.status = 3  # 停止工作
                elif result[0] < -0.03:  # 异常
                    if debug:
                        print('异常值：' + str(result[0]))
                        print(device.powerList)
                    if frontFlag >= size:
                        device.status = 1  # 正常
                    else:
                        device.status = 0  # 不正常
                else:
                    if (sum(device.powerList) / self.period) < 10:  # 平均功率小于10,认为未运行
                        device.status = 3
                    else:
                        device.status = 1
                        # 卡住平稳后的判断
                        """
                        flag = False
                        if abs(m - n) < 0.001:
                            flag = True

                        if m < 0.1 and n < 0.1:
                            m = float(str(m)[0:4])
                            n = float(str(n)[0:4])

                        if flag and m - n != 0:
                            device.status = 0
                        """
                        if debug:
                            print(device.powerList)
                self.frame.OnCallBack(device)
            except Exception as e:
                self.frame.OnCallBack(str(e.args))
                pass
        pass


class MyFrame(wx.Frame):
    def __init__(self, period=40):
        if 1:
            # wx.Frame.__init__(self, None, -1,title="非侵入式电力监测".decode('utf-8'), size=(1366,768),pos=(0,0))
            wx.Frame.__init__(self, None, -1, title=decode("设备异常监测"), size=(1366, 768), pos=(0, 0))
        else:
            wx.Frame.__init__(self, None, -1, title=decode("设备异常监测"), size=(444, 333), pos=(300, 50))

        # self.SetBackgroundStyle(wx.BG_STYLE_ERASE)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        panel = wx.Panel(self, -1)
        self.bgImg = wx.Image("./icon/background.png", wx.BITMAP_TYPE_PNG)
        self.status = 100
        self.currentStatus = 99
        self.p = panel
        self.period = period
        self.titleColor = 'blue'
        self.fontNormal = wx.Font(16, wx.ROMAN, wx.NORMAL, wx.NORMAL)
        self.fontLarge = wx.Font(22, wx.ROMAN, wx.NORMAL, wx.NORMAL)
        # self.fontLarge = wx.Font(22,wx.DECORATIVE,wx.ITALIC,wx.BOLD)

        # 右边部分控件
        topBox = wx.BoxSizer()  # 默认水平尺寸器
        image = wx.Image("./icon/SmartHome.png", wx.BITMAP_TYPE_PNG)
        image = image.Scale(image.GetWidth() / 2, image.GetHeight() / 2)
        bmp = image.ConvertToBitmap()
        bmp = wx.StaticBitmap(panel, -1, bmp)
        bmp.SetBackgroundColour((255, 255, 255))
        topBox.Add(bmp, proportion=0, flag=wx.ALIGN_CENTER_HORIZONTAL, border=10)  # EXPAND标记确保组件扩展到分配的空间中

        bottomBox = wx.BoxSizer(wx.VERTICAL)  # 默认水平尺寸器

        self.tips = wx.StaticText(panel, 99, label=decode('系统运行中...'),size=(wx.EXPAND,-1),style = wx.ALIGN_CENTER|wx.ST_NO_AUTORESIZE)
        self.tips.SetFont(self.fontNormal)
        self.tips.SetForegroundColour(self.titleColor)
        self.tips.SetBackgroundColour(None)


        # line = wx.StaticText(panel,label='',size=(2,wx.EXPAND))
        # line.SetBackgroundColour('black')

        # bottomBox.Add(line,proportion=0,flag=wx.RIGHT,border=20)
        bottomBox.Add(self.tips, proportion=0, flag=wx.ALIGN_CENTER_HORIZONTAL)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add((-1, 50))  # 添加垂直的间距
        vbox.Add(topBox, proportion=0, flag=wx.ALIGN_CENTER_HORIZONTAL, border=10)
        vbox.Add((-1, 50))
        vbox.Add(bottomBox, proportion=1, flag=wx.EXPAND, border=10)

        panel.SetSizer(vbox)
        # 关闭事件
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        panel.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        # self.Bind(wx.EVT_SIZE,self.onSize)
        self.Bind(EVT_MY_TEST, self.OnHandle)  # 4绑定事件处理函数
        self.Bind(wx.EVT_CLOSE, self.OnFormClosed, self)
        # self.startBtn.Bind(wx.EVT_BUTTON, self.onClickBtn)
        pub.subscribe(self.updateView, "update")  # python2 为Publisher python 为pub
        self.hjhTest()
        self.startMonitor()

    def updateView(self, msg):
        pass

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        # dc = wx.AutoBufferedPaintDC(self)

    def hjhTest(self):  # wxpython 4.0.4需要此操作才能显示
        # test
        # self.test = wx.StaticText(self.containerPanel, 990, label=decode('测试'), size=(0, 400))
        # self.container.Add(self.test, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=10)
        # test
        pass

    def startMonitor(self, period=40):
        t = MyThread(self, period)
        self.tips.SetLabel(decode('监测中...'))
        t.start()

    def OnFormClosed(self, event):
        self.Destroy()

    def OnHandle(self, event):  # 8 事件处理函数
        try:
            device = event.GetEventArgs()
            if isinstance(device, common_class.Device):
                if device.status == 1:
                    self.status = 1
                elif device.status == 3:  # 未运行
                    self.status = 3
                else:
                    self.status = 0
                wx.CallAfter(pub.sendMessage, "update", msg=device)  # python2不需要明确msg ,3.6 32位需要明确
            elif isinstance(device, int):
                self.status = -1
            else:
                self.status = -2

            if self.currentStatus == self.status:
                return
            else:
                if self.status == 1:
                    value = decode('设备正常工作中...' + str(device.minSquareValue) + device.data)
                elif self.status == 0:
                    value = decode('设备异常...' + str(device.minSquareValue) + device.data)
                elif self.status == -1:
                    value = decode('数据采集中...')
                elif self.status == -2:
                    value = decode('未获取到数据...')
                elif self.status == 3:
                    value = decode('设备已停止运行...')
                self.tips.SetLabel(value)
                self.currentStatus = self.status
        except Exception as e:
            pass

    def OnCallBack(self, param):
        evt = MyTestEvent(myEVT_MY_TEST, self.tips.GetId())  # 5 创建自定义事件对象
        evt.SetEventArgs(param)  # 6添加数据到事件
        self.GetEventHandler().ProcessEvent(evt)  # 7 处理事件

    def OnEraseBackground(self, evt):
        dc = evt.GetDC()
        if not dc:
            dc = wx.ClientDC(self)
            rect = self.GetUpdateRegion().GetBox()
            dc.SetClippingRect(rect)
        dc.Clear()
        self.StretchBackground(dc)

    def StretchBackground(self, dc):
        sz = self.GetClientSize()
        image = self.bgImg.Scale(sz.x, sz.y)
        bg_bmp = image.ConvertToBitmap()
        # bmp = wx.Bitmap("./icon/background.png")
        dc.DrawBitmap(bg_bmp, 0, 0)

    def onSize(self, evt):
        self.Refresh()


def getCurrentTime():
    global currentTime, cacheFileName, currentCache
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    day = datetime.datetime.now().day
    day = 19
    if month < 10:
        month = '0' + str(month)
    if day < 10:
        day = '0' + str(day)
    currentTime = str(year) + '-' + str(month) + '-' + str(day)
    currentCache = currentTime + cacheFileName


def work():
    global app
    getCurrentTime()
    if app is None:
        app = wx.PySimpleApp()
    frame = MyFrame(40)
    frame.Show(True)
    app.MainLoop()


if __name__ == "__main__":
    app = wx.App()
    work()
