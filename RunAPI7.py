#
#
#   带水印  定制版
#
#


from PyQt5.QtWidgets import  QHBoxLayout, QVBoxLayout, QApplication, QWidget, QPushButton, QLabel,QLineEdit,QGroupBox,QListWidget,QListWidgetItem,QCheckBox,QDateTimeEdit
from PyQt5.QtMultimedia import QSound
from PyQt5.QtGui import QIcon,QPixmap,QFont
import PyQt5.QtCore as QtCore
import qdarkstyle
import sys
import queue
from fcoin3 import Fcoin
import random
import time
import datetime
import json
import sms_send
import re
import codecs


def catch_exceptions(t, val, tb):
    print(t,val,tb)
    old_hook(t, val, tb)

old_hook = sys.excepthook
sys.excepthook = catch_exceptions



class workThread(QtCore.QThread):
    logSignal = QtCore.pyqtSignal(dict)

    def __init__(self):
        super(workThread,self).__init__()

    def run(self):
        self.work()

    def work(self):
        global gIniQueue

        self.printLog('软件启动!')
        file=open('./ini.json')
        dic=json.loads( file.read())
        apikey=dic['apikey']
        apisecret=dic['apisecret']
        file.close()

        while gFlag:
            try:

                try:
                    ini=gIniQueue.get(block=False)
                except:
                    pass
                else:
                    str1=ini[0]
                    str2=ini[1]
                    num=ini[2]
                    str3=ini[3]
                    myTime=ini[4]
                    num2=ini[5]
                    buyFlag=ini[6]
                    tel=ini[7]
                    myTime2=ini[8]
                    num3=ini[9]


                    # test
                    self.printLog(str(ini))


                # file = open('./mytxt.txt', 'a+')
                fcoin = Fcoin()
                # 主号
                # fcoin.auth('', '')
                # 刷号
                fcoin.auth(apikey,apisecret,tel)
                # os.system('fskl.mp3')
                # 获取账户资产
                data=fcoin.get_balance()
                self.printLog('交易对：%s'%(str3))
                level= fcoin.get_market_depth('L20',str3)
                if ('data' not in data.keys()) or (not data['data']):
                    continue
                for i in data['data']:
                    if i['currency']==str1:
                        my_usdt=i['balance']
                        self.printLog(str1+'余额: '+my_usdt)
                    if i['currency']==str2:
                        my_ft=i['balance']
                        self.printLog(str2+'余额: '+my_ft)

                nowBids=level['data']['bids'][0]
                sumBids=0
                for i in range(0,len(level['data']['bids'])):
                    if (i%2)==0:
                        nowBids=level['data']['bids'][i]
                        self.printLog('本次价格：%s'%(nowBids))
                    else:
                        temp_Num2=sumBids
                        sumBids+=level['data']['bids'][i]
                        self.printLog('买盘 本次数量总和：%s  本次数量：%s 上次数量总和：%s  总数量：%s'%(sumBids,level['data']['bids'][i],temp_Num2,num3))
                        if sumBids>num3: #num3是输入的数
                            if i!=0:
                                sumBids=temp_Num2
                            self.printLog('本次数量总和：%s'%(sumBids))
                            if i>0:
                                nowBids=level['data']['bids'][i-1]
                                self.printLog('买盘本次价格：%s' % (nowBids))
                            break
                        elif sumBids==num3:
                            break

                nowAsks=level['data']['asks'][0]
                sumAsks=0
                for i in range(0,len(level['data']['asks'])):
                    if(i%2)==0:
                        nowAsks=level['data']['asks'][i]
                        self.printLog('本次价格：%s'%(nowAsks))
                    else:
                        temp_Num2=sumAsks
                        sumAsks+=level['data']['asks'][i]
                        self.printLog('卖盘 本次数量总和：%s  本次数量：%s  上次数量总和：%s  总数量：%s'%(sumAsks,level['data']['asks'][i],temp_Num2,num3)) #sumAsks+temp_Num2 这是什么意思
                        if sumAsks>num3: #num3是输入的数
                            if i!=0:
                                sumAsks=temp_Num2
                            self.printLog('本次数量总和：%s'%(sumAsks))
                            if i>0:
                                nowAsks=level['data']['asks'][i-1]
                                self.printLog('卖盘本次价格：%s' % (nowAsks))
                            break
                        elif sumAsks==num3:
                            break

                self.printLog('价格小数：%s'%(num2))
                nowResult=round((round(nowAsks,num2)+round(nowBids,num2))/2,num2)


                logStr=str(data)
                # self.printLog(logStr)
                # file.write(logStr+ '\n')


                nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                resultstr = fcoin.get_market_ticker(str3)
                logStr=str(resultstr)
                # self.printLog(logStr)
                # file.write(logStr+ '\n')
                wantstr = resultstr["data"]["ticker"]
                # a是买一价  b是卖一价
                a, b = wantstr[2], wantstr[4]
                # result = round(random.uniform(a, b), num2)
                result=nowResult
                logStr="random price is:" + str(result) + "now time:" + nowtime
                # self.printLog(logStr)
                # file.write(logStr+ '\n')

                #卖
                if num<float(my_ft):
                    sellop = fcoin.sell(str3, result, str(round(num,2)))
                    if (sellop is not None ) and (sellop['status']==0):
                        logStr=r'限价卖出成功 限价卖出%s个%s  卖出价格是%s  当前时间是%s'%(num,str2,result,nowtime)
                        self.printLog(logStr)
                    else:
                        self.printLog(sellop['msg'])

                elif (num>float(my_ft)) :

                    if buyFlag:
                        buyop = fcoin.buy_market(str3,round(float(num)*float(result)-float(my_ft)*float(result),2))
                        tempFlag=False
                        if  (buyop is not None) and (buyop['status']==3014):
                            tempFlag=True
                            temp_num = int(re.search(r'\d+$', buyop['msg']).group(0))
                            buyop = fcoin.buy_market(str3, str(temp_num))
                            #
                            # if (buyop is not None) and (buyop['status'] == 0):
                            #     # print(num-float(my_ft))*(result/float(my_usdt))
                            #     logStr = r'市价补仓买入成功 市价买入%s个%s的%s  当前时间是%s' % (
                            #     str(round((num - float(my_ft)) * b + (((num - float(my_ft)) * b) * 0.1), 2)), str1,
                            #     str2, nowtime)
                            #     self.printLog(logStr)
                            #     continue
                                # file.write(logStr+ '\n')
                            # else:
                            #     self.printLog(buyop['msg'])
                            #     continue

                        # buyop = fcoin.buy(str3, result,str(float(num-float(my_ft))*(result/float(my_usdt))))
                        # buyop = fcoin.buy(str3, b, str(round(num-float(my_ft)+((num-float(my_ft))*0.1),2)))
                        if (buyop is not None) and (buyop['status']==0):
                            # print(num-float(my_ft))*(result/float(my_usdt))
                            if not tempFlag:
                                logStr=r'市价补仓买入成功 市价买入%s个%s的%s  当前时间是%s'%(str(round(float(num)*float(result)-float(my_ft)*float(result),2)),str1,str2,nowtime)
                            else:
                                logStr=r'市价补仓买入成功 市价买入%s个%s的%s  当前时间是%s'%(temp_num,str1,str2,nowtime)
                            self.printLog(logStr)
                            continue
                            # file.write(logStr+ '\n')

                        else:
                            self.printLog(buyop['msg'])
                            continue
                            # time.sleep(60*?)
                        # buyrecord = buyop["data"]


                        # sellop = fcoin.sell(str3, result, str(num))
                        # if (sellop is not None) and (sellop['status']==0):
                        #     logStr = r'限价卖出成功 卖出%s个s%  卖出价格是%s  当前时间是%s' % (num, str2,result, nowtime)
                        #     self.printLog(logStr)
                        #     # file.write(logStr+ '\n')
                        # else:
                        #     self.printLog(sellop['msg'])
                        # if sellop:
                        #     sellrecord = sellop["data"]
                    else:
                        smsResult=sms_send.send('您当前交易对数量不足，请及时处理', tel, '44060')
                        #在这等15分钟
                        logStr = r'因为交易对数量不足程序已停止，30分钟后重新启动'
                        time.sleep(60 * 30)

                #买
                if num< float(my_usdt):
                    buyop = fcoin.buy(str3, result, str(round(num,2)))
                    if (buyop is not None) and (buyop['status']==0):
                        logStr=r'限价买入成功 限价买入%s个%s  买入价格是%s  当前时间是%s'%(num,str2,result,nowtime)
                        self.printLog(logStr)
                        # file.write(logStr+ '\n')
                    else:
                        self.printLog(buyop['msg'])

                    # buyrecord = buyop["data"]

                elif num> float(my_usdt):

                    if buyFlag:
                        # sell正常卖  sell_market非正常卖
                        # sellop = fcoin.sell_market(str3,  str(round(num-float(my_ft)+((num-float(my_ft))*0.1),2)))
                        sellop = fcoin.sell_market(str3, round((float(num)*float(result)-float(my_usdt)),2))
                        # sellop = fcoin.sell_market(str3, num+(num*result)*0.01)
                        tempFlag = False
                        if (sellop is not None) and (sellop['status'] == 3014):
                            tempFlag = True
                            temp_num = int(re.search(r'\d+$', sellop['msg']).group(0))
                            sellop = fcoin.buy_market(str3, str(temp_num))

                        # sellop =fcoin.sell(str3, round(a,num2), str(round(num-float(my_ft)+((num-float(my_ft))*0.1),2)))
                        if (sellop is not None) and (sellop['status']==0):
                            if not tempFlag:
                                logStr=r'市价补仓卖出成功 市价卖出%s个%s，当前时间是%s'%(str(round((float(num)*float(result)-float(my_usdt)))),str2,nowtime)
                            else:
                                logStr=r'市价补仓卖出成功 市价卖出%s个%s，当前时间是%s'%(temp_num+temp_num*0.1,str2,nowtime)
                            self.printLog(logStr)
                            continue
                            # file.write(logStr+ '\n')
                        else:
                            self.printLog(sellop['msg'])
                            continue

                        # if sellop:
                        #     sellrecord = sellop["data"]

                        # buyop = fcoin.buy(str3, result, str(num))
                        # if (buyop is not None) and (buyop['status']==0):
                        #     logStr = r'限价买入成功 限价买入%s个%s  买入价格是%s  当前时间是%s' % (num,str2, result, nowtime)
                        #     self.printLog(logStr)
                        #     # file.write(logStr+ '\n')
                        # else:
                        #     self.printLog(buyop['msg'])
                        # # buyrecord = buyop["data"]
                    else:
                        smsResult=sms_send.send('您当前交易对数量不足，请及时处理', tel, '44060')
                        logStr = r'因为交易对数量不足程序已停止，30分钟后重新启动'
                        time.sleep(60 * 30)
                time.sleep(myTime)

                # 获取订单列表
                if buyFlag:
                    rol = fcoin.list_orders(str3, 'submitted,partial_filled')
                    if ('data' not in rol.keys()) or (not rol['data']):
                        continue
                    lastTime=rol['data'][len(rol['data'])-1]['created_at']
                    lastTime=int(re.sub(r'\d{3}$','',str(lastTime)))
                    nowTime=int(time.time())


                    if not buyFlag:
                        if (nowTime-lastTime) >(myTime):
                            smsResult=sms_send.send('您当前有超过5分钟未成交的订单，请及时处理', tel, '44060')
                    else:
                        # 这里加not true的else
                        if buyFlag:
                            for p in rol["data"]:
                                if p["side"] == "buy":
                                    lastTime = p['created_at']
                                    lastTime = int(re.sub(r'\d{3}$', '', str(lastTime)))
                                    nowTime = int(time.time())
                                    if (nowTime-lastTime) >(myTime2):
                                        # 市价卖
                                        sellamount = round(float(p["amount"]) - float(p["filled_amount"]), 2)
                                        temptemp_result = fcoin.cancel_order(p["id"])
                                        if (temptemp_result is None) or (temptemp_result['status'] != 0):
                                            logStr = "检测到有超过" + str(
                                                myTime2) + "秒未完成订单 限价买入订单取消失败,因为已取消，现在时间是:" + nowtime
                                        else:
                                            logStr = "检测到有超过" + str(myTime2) + "秒未完成订单 限价买入订单取消成功，现在时间是:" + nowtime

                                        self.printLog(logStr)
                                        file.write(logStr + '\n')

                                        temptemp_result1 = fcoin.buy_market(str3, sellamount)
                                        if (temptemp_result1 is None) or (temptemp_result1['status']!=0):
                                            logStr="检测到有超过"+str(myTime2)+"秒未完成订单 限价买入订单取消失败,因为已取消，现在时间是:" + nowtime
                                        else:
                                            logStr="检测到有超过"+str(myTime2)+"秒未完成订单 限价买入订单取消成功，现在时间是:" + nowtime

                                        self.printLog(logStr)
                                        # file.write(logStr+ '\n')

                                elif p["side"] == "sell":
                                    lastTime = p['created_at']
                                    lastTime = int(re.sub(r'\d{3}$', '', str(lastTime)))
                                    nowTime = int(time.time())
                                    if (nowTime - lastTime) > (myTime2):
                                        # 市价卖
                                        sellamount = round(float(p["amount"]) - float(p["filled_amount"]), 2)
                                        temptemp_result=fcoin.cancel_order(p["id"])
                                        if (temptemp_result is None) or (temptemp_result['status']!=0):
                                            logStr="检测到有超过"+str(myTime2)+"秒未完成订单 限价卖出订单取消失败,因为已取消，现在时间是:" + nowtime
                                        else:
                                            logStr="检测到有超过"+str(myTime2)+"秒未完成订单 限价卖出订单取消成功，现在时间是:" + nowtime

                                        self.printLog(logStr)
                                        file.write(logStr+ '\n')

                                        temptemp_result=fcoin.sell_market(str3,sellamount)
                                        if (temptemp_result is None) or (temptemp_result['status']!=0):
                                            logStr="检测到有超过"+str(myTime2)+"秒未完成订单 市价卖出结果失败，因为已取消，现在时间是:" + nowtime
                                        else:
                                            logStr="检测到有超过"+str(myTime2)+"秒未完成订单  市价卖出结果成功，现在时间是:" + nowtime
                                        self.printLog(logStr)
                                        file.write(logStr+ '\n')

                                # elif ['side']=='buy':
                                #     lastTime = p['created_at']
                                #     lastTime = int(re.sub(r'\d{3}$', '', str(lastTime)))
                                #     nowTime = int(time.time())
                                #     if (nowTime - lastTime) > (myTime2):
                                #         # 市价买
                                #         sellamount = round(float(p["amount"]) - float(p["filled_amount"]), 2)
                                #         temptemp_result = fcoin.buy_market(str3, sellamount)
                                #         if (temptemp_result is None) or (temptemp_result['status'] != 0):
                                #             logStr = "检测到有超过" + str(myTime2) + "秒未完成订单 市价买入结果失败，因为已取消，现在时间是:" + nowtime
                                #         else:
                                #             logStr = "检测到有超过" + str(myTime2) + "秒未完成订单  市价买入结果成功，现在时间是:" + nowtime
                                #         self.printLog(logStr)
                                #         file.write(logStr + '\n')
                                        # file.write(logStr+ '\n')

                # isemprol = fcoin.list_orders('ftusdt', 'submitted,partial_filled')
                # print(isemprol)
                # time.sleep(myTime)
                # if len(isemprol["data"]) != 0:
                #     flag = False
                #     # os.system('fskl.mp3')
                # file.close()
                # # 执行完等3秒继续循
                # time.sleep(1)

            except Exception as e:
                raise e
                time.sleep(myTime)

        self.printLog('软件结束!')

    def printLog(self,str):
        self.logSignal.emit({'msg':str})


