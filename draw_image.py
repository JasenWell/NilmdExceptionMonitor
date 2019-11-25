# coding=utf-8
# 根据ADSP-CM408F开发板取得的数据绘图 by hjh 2018-7-23
import matplotlib.pyplot as plt
import nilmd_utils, common_class
import time

dataDir = './test_data/'  # 408f数据目录


def getTotalData(name, period):  # 取得电压相位对齐后的电流电压数据
    global dataDir
    f = open(dataDir + name)
    line = f.readline()
    n = 0
    device = common_class.Device()
    datas = []  # 所有数据
    irmsList = []
    vrmsList = []
    while line:
        if (len(str(line)) < 10):
            datas.append(float(str(line)))
        else:
            datas.append(float(str(line)[0]))  # 只保留次数
        line = f.readline()
    f.close()
    while (n < period):
        try:
            power = datas[1280 * (n + 1) + 1 + n * 3]  # 取出电流 ,现为功率
            device.powerList.append(power)
            tempList = datas[1280 * n + 1 + n * 3: 1280 * (n + 1) + 1 + n * 3]  # 取出单次的电流电压
        except Exception as e:
            pass

        for i in range(len(tempList)):
            if (i % 2 == 0):
                irmsList.append(tempList[i])
            else:
                vrmsList.append(tempList[i])
        n += 1

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


def drawPowerCompareImage(n, *yValues):
    goodValues, badValues = yValues
    xValues = [x for x in range(len(goodValues))]
    plt.figure(figsize=(12, 6), dpi=80)
    # 创建第一个画板
    # plt.figure(1)
    # 将第一个画板划分为2行2列组成的区块，并获取到第一块区域
    ax1 = plt.subplot(211)
    # 在第一个子区域中绘图
    plt.plot(xValues, goodValues, color='r')
    # plt.scatter(xValues,yValues,color="blue")
    # plt.scatter(xValues,yValues,marker="v",s=50,color="r")
    # 选中第二个子区域，并绘图

    xValues = [x for x in range(len(badValues))]
    ax2 = plt.subplot(212)
    plt.plot(xValues, badValues, color='blue')
    ax1.set_title("normal_power")
    ax2.set_title("unnormal_power")
    # plt.tight_layout()
    name = 'compare_12_power_'
    plt.savefig("./Image/" + name + str(time.time()) + ".png")
    pass


def drawSinglePowerImage(yValues):
    xValues = [x for x in range(len(yValues))]
    plt.figure(figsize=(12, 6), dpi=80)
    # 创建第一个画板
    # plt.figure(1)
    # 将第一个画板划分为2行2列组成的区块，并获取到第一块区域
    ax1 = plt.subplot(111)
    # 在第一个子区域中绘图
    plt.plot(xValues, yValues, color='b')
    # plt.scatter(xValues,yValues,color="blue")
    # plt.scatter(xValues,yValues,marker="v",s=50,color="r")
    # 选中第二个子区域，并绘图
    ax1.set_title("unnormal_power")

    # plt.tight_layout()
    name = 'compare_12_power_'
    plt.savefig("./Image/" + name + str(time.time()) + ".png")


def drawCompareImage():  # 画对比图
    rightList = ['current_2019-11-07_cache_12_3_right_3.txt', 'current_2019-11-07_cache_12_3_right_4.txt']
    badList = ['current_2019-11-07_cache_12_3_bad_3.txt', 'current_2019-11-07_cache_12_3_bad_4.txt']
    rightList = ['2019-11-18_cache_12_good3.txt', '2019-11-18_cache_12_good2.txt', '2019-11-18_cache_12_good.txt']
    badList = ['2019-11-18_cache_12_bad3.txt', '2019-11-18_cache_12_bad2.txt', '2019-11-18_cache_12_bad.txt']
    goodDeviceList = []
    badDeviceList = []
    period = 40  # 16个周期 的640点数
    for i in range(len(rightList)):
        goodDeviceList.append(getTotalData(rightList[i], period))
    for i in range(len(badList)):
        badDeviceList.append(getTotalData(badList[i], period))
    # drawSinglePowerImage(badDeviceList[0].powerList)
    for i in range(len(goodDeviceList)):
        goodDatas = goodDeviceList[i].powerList
        badDatas = badDeviceList[i].powerList
        print(nilmd_utils.zuixiaoerchen(goodDatas))
        print(nilmd_utils.zuixiaoerchen(badDatas))
        # drawPowerCompareImage(i, *(goodDatas,badDatas))
        print('std_good: '+ str(nilmd_utils.getSTDValue(goodDatas)))
        print('std_bad: ' + str(nilmd_utils.getSTDValue(badDatas)))
        #算数均值受电压变化，意义不大
        #简单几何平均数

        print('正常几何均数：',pow(nilmd_utils.product(*tuple(goodDatas)),1/len(goodDatas)))
        print('不正常几何均数：', pow(nilmd_utils.product(*tuple(badDatas)), 1 / len(badDatas)))
        pass
    if 1:
        return
    rightIrmsList = goodDeviceList[0].irmsList  # 电流
    rightVrmsList = goodDeviceList[0].vrmsList  # 电压

    badIrmsList = badDeviceList[0].irmsList  # 电流
    badVrmsList = badDeviceList[0].vrmsList  # 电压
    size = len(rightIrmsList)
    number = int(640 / 2)  # 每张图640点
    count = size / number  # 图的数量
    n = 0
    std = False  # 是否打印标准差

    while n < (count):
        yValues = rightIrmsList[number * n:number * (n + 1)]
        if (std):
            size = len(yValues)
            yValues = nilmd_utils.doNormalize(yValues, 1)
            std = nilmd_utils.getSTDValue(yValues)
            print('right_std = ', std)
            yValues = badIrmsList[number * n:number * (n + 1)]
            yValues = nilmd_utils.doNormalize(yValues, 1)
            std = nilmd_utils.getSTDValue(yValues)
            print('bad_std = ', std)
            n += 1
            continue
        xValues = [x for x in range(len(yValues))]
        plt.figure(figsize=(12, 6), dpi=80)
        # 创建第一个画板
        # plt.figure(1)
        # 将第一个画板划分为2行2列组成的区块，并获取到第一块区域
        ax1 = plt.subplot(221)
        # 在第一个子区域中绘图
        plt.plot(xValues, yValues, color='blue')
        # plt.scatter(xValues,yValues,color="blue")
        # plt.scatter(xValues,yValues,marker="v",s=50,color="r")
        # 选中第二个子区域，并绘图
        yValues = rightVrmsList[number * n:number * (n + 1)]
        xValues = [x for x in range(len(yValues))]
        ax2 = plt.subplot(222)
        plt.plot(xValues, yValues, color='blue')

        ax3 = plt.subplot(223)
        yValues = badIrmsList[number * n:number * (n + 1)]
        xValues = [x for x in range(len(yValues))]
        plt.plot(xValues, yValues, color='r')

        ax4 = plt.subplot(224)
        yValues = badVrmsList[number * n:number * (n + 1)]
        xValues = [x for x in range(len(yValues))]
        plt.plot(xValues, yValues, color='r')

        ax1.set_title("right_irms")
        ax2.set_title("right_vrms")
        ax3.set_title("bad_irms")
        ax4.set_title("bad_vrms")

        # plt.tight_layout()
        name = 'compare_12_'
        plt.savefig("./Image/" + name + str(n + 1) + ".png")
        n += 1


if __name__ == '__main__':
    drawCompareImage()
    pass
