#!-*- coding:utf-8 -*-
#
#
#   带水印
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
import re
import codecs
import bitmex
import sys
sys.path.insert(1, '/usr/local/lib/python3.6/site-packages/')


def catch_exceptions(t, val, tb):
    print(t,val,tb)
    old_hook(t, val, tb)

old_hook = sys.excepthook
sys.excepthook = catch_exceptions



class workThread(QtCore.QThread):
    logSignal = QtCore.pyqtSignal(dict)

    def __init__(self):
        super(workThread,self).__init__()
        self.printLog('软件启动!')

        file=open('./fcoin.json')
        fcoin_dic = json.loads(file.read())
        file.close()
        fcoin_apikey = fcoin_dic['apikey']
        fcoin_apisecret = fcoin_dic['apisecret']

        file=open('./bitmex.json')
        bit_dic = json.loads(file.read())
        file.close()
        bitmex_apikey = bit_dic['apikey']
        bitmex_apisecret = bit_dic['apisecret']

        self.fcoin = Fcoin()
        self.fcoin.auth(fcoin_apikey, fcoin_apisecret, '')

        print('a')
        self.bitcoin = bitmex.bitmex(test=False, api_key=bitmex_apikey, api_secret=bitmex_apisecret)
        print('b')
        self.way = 2
        self.number = 1000

        self.bit_buy_order = ''
        self.bit_sell_order = ''
        
        self.fcoin_symbol = 'btcusdt'
        self.bit_symbol = 'XBTUSD'

    def run(self):
        self.work()

    def get_price(self):
        data = self.bitcoin.OrderBook.OrderBook_getL2(symbol="XBTUSD", depth=1).result()
        for i in data[0]:
            if i['side'] == 'Sell':
                sell_price = i['price']
            elif i['side'] == 'Buy':
                buy_price = i['price']
        return sell_price, buy_price

    def one_way(self):
        print('单边')
        if self.bit_sell_order != '':
            #判断是否成交
            sell_result = self.bitcoin.Order.Order_getOrders(symbol=self.bit_symbol).result()
            for item in sell_result[0]:
                if item['orderID'] == self.bit_sell_order and item['ordStatus'] == 'Filled':
                    #已成交，下fcoin买单，获取卖一价
                    resultstr = self.fcoin.get_market_ticker(self.fcoin_symbol)
                    sell = resultstr["data"]["ticker"][4]
                    sell = round(float(sell) * self.fcoin_number, 2)
                    buy_op = self.fcoin.buy_market(self.fcoin_symbol, sell)
                    if (buy_op is not None) and (buy_op['status'] == 3014):
                        self.way = 1
                        return 
                    nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    logStr = r'fcoin市价补仓买入成功 市价买入%s个%s  当前时间是%s'%(sell, self.fcoin_symbol, nowtime)
                    self.printLog(logStr)

                    self.bit_sell_order = ''
                    return
                if item['orderID'] == self.bit_sell_order:
                    sell_price, buy_price = self.get_price()
                    if sell_price != item['price']:
                        #取消单
                        data = self.bitcoin.Order.Order_cancel(orderID=self.bit_sell_order).result()
                        if data[0][0]['ordStatus'] == 'Canceled':
                            self.printLog('当前订单价格变化未成交，取消单:%s 成功' % self.bit_sell_order)
                        self.bit_sell_order = ''
                        return
            return

        sell_price, buy_price = self.get_price()

        # bitmex下卖单
        sell_result = self.bitcoin.Order.Order_new(symbol=self.bit_symbol, orderQty=-1 * self.number, price=sell_price, execInst='ParticipateDoNotInitiate').result()
        self.bit_sell_order = sell_result[0]['orderID']

        nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logStr = r'bitmex限价卖出成功 限价卖出%s个%s  卖出价格是%s  当前时间是%s' % (self.number, self.bit_symbol, sell_price, nowtime)
        self.printLog(logStr)
        return

    def two_way(self):
        #双边挂单
        print('双边')

        sell_price, buy_price = self.get_price()

        if self.bit_sell_order != '' or self.bit_buy_order != '':
            #判断是否成交
            result = self.bitcoin.Order.Order_getOrders(symbol=self.bit_symbol, reverse=True, count=20).result()
            for item in result[0]:
                if item['orderID'] == self.bit_sell_order:
                    if item['ordStatus'] == 'Filled':
                        #已成交，下fcoin买单
                        resultstr = self.fcoin.get_market_ticker(self.fcoin_symbol)
                        sell = resultstr["data"]["ticker"][4]
                        sell = round(float(sell) * self.fcoin_number, 2)
                        buy_op = self.fcoin.buy_market(self.fcoin_symbol, sell)
                        if (buy_op is not None) and (buy_op['status'] == 3014):
                            self.way = 1
                            return 
                        nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        logStr = r'fcoin市价补仓买入成功 市价买入%s个%s  当前时间是%s'%(sell, self.fcoin_symbol, nowtime)
                        self.printLog(logStr)
                        self.bit_sell_order = ''
                    else:
                        if sell_price != item['price']:
                            #取消单
                            data = self.bitcoin.Order.Order_cancel(orderID=self.bit_sell_order).result()
                            if data[0][0]['ordStatus'] == 'Canceled':
                                self.printLog('当前订单价格变化未成交，取消单:%s 成功' % self.bit_sell_order)
                            self.bit_sell_order = ''

                if item['orderID'] == self.bit_buy_order:
                    if item['ordStatus'] == 'Filled':
                        #已成交，下fcoin卖单
                        sell = self.fcoin_number
                        sell_op = self.fcoin.sell_market(self.fcoin_symbol, sell)
                        if (sell_op is not None) and (sell_op['status'] == 3014):
                            self.way = 1
                            return
                        nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        logStr = r'fcoin市价补仓卖出成功 市价卖出%s个%s  当前时间是%s'%(self.number, self.fcoin_symbol, nowtime)
                        self.printLog(logStr)
                        self.bit_buy_order = ''
                    else:
                        if buy_price != item['price']:
                            #取消单
                            data = self.bitcoin.Order.Order_cancel(orderID=self.bit_buy_order).result()
                            if data[0][0]['ordStatus'] == 'Canceled':
                                self.printLog('当前订单价格变化未成交，取消单:%s 成功' % self.bit_sell_order)
                            self.bit_buy_order = ''

        nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self.bit_buy_order == '':
            # bitmex下买单
            buy_result = self.bitcoin.Order.Order_new(symbol=self.bit_symbol, orderQty=self.number, price=buy_price, execInst='ParticipateDoNotInitiate').result()
            self.bit_buy_order = buy_result[0]['orderID']
            logStr = r'bitmex限价买入成功 限价买入%s个%s  买入价格是%s  当前时间是%s' % (self.number, self.bit_symbol, buy_price, nowtime)
            self.printLog(logStr)

        if self.bit_sell_order == '':
            # bitmex下卖单
            sell_result = self.bitcoin.Order.Order_new(symbol=self.bit_symbol, orderQty=-1 * self.number, price=sell_price, execInst='ParticipateDoNotInitiate').result()
            self.bit_sell_order = sell_result[0]['orderID']
            logStr = r'bitmex限价卖出成功 限价卖出%s个%s  卖出价格是%s  当前时间是%s' % (self.number, self.bit_symbol, sell_price, nowtime)
            self.printLog(logStr)

        self.way = 2

    def work(self):
        global gIniQueue

        self.printLog('软件启动!')

        gFlag = True

        while gFlag:
            try:
                try:
                    ini=gIniQueue.get(block=False)
                except:
                    pass
                else:
                    '''
                    a=ini[0]
                    b=ini[1]
                    self.number=ini[2]
                    self.fcoin_number=ini[3]
                    myTime=ini[4]
                    
                    num2=ini[5]
                    buyFlag=ini[6]
                    tel=ini[7]
                    myTime2=ini[8]
                    '''
                a = 3
                b = 18320
                self.number = 1000
                self.fcoin_number=0.16
                myTime=19
                balance = self.fcoin.get_balance()
                #检测fcoin的余额
                if not balance or balance['status'] != 0:
                    print('ddd')
                    time.sleep(myTime)
                    continue
                print('balance')

                str1 = 'usdt'
                str2 = 'btc'

                for item in balance['data']:
                    if item['currency'] == str1:
                        my_usdt = float(item['balance'])
                        self.printLog(str1+'余额: %s' % my_usdt)
                    if item['currency'] == str2:
                        my_ft = float(item['balance'])
                        self.printLog(str2+'余额: %s' % my_ft)
                print('balance2')
                if self.way == 1:
                    print('way1')
                    if my_usdt > b and my_ft > a:
                        self.two_way()
                    else:
                        self.one_way()
                    time.sleep(myTime)
                    continue
                else:
                    print('way2')
                    self.two_way()
                time.sleep(myTime)
                continue

            except Exception as e:
                self.printLog(e)
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
        mylable1=QLabel('a:')
        self.input1=QLineEdit()
        self.input1.setText('3')
        hBox1.addWidget(mylable1)
        hBox1.addWidget(self.input1)
        vBox2.addLayout(hBox1)

        hBox2 = QHBoxLayout()
        mylable2 = QLabel('b:')
        self.input2 = QLineEdit()
        self.input2.setText('18282')
        hBox2.addWidget(mylable2)
        hBox2.addWidget(self.input2)
        vBox2.addLayout(hBox2)

        hBox3 = QHBoxLayout()
        mylable3 = QLabel('bitmex交易数量:')
        self.input3 = QLineEdit()
        self.input3.setText('1000')
        hBox3.addWidget(mylable3)
        hBox3.addWidget(self.input3)
        vBox2.addLayout(hBox3)

        hBox4 = QHBoxLayout()
        mylable4 = QLabel('fcoin交易数量:')
        self.input4 = QLineEdit()
        self.input4.setText('0.16')
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

        '''
        hBox7 = QHBoxLayout()
        mylable6 = QLabel('价格小数:')
        self.input7 = QLineEdit()
        self.input7.setText('6')
        hBox7.addWidget(mylable6)
        hBox7.addWidget(self.input7)
        vBox2.addLayout(hBox7)

        hBox5=QHBoxLayout()
        self.input8 = QCheckBox()
        self.input8.setText('当余额不足是否市价增补仓')
        mylable7=QLabel('输入手机号:')
        self.input8.setChecked(True)
        self.input9 = QLineEdit()
        mylable9=QLabel('请输入多久取消订单(秒):')
        self.input10=QLineEdit()
        self.input10.setText('5')
        '''

        submitBtn=QPushButton('  提交  ')
        submitBtn.clicked.connect(self.submitFn)

        '''
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
        '''

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
        self.setWindowTitle('Jc全自动挖矿交易软件')
        self.resize(700,500)
        self.show()

    def submitFn(self,click):
        self.sendIni()

    def sendIni(self):
        global gIniQueue
        myList = [
            float(self.input1.text()),
            float(self.input2.text()),
            float(self.input3.text()),
            str(self.input4.text()),
            int(self.input6.text()),
            #int(self.input7.text()),
            #bool(self.input8.isChecked()),
            #str(self.input9.text()),
            #int(self.input10.text())
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
        print("1")
        self.printLog({'msg': '正在启动软件1'})
        self.sendIni()
        self.printLog({'msg': '正在启动软件2'})
        print("2")
        self.myTh = workThread()
        self.printLog({'msg': '正在启动软件3'})
        print("3")
        self.myTh.logSignal.connect(self.printLog)
        self.printLog({'msg': '正在启动软件4'})
        print("4")
        self.myTh.start()
        self.printLog({'msg': '正在启动软件'})
        print("5")

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
