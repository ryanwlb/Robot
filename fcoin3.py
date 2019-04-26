import hmac
import hashlib
import requests
import sys
import time
import base64
import json
from collections import OrderedDict
import sms_send


class Fcoin():
    def __init__(self,base_url = 'https://api.fcoin.com/v2/'):
        self.base_url = base_url

    def auth(self, key, secret,tel):
        self.key=bytes(key,'utf-8')
        self.secret=bytes(secret,'utf-8')
        self.tel=tel
        # self.key = bytes("610e1efa3b6944d3bea1259a70784edf",'utf-8')
        # self.secret = bytes("87112b80244642d09d60e6bcf6165016", 'utf-8')


    def public_request(self, method, api_url, **payload):
        """request public url"""
        r_url = self.base_url + api_url
        try:
            r = requests.request(method, r_url, params=payload,timeout=10)
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        if r.status_code == 200:
            return r.json()

    def get_signed(self, sig_str):
        """signed params use sha512"""
        sig_str = base64.b64encode(sig_str)
        signature = base64.b64encode(hmac.new(self.secret, sig_str, digestmod=hashlib.sha1).digest())
        return signature


    def signed_request(self, method, api_url, **payload):
        """request a signed url"""

        param=''
        if payload:
            sort_pay = sorted(payload.items())
            #sort_pay.sort()
            for k in sort_pay:
                param += '&' + str(k[0]) + '=' + str(k[1])
            param = param.lstrip('&')
        timestamp = str(int(time.time() * 1000))
        full_url = self.base_url + api_url

        if method == 'GET':
            if param:
                full_url = full_url + '?' +param
            sig_str = method + full_url + timestamp
        elif method == 'POST':
            sig_str = method + full_url + timestamp + param

        signature = self.get_signed(bytes(sig_str, 'utf-8'))

        headers = {
            'FC-ACCESS-KEY': self.key,
            'FC-ACCESS-SIGNATURE': signature,
            'FC-ACCESS-TIMESTAMP': timestamp

        }

        try:
            r = requests.request(method, full_url, headers = headers, json=payload,timeout=10)

            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
            print(r.text)
            result=r.json()
            # if result['msg']=='account balance insufficient':
                # result=sms_send.send("您当前余额不足，请及时处理",self.tel,'44060')
                # time.sleep(60*30)
            return r.json()
        if r.status_code == 200:
            return r.json()


    def get_server_time(self):
        """Get server time"""
        return self.public_request('GET','/public/server-time')['data']


    def get_currencies(self):
        """get all currencies"""
        return self.public_request('GET', '/public/currencies')['data']

    def get_symbols(self):
        """get all symbols"""
        return self.public_request('GET', '/public/symbols')['data']

    def get_market_ticker(self, symbol):
        """get market ticker"""
        return self.public_request('GET', 'market/ticker/{symbol}'.format(symbol=symbol))

    def get_market_depth(self, level, symbol):
        """get market depth"""
        return self.public_request('GET', 'market/depth/{level}/{symbol}'.format(level=level, symbol=symbol))

    def get_trades(self,symbol):
        """get detail trade"""
        return self.public_request('GET', 'market/trades/{symbol}'.format(symbol=symbol))

    def get_balance(self):
        """get user balance"""
        return self.signed_request('GET', 'accounts/balance')

    def list_orders(self, symbol, states):
        """get orders"""
        return self.signed_request('GET','orders', symbol=symbol, states=states)

    def create_order(self, **payload):
        """create order"""
        return self.signed_request('POST','orders', **payload)

    def buy(self,symbol, price, amount):
        """buy someting"""
        return self.create_order(symbol=symbol, side='buy', type='limit', price=str(price), amount=amount)

    def sell(self, symbol, price, amount):
        """buy someting"""
        return self.create_order(symbol=symbol, side='sell', type='limit', price=str(price), amount=amount)

    def get_order(self,order_id):
        """get specfic order"""
        return self.signed_request('GET', 'orders/{order_id}'.format(order_id=order_id))

    def cancel_order(self,order_id):
        """cancel specfic order"""
        return self.signed_request('POST', 'orders/{order_id}/submit-cancel'.format(order_id=order_id))

    def order_result(self, order_id):
        """check order result"""
        return self.signed_request('GET', 'orders/{order_id}/match-results'.format(order_id=order_id))
    def get_candle(self,resolution, symbol, **payload):
        """get candle data"""
        return self.public_request('GET', 'market/candles/{resolution}/{symbol}'.format(resolution=resolution, symbol=symbol), **payload)

    def sell_market(self, symbol, amount):
        """buy someting"""
        return self.create_order(symbol=symbol, side='sell', type='market', amount=amount)

    def buy_market(self, symbol, amount):
        """buy someting"""
        return self.create_order(symbol=symbol, side='buy', type='market', amount=amount)