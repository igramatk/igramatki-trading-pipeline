# -*- coding: utf-8 -*-
"""
Created on Sat Oct 30 21:30:11 2021

@author: Iulian
"""
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum
from ibapi.order import Order
import pandas as pd
import threading
import multiprocessing
import time
from datetime import datetime

sp500 = pd.read_excel('E:/Trading/S&P500.xlsx')

d = pd.DataFrame([0])
h = pd.DataFrame(index = sp500['Symbol'], columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'wap', 'barCount'])
c = pd.DataFrame()
op = []
i = 0


def catch(obj, dfname):
   
    newdf = True
    
    if dfname in globals():
        if type(eval(dfname)) == pd.DataFrame:
            newrec = pd.DataFrame(obj, index=dfname.index[-1]+1)
            result = eval(dfname).append(newrec)
            newdf = False
            
    if newdf:
        result = pd.DataFrame(obj, index=[0])
    
    return result        


class twsapi(EWrapper, EClient):
    def __init__(self) :
        EWrapper.__init__(self)
        EClient.__init__(self, self)
        
    def error(self, reqId, errorCode:int, errorString:str):
        print("ERROR ", reqId, errorCode, errorString)
        
    def contractDetails(self, reqId:int, contractDetails):
        global c
        c = catch(contractDetails.__dict__,"c")
        
    def tickPrice(self, reqId, tickType, price:float, attrib):
        print("Tick price. TickerID:", reqId, "tickType:", TickTypeEnum.to_str(tickType), "Price:", price)
        global d 
        d[TickTypeEnum.to_str(tickType)] = price

    def tickSize(self, reqId, tickType, size):
        print("Tick size. TickerID:", reqId, "tickType:", TickTypeEnum.to_str(tickType), "Size:", size) 
        global d 
        d[TickTypeEnum.to_str(tickType)] = size
        
    def historicalData(self, reqId, bar):
        #print("historicalData:", bar)
        global h
        global i
        #h1 = catch(bar.__dict__, "h1")
        b = bar.__dict__
        h.iloc[i] = b
        i +=1
        
    def nextValidId(self, orderId):
        self.nextOrderId = orderId
        self.start()
        
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print("orderStatus:", locals())
        
    def openOrder(self, orderId, contract, order, orderState):
        print("openOrder:", locals())
        
    def execDetails(self, reqId, contract, execution):
        print("execDetails:", locals())
        
    def securityDefinitionOptionParameter(self, reqId, exchange, underlyingConId, tradingClass, multiplier, expirations, strikes):
        global op
        op.append(locals())
        #op = catch(locals(), "op")
        
    def updateAccountValue(self, key, val, currency, accountName):
        print(list(locals().values())[1:])
        
    def wshMetaData(self, reqId: int, dataJson: str):
         super().wshMetaData(reqId, dataJson)
         print("WshMetaData.", "ReqId:", reqId, "Data JSON:", dataJson)
         findata = dataJson
        
    def stop(self):
        self.done = True
        self.disconnect()
        
    def start(self):
        # aplopt = Contract()
        # aplopt.symbol = "AAPL"
        # aplopt.secType = "OPT"
        # aplopt.exchange = "SMART"
        # aplopt.currency = "USD"
        # aplopt.lastTradeDateOrContractMonth = "202112"
        
        #time.sleep(1)
        # self.reqContractDetails(1, aplopt)
        # self.reqSecDefOptParams(5, "AAPL", "", "STK", 265598)
        
        # self.reqAccountUpdates(True, "")
        
        oid = self.nextOrderId
        
        self.reqMarketDataType(4)

        #self.reqWshMetaData(37)
        
        #self.reqMktData(2, apl, "", False, False, [])

        today = datetime.now().strftime('%Y%m%d %X')

        for tkr in sp500['Symbol'][:8]:
            global s
            s = tkr
            apl = Contract()
            apl.symbol = s
            apl.secType = "STK"
            apl.exchange = "SMART"
            apl.currency = "USD"
               
            self.reqHistoricalData(3, apl, today, "1 D", "1 day", "TRADES", 0, 1, False, [])
            time.sleep(0.5) 
            
        # order = Order()
        # order.action = "BUY"
        # order.totalQuantity = 1
        # order.orderType = "LMT"
        # order.lmtPrice = 100
        
        # self.placeOrder(oid, apl, order)
        # self.cancelOrder(oid)


def main():
    tws = twsapi()
    #tws.nextOrderId = 0
    tws.connect('127.0.0.1', 7497, 13)  
    
    threading.Timer(3, tws.stop).start()
    tws.run()
    
    
if __name__ == '__main__':
    main()
    
    op  = pd.DataFrame(op)
