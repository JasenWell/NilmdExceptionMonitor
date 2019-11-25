# coding=utf-8
# 工具类
import math, numpy


def decode(msg):
    if 1:
        return msg.decode('string_escape')
    return msg.decode('utf-8').encode('gbk')


def formatPrint(msg, data):  # 解决输出ascii问题
    if isinstance(data, int):
        print((msg + ('%d' % data)))
    elif isinstance(data, float):
        print((msg + ('%f' % data)))


def zuixiaoerchen(arrayY, picTitle=''):
    if len(arrayY) == 0:
        return [0, 0, 0]

    # 取得最大销量，作为纵坐标的峰值标准
    maxValue = max(arrayY)

    # 设置横坐标和纵坐标的值
    # def arange(start=None, stop=None, step=None, dtype=None)
    x = numpy.arange(1, len(arrayY) + 1, 1)

    # def array(p_object, dtype=None, copy=True, order='K', subok=False, ndmin=0)
    y = numpy.array(arrayY)

    # 第1個拟合，设置自由度為1 : (y = ax + b)
    z = numpy.polyfit(x, y, 1)
    # z: [  0.46428571  13.35238095]
    # 生成的多項式對象(y = ax + b)
    p = numpy.poly1d(z)
    # p: -0.1448x + 13.23
    if z[0] > 0:
        """
        # 绘制原曲线及 拟合后的曲线

        # 原曲线 , 设置颜色(蓝色)和标签
        pylab.plot(x, y, 'b^-', label='original sales growth')

        # 自由度为1的趋势曲线, 设置颜色(蓝色)和标签
        pylab.plot(x, p(x), 'gv--', label=f'y = {z[0]}x + {z[1]}')

        # 设置图表的title
        pylab.title(f"picTitle: {picTitle}")

        # 设置横坐标，纵坐标的范围 [xmin=0, xmax=16, ymin=0, ymax=30]
        pylab.axis([0, len(arrayY) + 1, 0, maxValue + 1])
        pylab.legend()

        # 保存成图片，需要提前创建文件夹 Growth，程序不会自动创建
        pylab.savefig(f"Growth/{picTitle}.png", dpi=96)

        # 清除图表设置，以防止曲线多次累计
        # 如果不清除，那么在这个程序运行起见，多次调用这个函数时，会不断将之前的曲线累计到新图片中
        pylab.clf()
        """

    return [z[0], z[1], maxValue]


def product(*args):
    """
    计算元组乘积
    :param args:
    :return:
    """
    sum = 1
    for n in args:
        sum = sum*n
    return sum


def doNormalize(irmsList, length=0):  # 归一化
    minV = min(irmsList)
    maxV = max(irmsList)
    tList = []
    for index in range(len(irmsList)):
        if maxV == minV:
            tList.append(0)
        else:
            t = (irmsList[index] - minV) / (maxV - minV)
            if length == 1:  # 格式化6位小数
                tList.append(float('%.6f' % t))
            else:
                tList.append(t)
    return tList


def getSTDValue(datas):
    total = sum(datas)
    size = len(datas)
    m = total / size
    total = 0
    for k in range(size):
        total = total + (datas[k] - m) ** 2
    std = math.sqrt(total / size)  # 标准差,不进行开方为方差
    return std


def getZeroPhasePoint(vrmsList, threshold, zeroPhaseValue, size, lastPoint, boardType=1):
    dataSize = 640
    if boardType:
        dataSize = 640
    point = -1
    for i in range(len(vrmsList)):
        if (i < lastPoint + 1):
            continue
        if (abs(zeroPhaseValue - vrmsList[i]) <= threshold):
            point = i  # 返回 0相位点
            break
    if (point == -1 or (point + size) > dataSize):  # 如果没有找到或者对应点后面的数据不足
        lastPoint = 0  # 重新从起点查找
        threshold = threshold + 200  # 阈值以200递增
        return getZeroPhasePoint(vrmsList, threshold, zeroPhaseValue, size, lastPoint)
    i = point + 1
    flag = True
    while i < point + 6:  # 判断后面5个点是否均大于起点值,统一处于上升沿
        if vrmsList[i] < vrmsList[point]:
            flag = False
            break
        i = i + 1
    if not flag:
        threshold = threshold + 200  # 阈值以200递增
        lastPoint = point
        return getZeroPhasePoint(vrmsList, threshold, zeroPhaseValue, size, lastPoint)
    # 这里是否需要查找此点后更接近于0相点的点，可以看此点后5点,与0相点差值最小即最优点，这里暂时不考虑
    return point


# 取得0相位点,valueList为电压数据
"""
:param size  完整周期的一半,320点
"""


def getZeroPhase(vrmsList, threshold, size, number=0, boardType=1):
    if boardType:
        vrmsList = vrmsList[640 * number:640 * (number + 1)]
    nlist = sorted(vrmsList)
    if (nlist[1] - nlist[0]) > 10000:  # 防止数据问题，电压变化很大
        value = (nlist[len(nlist) - 1] - nlist[1]) / 2
        zeroPhaseValue = nlist[1] + value  # 0相位估计值
    else:
        value = (nlist[len(nlist) - 1] - nlist[0]) / 2
        zeroPhaseValue = nlist[0] + value  # 0相位估计值

    if 0:
        formatPrint('0相电压：', zeroPhaseValue)

    return getZeroPhasePoint(vrmsList, threshold, zeroPhaseValue, size, 0, boardType)
