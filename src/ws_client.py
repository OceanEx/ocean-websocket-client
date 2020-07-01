# -*- coding: utf-8 -*-
# Copyright © 2020 Ocean IP Limited

# Permission is hereby granted, free of charge, to any person obtaining a copy of this ws_client 
# software and associated documentation files (the “Software”),to deal in the Software without restriction, 
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE, 
# INCLUDING BUT NOT LIMITED TO LEGAL OR ECONOMIC CONSEQUENCES STEMMING FROM THE REGULATORY CLASSIFICATION OF TOKENS AS EQUITY SECURITIES, 
# THE USE OF TRADING BOTS AND/OR LIQUIDITY MINING CAMPAIGN PARTICIPATION.

import json
import websocket
import uuid
import time
from time import sleep
import base64
import sys
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
import logging, optparse, os
from os import system, name
import readline
import threading
from threading import Thread, Lock

# set up readline
readline.parse_and_bind('tab: complete')
readline.parse_and_bind('set editing-mode vi')


# user info
userid = "ID4XXXXXX"
apikid = "KIDXXXXXX"

# prod url 
url = "wss://ws.oceanex.pro/ws/v1"

class OceanExWSListener(object):
    def __init__(self, endpoint, logger, userid=None, apikid=None):
        self.url = endpoint
        self.uid = userid
        self.kid = apikid
        self.logger = logger
        self.ws = websocket.WebSocketApp(self.url,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error)
        self.thread = Thread(target = self.ws.run_forever, args = (None , None , 60, 30))
        self.connected = False
        self.authenticated = False
    
####################### session ########################    
    def connect(self):
        self.connected = True
        self.thread.start()

    def reconnect(self):
        # clean up previous connection
        if self.connected == True:
            self.ws.close()
            self.thread.join() 

        self.thread = Thread(target = self.ws.run_forever, args = (None , None , 60, 30))
        self.connect()
        self.connected = True

    def disconnect(self):
        logger.debug("Websocket disconnecting")
        print('disconnecting...')
        self.ws.close()
        self.thread.join()

    def isAuthenticatd(self):
        return self.authenticated

#################### base send function #########################

    def send_json(self, data):

        if self.connected == False:
           print('not connected')
           self.logger.error('not connected')
           return 

        logger.debug("Send request {}".format(data))
        self.ws.send(json.dumps(data))

