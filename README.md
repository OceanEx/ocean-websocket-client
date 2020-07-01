- [Change Log](#Change-log)
- [Websocket testing program](#Websocket-testing-program)
   - [Introduction](#Introduction)
   - [Download](#Download)
- [User Guide](#Usage)
   - [Set up your account](#set-up-your-account)
   - [Load program](#load-program)
   - [Session up](#session-up)
   - [Disconnect and reconnect](#disconnect-and-reconnect)
   - [Enter command](#enter-command)
   - [Sending order](#sending-order)
   - [Callbacks](#callbacks)
- [Logger](#Logger)
- [Legal](#Legal)
   
# Websocket Testing Guide

## Change log

| Version            | Note              | date     |   
| ------------------ | ----------        | ---------|
| 0.0.0              | first version     |2020-03-04|
| 0.0.1              | add more index. change single cancel order to multiple cancel  orders   |2020-03-25|
| 0.0.2              | publish public version |2020-06-10|
| 0.0.3              | modify prod url to "wss://ws.oceanex.pro/ws/v1" |2020-07-01|

## Websocket testing program

### Introduction

**ws_client** is a mutli-threading websocket interactive Python client for communicating with OceanEx. It maintains the session status with the websocket server. It periodically resposones to server ping msg with pong msg back. The `ws_client` will not disconnect unless the exchange is down or users manually quit from the program. 

```
*********************************OCEANEX INTERACTIVE CLIENT*********************************************
*                                                                                                      *
*  Type cls or clear to clear the screen and display banner again.                                     *
*  Type banner or lhelp to display this 'banner' again.                                                *
*  Type h or ? or 'help'to get help on all commands for this Session.                                  *
*  Type shell or sh to enter shell. Enter ^D to exit shell.                                            *
*  Type q or Q to exit.                                                                                *
*                                                                                                      *
*                                                                                                      *
*                                                                                                      *
*  INPUT CHOICES:                                                                                      *
*        Choice:  1)  Authenticate                                                                     *
*        Choice:  2)  Get All Tickers                                                                  *
*        Choice:  3)  Get All Markets                                                                  *
*        Choice:  4)  Get All TradingFee                                                               *
*        Choice:  5)  Get Account                                                                      *
*        Choice:  6)  Enter New Order:MARKET_ID,SIDE,PRICE,VOLUME,ORD_TYPE                             *
*        Choice:  7)  Cancel Multiple Orders:OIDs                                                      *
*        Choice:  8)  Mass Cancel All                                                                   *
*        Choice:  9)  List Open Orders:MARKET_ID,ORD_TYPE                                              *
*        Choice: 10)  Display Order Details:OID                                                        *
*        Choice: 11)  Display History Order:OID                                                        *
*        Choice: 12)  Display All Hisotry Orders:MARKET_ID                                             *
*        Choice: 13)  Get Timestamp                                                                   *
*        Choice: 14)  Get OrderBook: MARKET_ID,LEVEL,PRECISION                                         *
*        Choice: 15)  Get K-line: MARKET_ID,LIMIT,PERIOD                                               *
*        Choice: 16)  Disconnect                                                                       *
*        Choice: 17)  Reconnect                                                                        *
*                                                                                                      *
*                                                                                                      *
********************************************************************************************************
Session up
Prompt ("stop" "q" "quit" "exit" to quit, h or ? or 'help' to Help):
```


### Download

The program can be downloaded from [here](https://github.com/OceanEx/ocean-websocket-client/blob/master/src/ws_client.py). This Python program is compatible with Python 2.7.x and Python 3.x.


## User Guide

### Set up the exchange account

Please make sure you have modified account settings based your own environment. To obtain `userid` and `apikid`, please enable API trading in OceanEx and follow the official instructions.

```
# user info
userid = "ID4XXXXXX"
apikid = "KIDXXXXXX"

# prod url
url = "wss://ws.oceanex.pro/ws/v1"
```

Make sure your **key.pem** file is under same directory where you run this program. The program has currently hard coded the file location as below: 

```
def authenticate
...
   with open("key.pem", "r") as private_file:
...
```

## Load program
Run the following command in any shell environment. The logs will be collected in `ws_client.log`
```
python ws_client.py 
```

or check command 
```
python ws_client.py --help
Usage: ws_client.py [options]

Options:
  -h, --help            show this help message and exit
  -l LOGLEVEL, --logLevel=LOGLEVEL
                        [l]og Level for ws_client.py, logs
                        ws_client.log default: INFO or info other
                        Option: DEBUG/debug, WARN/warn, ERROR/ error

```


### Session up
Once the program is started, it automatically builds up a session with OceanEx. A separate thread will start as inbound messages received and callback trigger. 

Make sure you see the session up message. Otherwise, please check the logs in `ws_client.log`. 
```
*        Choice: 16)  Disconnect                                                                       *
*        Choice: 17)  Reconnect                                                                        *
*                                                                                                      *
*                                                                                                      *
********************************************************************************************************
Session up
Prompt ("stop" "q" "quit" "exit" to quit, h or ? or 'help' to Help):
```


### Disconnect and reconnect 
You can quit the program by typing `stop`, `q`, `quit`, or `exit`. To disconnect and reconnect without killing program, use the following command: 

```
*        Choice: 16)  Disconnect                                                                       
*        Choice: 17)  Reconnect
```
```
Prompt ("stop" "q" "quit" "exit" to quit, h or ? or 'help' to Help):
> q
disconnecting...
Disconnected
Session Down
end....
```

### Enter command 
Follow the instruction and enter the command for testing. You may will see a prompt after typing from the inner thread callback. 
```
Prompt ("stop" "q" "quit" "exit" to quit, h or ? or 'help' to Help):
> Session up
2
received tickers info.
```


### Sending order 
Particularly, some APIs are private ones which need to be authenticated first. User can enter `1` to proceed with authentication. A user only needs to send authentication once for all private API operations. 
```
Prompt ("stop" "q" "quit" "exit" to quit, h or ? or 'help' to Help):
> 6

Not Authenticated. Please Authenticate first
Prompt ("stop" "q" "quit" "exit" to quit, h or ? or 'help' to Help):
> 1
Authenticated.
Prompt ("stop" "q" "quit" "exit" to quit, h or ? or 'help' to Help):
> 6
MARKET_ID,SIDE,PRICE,VOLUME,ORD_TYPE (example: vetusdt, buy, 0.75, 1000, limit)
> vetusdt, buy, 0.75, 1000, limit
*************************************
received order ack. order id: 31
*************************************
```

### Callbacks 

Each response will hit particularly callback function. For example, ```__on_order_ack```. If there is need to handle more incoming messages, please create more callback functions. Otherwise, undefined messages will hit ```__on_anymessage```

See logs example:
```
2020-03-05 12:47:06,155 (INFO, ws_client.py:205)  received Order Ack:
{
  "identifier": {
    "handler": "OrderHandler"
  },
  "message": {
    "action": "create",
    "code": 0,
    "data": {
      "avg_price": "0.0",
      "created_at": "2020-03-05T12:47:06Z",
      "created_on": 1583412426,
      "executed_volume": "0.0",
      "id": 32,
      "market": "vetusdt",
      "market_display_name": "VET/USDT",
      "market_name": "VET/USDT",
      "ord_type": "limit",
      "price": "0.75",
      "remaining_volume": "1000.0",
      "side": "bid",
      "state": "wait",
      "trades_count": 0,
      "volume": "1000.0"
    },
    "uuid": "6b5f552e-5edf-11ea-b613-7aa0b0f73a47"
  }
}
```

## Logger 
The logger is named as **ws_client.log** . It is created at the same directory where `ws_client.py` is running. It supports *debug, info, warn*. |

example:
```
2020-03-05 12:36:22,720 (INFO, ws_client.py:163)  connection established
2020-03-05 12:36:22,721 (INFO, ws_client.py:94)  receive welcome
2020-03-05 12:36:26,437 (INFO, ws_client.py:266)  Send authentication
2020-03-05 12:36:26,602 (INFO, ws_client.py:168)  account logged in:
{
  "identifier": {
    "handler": "AuthHandler"
  },
  "message": {
    "action": "login",
    "code": 0,
    "data": {
      "scopes": {
        "query": true,
        "sell/buy": true,
        "withdraw": true
      }
    },
    "uuid": "ee24b438-5edd-11ea-b613-7aa0b0f73a47"
  }
}
```


## Legal notice

**ws_client** is created by OceanEx R&D for  **the sole purpose of showing how to communicate with OceanEx APIs**. There is no scheduled maintenance and no warrenty comes with the code. **ws_client** is licensed under [the MIT License (MIT)  ](https://github.com/OceanEx/websocket-api-client/blob/master/LICENSE)