class timerThread(QtCore.QThread):
    startSignal=QtCore.pyqtSignal()
    endSignal=QtCore.pyqtSignal()

    def __init__(self):
        super(timerThread,self).__init__()

    def run(self):
        while True:
            if gTimeFlag and (gStartTime is not None) and (gEndTime is not None) and (not gWorkRunFlag):
                nowTime=datetime.datetime.now()
                if (nowTime>=gStartTime) and (nowTime<gEndTime) and (gFlag==False):
                    self.startSignal.emit()
                elif nowTime>=gEndTime:
                    self.endSignal.emit()
                    break
            time.sleep(0.5)


class OWO(QWidget):
    def __init__(self):
        super(QWidget,self).__init__()

        tempTime=datetime.datetime.now()
        tempTime=tempTime.strftime(r'%Y-%m-%d %H %M %S')
        self.logFile=codecs.open('./log/'+str(tempTime)+'日志'+'.html','w','utf-8')
        self.htmlPart1="""
                    <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Log</title>
            </head>
            <body>
                <table>
        """
        self.htmlPart2="""
            </table>
            </body>
            </html>
        """
        self.logFile.write(self.htmlPart1)


        vBox = QVBoxLayout()

        logG=QGroupBox()
        logG.setTitle('信息')
        hBox=QHBoxLayout()
        self.logList=QListWidget()
        hBox.addWidget(self.logList)
        logG.setLayout(hBox)


        iniG=QGroupBox()
        iniG.setTitle('设置')
        vBox2 = QVBoxLayout()

        hBox1 = QHBoxLayout()
        mylable1=QLabel('交易对1:')
        self.input1=QLineEdit()
        self.input1.setText('usdt')
        hBox1.addWidget(mylable1)
        hBox1.addWidget(self.input1)
        vBox2.addLayout(hBox1)

        hBox2 = QHBoxLayout()
        mylable2 = QLabel('交易对2:')
        self.input2 = QLineEdit()
        self.input2.setText('ft')
        hBox2.addWidget(mylable2)
        hBox2.addWidget(self.input2)
        vBox2.addLayout(hBox2)

        hBox3 = QHBoxLayout()
        mylable3 = QLabel('交易数量:')
        self.input3 = QLineEdit()
        self.input3.setText('10')
        hBox3.addWidget(mylable3)
        hBox3.addWidget(self.input3)
        vBox2.addLayout(hBox3)

        hBox4 = QHBoxLayout()
        mylable4 = QLabel('交易对:')
        self.input4 = QLineEdit()
        self.input4.setText('ftusdt')
        hBox4.addWidget(mylable4)
        hBox4.addWidget(self.input4)
        vBox2.addLayout(hBox4)

        hBox6=QHBoxLayout()
        mylable6=QLabel('交易时间:')
        self.input6=QLineEdit()
        self.input6.setText('10')
        hBox6.addWidget(mylable6)
        hBox6.addWidget(self.input6)
        vBox2.addLayout(hBox6)

        hBox7 = QHBoxLayout()
        mylable6 = QLabel('价格小数:')
        self.input7 = QLineEdit()
        self.input7.setText('6')
        hBox7.addWidget(mylable6)
        hBox7.addWidget(self.input7)
        vBox2.addLayout(hBox7)

        hBox11 = QHBoxLayout()
        mylable11 = QLabel('输入数值!:')
        self.input11 = QLineEdit()
        self.input11.setText('0')
        hBox11.addWidget(mylable11)
        hBox11.addWidget(self.input11)
        vBox2.addLayout(hBox11)

        hBox5=QHBoxLayout()
        self.input8 = QCheckBox()
        self.input8.setText('当余额不足是否市价增补仓')
        mylable7=QLabel('输入手机号:')
        self.input8.setChecked(True)
        self.input9 = QLineEdit()
        mylable9=QLabel('请输入多久取消订单(秒):')
        self.input10=QLineEdit()
        self.input10.setText('5')
        submitBtn=QPushButton('  提交  ')
        submitBtn.clicked.connect(self.submitFn)
        hBox5.addWidget(self.input8)
        hBox5.addSpacing(8)
        hBox5.addWidget(mylable7)
        hBox5.addWidget(self.input9)
        hBox5.addSpacing(8)
        hBox5.addWidget(mylable9)
        hBox5.addWidget(self.input10)
        hBox5.addStretch()
        hBox5.addWidget(submitBtn)
        # hBox5.addStretch()
        vBox2.addLayout(hBox5)

        iniG.setLayout(vBox2)

        vBox.addWidget(logG)
        vBox.addWidget(iniG)

        hBox7=QHBoxLayout()
        self.startBtn=QPushButton('  运行  ')
        self.startBtn.clicked.connect(self.startBtnClick)
        self.stopBtn=QPushButton('  停止  ')
        self.stopBtn.clicked.connect(self.stopBtnClick)
        mylable8=QLabel('JC软件工作室 微信:jcccccccc1991')
        font=QFont('微软雅黑')
        font.setPixelSize(18)
        mylable8.setFont(font)
        mylable8.setStyleSheet("""
            QLabel{color:#FF0000}
        """)
        hBox7.addWidget(self.startBtn)
        hBox7.addStretch()
        hBox7.addWidget(mylable8)
        hBox7.addStretch()
        hBox7.addWidget(self.stopBtn)

        hBox8 = QHBoxLayout()
        tempNowTime = QtCore.QDateTime.currentDateTime()
        self.timerC = QCheckBox()
        self.timerC.setText('启用定时运行   ')
        self.timerC.stateChanged.connect(self.timerClicked)
        startLab = QLabel('开始时间:')
        self.startTimeEdit = QDateTimeEdit()
        self.startTimeEdit.setDateTime(tempNowTime)
        self.startTimeEdit.setStyleSheet("""
                    QDateTimeEdit{width:110px}
                """)
        endLab = QLabel('<--> 结束时间:')
        self.endTimeEdit = QDateTimeEdit()
        self.endTimeEdit.setDateTime(tempNowTime)
        self.endTimeEdit.setStyleSheet("""
                    QDateTimeEdit{width:110px}
                """)
        hBox8.addWidget(self.timerC)
        hBox8.addWidget(startLab)
        hBox8.addWidget(self.startTimeEdit)
        hBox8.addWidget(endLab)
        hBox8.addWidget(self.endTimeEdit)
        hBox8.addStretch()

        vBox.addLayout(hBox8)
        vBox.addLayout(hBox7)
        self.stopBtn.setEnabled(False)

        icon=QIcon()
        icon.addPixmap(QPixmap('./JC.ico'),QIcon.Normal)
        self.setWindowIcon(icon)
        self.setLayout(vBox)
        self.setWindowTitle('JC全自动挖矿交易软件')
        self.resize(700,500)
        self.show()

    def submitFn(self,click):
        self.sendIni()

    def sendIni(self):
        global gIniQueue
        myList = [
            str(self.input1.text()),
            str(self.input2.text()),
            float(self.input3.text()),
            str(self.input4.text()),
            int(self.input6.text()),
            int(self.input7.text()),
            bool(self.input8.isChecked()),
            str(self.input9.text()),
            int(self.input10.text()),
            int(self.input11.text())
        ]
        gIniQueue.put(myList)

    def printLog(self,dic):
        item=QListWidgetItem(dic['msg'])
        self.logList.addItem(item)
        self.logList.setCurrentRow(self.logList.count()-1)
        self.logFile.write(r'<tr><td>'+dic['msg']+r'</td></tr>')
        if self.logList.count()>1000:
            item=self.logList.takeItem(0)
            del item

    def startBtnClick(self,click):
        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)
        if not gTimeFlag:
            self.runWorkTh()
        elif gTimeFlag:
            self.runTimerTh()

    def runTimerTh(self):
        global gStartTime
        global gEndTime
        gStartTime=self.startTimeEdit.dateTime().toPyDateTime()
        gEndTime=self.endTimeEdit.dateTime().toPyDateTime()
        self.timerTh=timerThread()
        self.timerTh.startSignal.connect(self.runWorkTh)
        self.timerTh.endSignal.connect(self.stopBtnClick)
        self.timerTh.start()
        self.printLog({'msg':'启动定时器'})

    def runWorkTh(self):
        global gFlag
        gFlag = True
        self.sendIni()
        self.myTh = workThread()
        self.myTh.logSignal.connect(self.printLog)
        self.myTh.start()
        self.printLog({'msg': '正在启动软件'})

    def stopBtnClick(self,click=None):
        global gFlag
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)
        gFlag = False
        self.printLog({'msg':'正在关闭软件'})

    def closeEvent(self, QCloseEvent):
        global gFlag
        self.logFile.write(self.htmlPart2)
        self.logFile.close()
        gFlag=False
        QCloseEvent.accept()

    def timerClicked(self,status):
        global gTimeFlag
        gTimeFlag=status


if __name__=='__main__':

    gTimeFlag = False
    gStartTime = None
    gEndTime = None

    gWorkRunFlag = False

    gFlag=False
    gIniQueue=queue.Queue()

    app=QApplication(sys.argv)


    owo=OWO()

    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    sys.exit(app.exec_())