############################## call back ##########################################

    def __on_message(self, message):
        try:
            message = json.loads(message)
            logger.debug("Receive response: \n%s", json.dumps(message, sort_keys=True, indent=2, separators=(',', ': ')))
            if "type" in message and message['type'] == "ping":
                self.logger.debug("return pong")
                self.ws.send(json.dumps({"command": "pong"}))
                return
            if "type" in message and message['type'] == "welcome":
                self.logger.info("receive welcome")
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "AuthHandler":
                self.__on_login(message)
                return 
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "TickerHandler":
                self.__on_tickers(message)
                return 
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "MarketsHandler":
                self.__on_markets(message)
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "AccountHandler":
                self.__on_account(message)
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "ToolHandler" and message['message']['action'] == "timestamp":
                self.__on_timestamp(message)
                return 
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "FeeHandler" and message['message']['action'] == "trading_fee":
                self.__on_tradingfee(message)
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "OrderBookHandler":
                self.__on_orderbook(message)
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "KlineHandler":
                self.__on_k_line(message)
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "OrderHandler" and message['message']['action'] == "create" and message['message']['code'] == 0:
                self.__on_order_ack(message)
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "OrderHandler" and message['message']['action'] == "cancel" and message['message']['code'] == 0:
                self.__on_cancel_ack(message)
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "OrderHandler" and message['message']['action'] == "clear" and message['message']['code'] == 0:
                self.__on_mass_order_cancelled(message)
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "OrderHandler" and message['message']['action'] == "cancel" and message['message']['code'] != 0:
                self.__on_cancel_rejected(message)
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "OrderHandler" and message['message']['action'] == "index":
                self.__on_list_open_orders(message)
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "OrderHandler" and message['message']['action'] == "show" and message['message']['code'] == 0:
                self.__on_order_info(message)
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "OrderHistoryHandler" and message['message']['action'] == "show" and message['message']['code'] == 0:
                self.__on_history_order_info(message)
                return
            elif "handler" in message['identifier'] and message['identifier']['handler'] == "OrderHistoryHandler" and message['message']['action'] == "index" and message['message']['code'] == 0:
                self.__on_all_history_order_info(message)
                return
            else:
                self.__on_anymessage(message)
                return
                
        except Exception as E:
            self.logger.error(e)

    def __on_error(self, error):
        logger.error("Websocket encounter error: {}".format(error))

    def __on_close(self):
        self.connected = False
        self.authenticatd = False
        print('Disconnected')
        print('Session Down')
        logger.info("Websocket close")

    def __on_open(self):
        print('Session up')
        logger.info("connection established")

    def __on_login(self, data):
        self.authenticated = True
        print('Authenticated.')
        logger.info("account logged in:\n%s ", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def print_to_console(self, data):
        print(json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_tickers(self, data):
        print('received tickers info.')
        logger.info("received tickers info:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_markets(self, data):
        print('received markets info');
        logger.info("received markets info:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_account(self, data):
        print('received account info');
        logger.info("received account info:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_timestamp(self, data):
        print('received timestamp info');
        logger.info("received timestamp info:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_tradingfee(self, data):
        print('received trading fee info');
        logger.info("received trading fee info:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_orderbook(self, data):
        print('received Orderbook info');
        logger.info("received Orderbook info:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_k_line(self, data):
        print('received K-Line info');
        logger.info("received K-Line info:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_order_ack(self, data):
        print('*************************************');
        print("received order ack. order id: %s"%(data["message"]["data"]["id"]));
        print('*************************************');
        logger.info("received Order Ack:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_cancel_ack(self, data):
        print('*************************************');
        print("received order id %s cancelled."%(data["message"]["data"]));
        print('*************************************');
        logger.info("received Order Cancel Ack:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_cancel_rejected(self, data):
        print('*************************************');
        print("received order cancel err code [%s] id %s rejected."%(data["message"]["code"],data["message"]["data"]['ids']));
        print('*************************************');
        logger.info("received Order Cancel Rejected:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_mass_order_cancelled(self, data):
        print('*************************************');
        print("received mass order ids %s cancelled."%(data["message"]["data"]));
        print('*************************************');
        logger.info("received Order Cancel info:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_list_open_orders(self, data):
        print('received list open order info');
        logger.info("received List Open Order info:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_order_info(self, data):
        print('received order info');
        logger.info("received order info:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_history_order_info(self, data):
        print('received history order info');
        logger.info("received history order info:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_all_history_order_info(self, data):
        print('all received history order info');
        logger.info("all received history order info:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

    def __on_anymessage(self, data):
        print('*************************************');
        print("Unknown message \n%s"%(json.dumps(data, sort_keys=True, indent=2, separators=(',', ': '))))
        print('*************************************');
        logger.info("received Unknown message:\n%s", json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))

####################### signature #######################

    def _generate_signature(self, user_private_key, cur):
        private_key = serialization.load_pem_private_key(
            user_private_key.encode('ascii'),
            password=None,
            backend=default_backend()
        )
        path = "GET|/ws/v1|{}|".format(cur)
        sign = private_key.sign(
            path.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signature = base64.b64encode(sign).decode()
        return signature

##################### sender function ##################
    def authenticate(self, args=None):
        logger.info("Send authentication")
        if self.uid is None or self.kid is None:
            print("Please set uid and kid first")
            return
        with open("key.pem", "r") as private_file:
            user_private_key = private_file.read()
        cur = int(time.time() * 1000)
        auth = {
            "identifier": {"handler": "AuthHandler"},
            "command": "message",
            "data": {
                "action": "login",
                "uuid": str(uuid.uuid1()),
                "args": {},
                "header": {
                    "uid": self.uid,
                    "api_key": self.kid,
                    "signature": self._generate_signature(user_private_key, cur),
                    "nonce": cur,
                    "verb": "GET",
                    "path": "/ws/v1"
                }
            }
        }
        self.send_json(auth)

    def get_tickers(self, args=None):
        if args is None:
            args = {}
        self.logger.debug("Get tickers")
        markets = []
        markets.append('vetusdt')
        args = {'markets': markets}
        data = {
            "identifier": {"handler": "TickerHandler"},
            "command": "message",
            "data": {
                "action": "index", "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def get_markets(self, args=None):
        if args is None:
            args = {}
        self.logger.debug("Get all markets")
        data = {
            "identifier": {"handler": "MarketsHandler"},
            "command": "message",
            "data": {
                "action": "index",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def get_timestamp(self, args=None):
        if args is None:
            args = {}
        self.logger.debug("Get timestamp")
        data = {
            "identifier": {"handler": "ToolHandler"},
            "command": "message",
            "data": {
                "action": "timestamp",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def get_tradingfee(self, args=None):
        if args is None:
            args = {}
        self.logger.debug("Get All Trading Fee")
        data = {
            "identifier": {"handler": "FeeHandler"},
            "command": "message",
            "data": {
                "action": "trading_fee",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def get_account(self, args=None):
        if self.authenticated == False:
           print('\nNot Authenticated. Please Authenticate first')
           self.logger.error('not authenticated')
           return 
        if args is None:
            args = {}
        self.logger.debug("Get Account")
        data = {
            "identifier": {"handler": "AccountHandler"},
            "command": "message",
            "data": {
                "action": "index",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def get_orderbook(self):
        args = input('MARKET_ID,LEVEL,PRECISION (example: vetusdt, 2, 6)\n> ')
        args = args.replace(' ', '')
        args = args.split(",")
        if len(args) != 3:
            print('ERROD: Expected 3 args but received %d' % (len(args)))
            return
        args = {'market': args[0], 'level': int(args[1]), 'precision': int(args[2]) }

        args = json.loads(json.dumps(args)) 

        self.logger.debug("Get orderbook")
        data = {
            "identifier": {"handler": "OrderBookHandler"},
            "command": "message",
            "data": {
                "action": "index",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def get_k_line(self):
        args = input('MARKET_ID,LIMIT,PERIOD (example: vetusdt, 30, 5)\n> ')
        args = args.replace(' ', '')
        args = args.split(",")
        if len(args) != 3:
            print('ERROD: Expected 3 args but received %d' % (len(args)))
            return
        args = {'market': args[0], 'limit': int(args[1]), 'period': int(args[2]) }
        args = json.loads(json.dumps(args)) 

        self.logger.debug("Get K-line")
        data = {
            "identifier": {"handler": "KlineHandler"},
            "command": "message",
            "data": {
                "action": "index",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def create_new_order(self):
        if self.authenticated == False:
           print('\nNot Authenticated. Please Authenticate first')
           self.logger.error('not authenticated')
           return

        args = input('MARKET_ID,SIDE,PRICE,VOLUME,ORD_TYPE (example: vetusdt, buy, 0.75, 1000, limit)\n> ')
        args = args.replace(' ', '')
        args = args.split(",")

        if len(args) != 5:
            print('ERROD: Expected 5 args but received %d' % (len(args)))
            return
        args = {'market': args[0], 'side': args[1], 'price': float(args[2]), 'volume': float(args[3]), 'ord_type': args[4] }
        args = json.loads(json.dumps(args)) 

        if args is None:
            args = {}
        self.logger.debug("Create a new order")
        data = {
            "identifier": {"handler": "OrderHandler"},
            "command": "message",
            "data": {
                "action": "create",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def cancel_order(self):
        if self.authenticated == False:
           print('\nNot Authenticated. Please Authenticate first')
           self.logger.error('not authenticated')
           return 

        args = input('OID (example: 18)\n> ')
        args = args.replace(' ', '')
        args = args.split(",")

        if len(args) != 1:
            print('ERROD: Expected 1 arg but received %d' % (len(args)))
            return
        ids = []
        ids.append(int(args[0]))
        args = {'ids': ids}
        args = json.loads(json.dumps(args)) 

        if args is None:
            args = {}
        self.logger.debug("cancel a single order")
        data = {
            "identifier": {"handler": "OrderHandler"},
            "command": "message",
            "data": {
                "action": "cancel",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def cancel_multiple_orders(self):
        if self.authenticated == False:
           print('\nNot Authenticated. Please Authenticate first')
           self.logger.error('not authenticated')
           return 

        args = input('OIDs (example:18,19,23)\n> ')
        args = args.replace(' ', '')
        args = args.split(",")

        if len(args) < 1:
            print('ERROD: Expected more than 1 arg but received %d' % (len(args)))
            return
        ids = []
        
        for i in range(len(args)):
            print(args[i])
            ids.append(int(args[i]))

        args = {'ids': ids}
        args = json.loads(json.dumps(args)) 

        if args is None:
            args = {}
        self.logger.debug("cancel multiple orders")
        data = {
            "identifier": {"handler": "OrderHandler"},
            "command": "message",
            "data": {
                "action": "cancel",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def mass_cancel(self, args=None):
        if self.authenticated == False:
           print('\nNot Authenticated. Please Authenticate first')
           self.logger.error('not authenticated')
           return 

        args = {}

        self.logger.debug("mass cancel all orders")
        data = {
            "identifier": {"handler": "OrderHandler"},
            "command": "message",
            "data": {
                "action": "clear",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def list_open_orders(self):
        if self.authenticated == False:
           print('\nNot Authenticated. Please Authenticate first')
           self.logger.error('not authenticated')
           return 


        args = input('MARKET_ID, ORD_TYPE (example: vetusdt, limit)\n> ')
        args = args.replace(' ', '')
        args = args.split(",")

        if len(args) != 2:
            print('ERROD: Expected 2 args but received %d' % (len(args)))
            return
        args = {'market': args[0], 'ord_type': args[1] }
        args = json.loads(json.dumps(args)) 

        self.logger.debug("list all open orders")
        data = {
            "identifier": {"handler": "OrderHandler"},
            "command": "message",
            "data": {
                "action": "index",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def order_info(self):
        if self.authenticated == False:
           print('\nNot Authenticated. Please Authenticate first')
           self.logger.error('not authenticated')
           return 

        args = input('OID (example: 23)\n> ')
        args = args.replace(' ', '')
        args = args.split(",")

        if len(args) != 1:
            print('ERROD: Expected 1 args but received %d' % (len(args)))
            return
        args = {'id': args[0]}
        args = json.loads(json.dumps(args)) 

        if args is None:
            args = {}
        self.logger.debug("order info request")
        data = {
            "identifier": {"handler": "OrderHandler"},
            "command": "message",
            "data": {
                "action": "show",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def history_order_info(self):
        if self.authenticated == False:
           print('\nNot Authenticated. Please Authenticate first')
           self.logger.error('not authenticated')
           return 

        args = input('OID (example: 23)\n> ')
        args = args.replace(' ', '')
        args = args.split(",")

        if len(args) != 1:
            print('ERROD: Expected 1 args but received %d' % (len(args)))
            return
        args = {'id': args[0]}
        args = json.loads(json.dumps(args)) 

        self.logger.debug("history order info request")
        data = {
            "identifier": {"handler": "OrderHistoryHandler"},
            "command": "message",
            "data": {
                "action": "show",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

    def all_history_order_info(self):
        if self.authenticated == False:
           print('\nNot Authenticated. Please Authenticate first')
           self.logger.error('not authenticated')
           return

        args = input('MARKET_ID (example: vetusdt)\n> ')
        args = args.replace(' ', '')
        args = args.split(",")

        if len(args) != 1:
            print('ERROD: Expected 1 args but received %d' % (len(args)))
            return
        args = {'market': args[0]}
        args = json.loads(json.dumps(args)) 

        self.logger.debug("all history order info request")
        data = {
            "identifier": {"handler": "OrderHistoryHandler"},
            "command": "message",
            "data": {
                "action": "index",
                "uuid": str(uuid.uuid1()),
                "args": args
            }
        }
        self.send_json(data)

############################## class end ####################################
        
def start_wb_client(ows):
    ows.connect()


def banner():
    print ("*********************************OCEANEX INTERACTIVE CLIENT*********************************************");
    print ("*                                                                                                      *");
    print ("*  Type cls or clear to clear the screen and display banner again.                                     *");
    print ("*  Type banner or lhelp to display this 'banner' again.                                                *");
    print ("*  Type h or ? or 'help'to get help on all commands for this Session.                                  *");
    print ("*  Type q or Q to exit.                                                                                *");
    print ("*                                                                                                      *");
    print ("*                                                                                                      *");
    print ("*                                                                                                      *");
    print ("*  INPUT CHOICES:                                                                                      *");
    print ("*        Choice:  1)  Authenticate                                                                     *");
    print ("*        Choice:  2)  Get All Tickers                                                                  *");
    print ("*        Choice:  3)  Get All Markets                                                                  *");
    print ("*        Choice:  4)  Get All TradingFee                                                               *");
    print ("*        Choice:  5)  Get Account                                                                      *");
    print ("*        Choice:  6)  Enter New Order:MARKET_ID,SIDE,PRICE,VOLUME,ORD_TYPE                             *");
    print ("*        Choice:  7)  Cancel Multiple Orders:OIDs                                                      *");
    print ("*        Choice:  8)  Mass Cancel All                                                                  *");
    print ("*        Choice:  9)  List Open Orders:MARKET_ID,ORD_TYPE                                              *");
    print ("*        Choice: 10)  Display Order Details:OID                                                        *");
    print ("*        Choice: 11)  Display History Order:OID                                                        *");
    print ("*        Choice: 12)  Display All Hisotry Orders:MARKET_ID                                             *");
    print ("*        Choice: 13)  Get Timestamp                                                                    *");
    print ("*        Choice: 14)  Get OrderBook: MARKET_ID,LEVEL,PRECISION                                         *");
    print ("*        Choice: 15)  Get K-line: MARKET_ID,LIMIT,PERIOD                                               *");
    print ("*        Choice: 16)  Disconnect                                                                       *");
    print ("*        Choice: 17)  Reconnect                                                                        *");
    print ("*                                                                                                      *");
    print ("*                                                                                                      *");
    print ("********************************************************************************************************");

def clean_screen():
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')

def console():

    banner()

    # build session 
    ows = OceanExWSListener(url, logger, userid, apikid)
    start_wb_client(ows)
    
    while True:
        try:
            sleep(0.5)
            choice = input('Prompt ("stop" "q" "quit" "exit" to quit, h or ? or \'help\' to Help):\n> ')
            if choice in ['stop',"q", "quit","exit"]:
                ows.disconnect()
                break
            elif choice in ['?',"h", "help", "banner"]:
                banner()
            elif choice in ["cls", "clear"]:
                clean_screen()
            elif choice == '1':
                ows.authenticate()
            elif choice == '2':
                ows.get_tickers()
            elif choice == '3':
                ows.get_markets()
            elif choice == '4':
                ows.get_tradingfee()
            elif choice == '5':
                ows.get_account()
            elif choice == '6':
                ows.create_new_order()
            elif choice == '7':
                ows.cancel_multiple_orders()
            elif choice == '8':
                ows.mass_cancel()
            elif choice == '9':
                ows.list_open_orders()
            elif choice == '10':
                ows.order_info()
            elif choice == '11':
                ows.history_order_info()
            elif choice == '12':
                ows.all_history_order_info()
            elif choice == '13':
                ows.get_timestamp()
            elif choice == '14':
                ows.get_orderbook()
            elif choice == '15':
                ows.get_k_line()
            elif choice == '16':
                ows.disconnect()
            elif choice == '17':
                ows.reconnect()
            else:
                print('can not regonize choice')
                sleep(0.5)
                banner()
        except Exception as e:
            logger.error(e)

if __name__ == "__main__":

    parser = optparse.OptionParser()
    parser.add_option('-l', '--logLevel', dest="logLevel", default="INFO", help="[l]og Level for ws_client.py, logs ws_client_py.log default: INFO or info other Option: DEBUG/debug, WARN/warn, ERROR/ error",)

    options, remainder = parser.parse_args()

    #logger
    logLvl = options.logLevel
    loggerFile = os.path.splitext(__file__)[0]+".log"
    logger = logging.getLogger(loggerFile)
    if (logLvl == "INFO" or logLvl == "info"):
	    logger.setLevel(logging.INFO)
    elif (logLvl == "DEBUG" or logLvl == "debug"):
	    logger.setLevel(logging.DEBUG)
    elif (logLvl == "WARN" or logLvl == "warn"):
	    logger.setLevel(logging.WARNING)
    elif (logLvl == "ERROR" or logLvl == "error"):
	    logger.setLevel(logging.ERROR)
    handler = logging.FileHandler(os.path.splitext(__file__)[0]+".log", mode='a')
    formatter = logging.Formatter('%(asctime)s (%(levelname)s, %(filename)s:%(lineno)d)  %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console()
    print('end.... ')
