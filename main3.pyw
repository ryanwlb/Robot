
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from PIL import Image
import time
import re


import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import base64
import json
import ctypes

whnd = ctypes.windll.kernel32.GetConsoleWindow()
if whnd != 0:
    ctypes.windll.user32.ShowWindow(whnd, 0)
    ctypes.windll.kernel32.CloseHandle(whnd)

url = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic'
# access_token = '24.8cbf13b334f3e08f32b3a563f3038d2d.2592000.1533111233.282335-11474718'
# access_token = '24.db04e98433f6fe760c51c82c89d3320e.2592000.1533199400.282335-11480288'
header = {'Content-Type': 'application/x-www-form-urlencoded'}
# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# C:\Users\xg\Desktop\test1.jpg

class 百度(object):

    def __init__(self, ak, sk):
        self.ak = ak.strip()
        self.sk = sk.strip()
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id='+self.ak+'&client_secret='+self.sk
        response = requests.get(host)
        response_json = json.loads(response.text)
        self.access_token = response_json['access_token']

    def 百度文本识别(self, 图片地址):
        try:
            with open(图片地址, 'rb') as f:
                pic = f.read()
            img = base64.b64encode(pic)
            # data = json.dumps()
            data = {'image': img}
        except:
            return False
        try:
            response = requests.post(url+'?access_token='+ self.access_token, headers=header, data=data, verify=False, timeout=2)
            response_json = json.loads(response.text)
        except:
            return False
        try:
            result = ''
            for each in response_json['words_result']:
                result += each['words']
        except:
            return False
        return result

def main():
    escape = 1.01
    init_escape = 1.01
    add = 0
    flag = 1
    t_flag = 0
    tp_flag = 0
    str_temp = ''
    loser = 0
    ax_flag = 0
    mode = ''
    loser_count = 0
    # init_escape为初始逃跑值
    # flag默认值1，表示胜利；0时表示失败，程序进行对escape进行累加add值

    browser = webdriver.Chrome()
    browser.get('https://bc.game/crash')
    browser.set_window_size(853, 704)
    wait = WebDriverWait(browser, 10)
    with open(r'C:\bcgame.ini', 'r') as f:
        ini = f.read()
        ini = ini.replace('\r', '')
        ini = ini.replace('\n', '')
        ini = ini.replace(' ', '')
        ak = re.findall(r'ak=(.*?)sk=', ini)[0]
        sk = re.findall(r'sk=(.*?)add=', ini)[0]
        add = int(re.findall(r'add=(.*?)price=', ini)[0])
        price = re.findall(r'price=(.*?)mode=', ini)[0]
        mode = re.findall(r'mode=(.*?)end=', ini)[0]
    我的 = 百度(ak, sk)
    # price = input('请先登录，然后输入你的投注金额，一旦回车，程序会立即跑流程，想修改请重启（别改窗口大小）：')
    # escape = float(input('请输入逃跑值：'))

    # init_escape = escape
    # print(type(price), type(escape), type(add), type(init_escape))

    time.sleep(1)
    escape_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#crash-controls > div.form > div:nth-child(2) > div.form-input > div > input"))
                )
    escape_input.clear()
    chob = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#crash-controls > div.form > div:nth-child(1) > div.form-input.number-select > div.el-select > div > input"))
                )
    chob.click()

    time.sleep(1)
    cho = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body > div.el-select-dropdown.el-popper > div.el-scrollbar > div.el-select-dropdown__wrap.el-scrollbar__wrap > ul > li:nth-child("+mode+")"))
                )
    cho.click()

    price_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#crash-controls > div.form > div:nth-child(1) > div.form-input.number-select > div.el-input-number.is-controls-right > div > input"))
                )
    price_input.clear()
    price_input.send_keys(price)

    price_submit = wait.until(
        EC.presence_of_element_located
        ((By.CSS_SELECTOR, "#crash-controls > div.bet-button > button"))
    )
    count = 0
    str_result = ''

    Ftime = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    while True:
        try:
            with open('D:\output.txt', mode='w') as f:
                f.write(str_result)
            with open('D:\log' + str(Ftime) + '.txt', mode='w') as f:
                f.write(str_result)
            browser.get_screenshot_as_file('screenshot.png')

            im = Image.open("screenshot.png")
            x = 35
            y = 140
            w = 295
            h = 200
            region = im.crop((x, y, x + w, y + h))
            region.save("screenshot.png")
            time.sleep(0.01)
            result = 我的.百度文本识别('screenshot.png')
            # print(result)
            if not result:
                continue
            try:
                a = re.findall(r'[^a-zA-Z\d!@~\.]', result)
                a = ''.join(a)

                b = re.findall(r'[\d\.]', result)
                b = ''.join(b)
                # print(b)
                b = b.replace('\n', '')
                b = b.replace('\t', '')
                b = b.replace('\r', '')
            except:
                continue
            try:
                b = float(b)
            except:
                continue

            if a.find('开始') != -1:
                if tp_flag == 0:
                    tip = '本次投注%.5f,逃跑值%.2f' % (float(price), escape)
                    str_result = tip + '\n' + str_result
                    # print(tip)
                    tp_flag = 1
                    count += 1
                    Rtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    str_result = str('【第'+str(count)+'次，时间为'+str(Rtime)+'】') + str_result
                else:
                    pass
                if not ax_flag:
                    escape_input.clear()
                    escape_input.send_keys(str(round(escape, 2)))
                    price_submit.click()
                    # 这行代码负责按下
                    # print('我投注·', end='')
                    t_flag = 0
                    ax_flag = 1
                else:
                    pass

            if a.find('爆炸') != -1:
                ax_flag = 0
                if b > escape:
                    loser = 0

                    escape = init_escape
                    str_tip = '赢·爆值为%.2f|\n1和1.01累计爆了%d次' % (b, loser_count)

                    if str_tip != str_temp:
                        # print(str_tip)
                        str_result = str_tip + '\n' + str_result
                        str_temp = str_tip
                        str_tip = ''
                    else:
                        str_temp = str_tip
                        str_tip = ''
                    flag = 1
                    # 成功了
                else:
                    if t_flag == 0:
                        if not loser:
                            # escape += 1
                            loser = 1
                        escape += add
                        loser_count += 1
                        t_flag = 1
                    else:
                        pass
                    str_tip = '输·爆值%.2f·逃值修改为%.2f·也就是累加%d|\n1和1.01累计爆了%d次' % (b, escape, add, loser_count)

                    if str_tip != str_temp:
                        # print(str_tip)
                        str_result = str_tip + '\n' + str_result
                        str_temp = str_tip
                        str_tip = ''
                    else:
                        str_temp = str_tip
                        str_tip = ''
                        # print(str_tip)
                    flag = 0
                    # 失败了
                tp_flag = 0


            time.sleep(1.2)
        except:
            continue



    # result = 百度文本识别(r'C:\Users\xg\Desktop\test1.jpg')


if __name__ == "__main__":
    main()