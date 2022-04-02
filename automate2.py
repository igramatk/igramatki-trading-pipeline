# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 21:53:31 2022

@author: Iulian
"""
from datetime import datetime, timedelta 
import pytz
import time
from threading import Timer
from ibapi.order import Order
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import yfinance as yf

class twsapi(EWrapper, EClient):
    
    def __init__(self) :
        EWrapper.__init__(self)
        EClient.__init__(self, self)
        ###
        global AccountInfo
        AccountInfo = {}
        global Portfolio
        Portfolio = {}
        global i #order counter - we need it to avoid duplicate order ids, because self.nextorderid does not update in time
        i = 0
        global quantity
        quantity = {}
        global stock_by_orderid
        stock_by_orderid = {}
        
    def nextValidId(self, orderId):
        self.nextOrderId = orderId
        print(f'Next valid order ID is {self.nextOrderId}')
        self.start()
        
    def start(self):       
        print(f'Cancelling all orders. Time elapsed: {time.perf_counter()-time_start} seconds.')
        self.reqGlobalCancel()

        print(f'Requesting account updates. Time elapsed: {time.perf_counter()-time_start} seconds.')
        self.reqAccountUpdates(True, "")

    def selloff(self):    
        print(f'Closing all positions. Time elapsed: {time.perf_counter()-time_start} seconds.')
        
        for symbol in Portfolio:
            if symbol in choice:
                print(f'Ticker {symbol} is in choice. Keeping it in portfolio.')
                
            else:
              print(f'Selling ticker {symbol} from portfolio')  
              stock = Contract()
              stock.symbol = symbol
              stock.secType = Portfolio[symbol]['SecType']
              stock.exchange = "SMART"
              stock.primaryExchange = "NASDAQ"
              stock.currency = AccountInfo['Currency']
           
              order = Order()
              order.action = "SELL"
              order.totalQuantity = Portfolio[symbol]['Position']
              order.orderType = "MKT"
              
              global i
              self.placeOrder(self.nextOrderId+i, stock, order)
              i += 1
              
    def buystock(self, stock_to_buy):
            print(f'Buying ticker {stock_to_buy}')  
            
            stock = Contract()
            stock.symbol = stock_to_buy
            stock.secType = "STK"
            stock.exchange = "SMART"
            stock.primaryExchange = "NASDAQ"
            stock.currency = "USD"
            
            order = Order()
            order.action = "BUY"
            order.totalQuantity = quantity[stock_to_buy]
            order.orderType = "MKT"
            
            global i
            global stock_by_orderid 
            stock_by_orderid[self.nextOrderId+i] = stock_to_buy
            self.placeOrder(self.nextOrderId+i, stock, order)
            i += 1            
    
    def buystocks(self):
            print(f'Buying chosen stock(s). Time elapsed: {time.perf_counter()-time_start} seconds.')
            choice_remaining = [s for s in choice if not s in Portfolio] + [s for s in Portfolio if Portfolio[s]['Position']==0 and s in choice]
            nstocks_remaining = len(choice_remaining)
            
            for s in choice_remaining:
                cashamount = float(AccountInfo['CashBalance']) / nstocks_remaining
                price = fulldata.iloc[-1].loc[s]
                global quantity
                quantity[s] = int(cashamount / price)
            
                self.buystock(s)
     
    def setstoploss(self):
        print(f'Setting stop-loss orders. Time elapsed: {time.perf_counter()-time_start} seconds.')
        for s in Portfolio:
            if Portfolio[s]['Position']>0:
                refprice = fulldata.iloc[-1][s] #today's price at algorithm start
                print(f'Reference price of stock {s} is {refprice}')
                
                if recession.iloc[-1].loc['in recession']: 
                    stoplossprice = round(refprice * 0.99, 2)
                else:
                    stoplossprice = round(refprice * 0.93, 2)               
                #1% stop loss if in recession, otherwise 7%
                print('Setting up stop-loss order at price ',stoplossprice)
    
                stock = Contract()
                stock.symbol = s
                stock.secType = "STK"
                stock.exchange = "SMART"
                stock.primaryExchange = "NASDAQ"
                stock.currency = "USD"
                
                order = Order()
                order.action = "SELL"
                order.totalQuantity = Portfolio[s]['Position']
                order.orderType = "STP"
                order.auxPrice = stoplossprice
                order.tif = "GTC"
                
                global i
                self.placeOrder(self.nextOrderId+i, stock, order)
                i += 1
            
    def stop(self):
        self.reqAccountUpdates(False, "")
        self.done = True
        print(f'Disconnecting from TWS API. Time elapsed: {time.perf_counter()-time_start} seconds.')
        self.disconnect()

     
    def error(self, reqId, errorCode:int, errorString:str):
        print("ERROR ", reqId, errorCode, errorString)
        
        if errorCode == 201: #insufficient cash for initial margin
            s = stock_by_orderid[reqId]
            global quantity
            quantity[s] = int(quantity[s] * 0.99)
            self.buystock(s)
        
        if errorCode == 200: #stock contract is ambiguous
            s = stock_by_orderid[reqId]
            stock = Contract()
            stock.symbol = s
            stock.secType = "STK"
            stock.exchange = "SMART"
            stock.currency = "USD"
            self.reqContractDetails(reqId+1, stock)
            
      
    def updatePortfolio(self, contract: Contract, position: float, marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str):
        global Portfolio
        Portfolio[contract.symbol] = {"SecType": contract.secType, "Exchange": contract.exchange,
              "Position": position, "MarketPrice": marketPrice, "MarketValue": marketValue, "AverageCost": averageCost,
              "UnrealizedPNL": unrealizedPNL, "RealizedPNL": realizedPNL, "AccountName": accountName}
        print(f"{contract.symbol} updated in portfolio - position is now {position}")

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        global AccountInfo
        AccountInfo[key] = val
        if key == 'CashBalance':
            print(f"Account updated - {key} is now {val}")
        
    def updateAccountTime(self, timeStamp: str):
        global AccountInfo
        AccountInfo["Time"] = timeStamp
        print(f"Account updated at time {timeStamp}.")

    def accountDownloadEnd(self, accountName: str):
        print("AccountDownloadEnd. Account:", accountName)
      
    def orderStatus(self, orderId , status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print("OrderStatus. Id: ", orderId, ", Status: ", status, ", Filled: ", filled, ", Remaining: ", remaining, ", LastFillPrice: ", lastFillPrice)
        
    def openOrder(self, orderId, contract, order, orderState):
        print("OpenOrder. ID:", orderId, contract.symbol, contract.secType, "@", contract.exchange, ":", order.action, order.orderType, order.totalQuantity, orderState.status)

    def execDetails(self, reqId, contract, execution):
        print("ExecDetails. ", reqId, contract.symbol, contract.secType, contract.currency, execution.execId,
              execution.orderId, execution.shares, execution.lastLiquidity)

    def contractDetails(self, reqId, contractDetails):
        super().contractDetails(reqId, contractDetails)
        global quirkycontract
        quirkycontract = contractDetails

    def contractDetailsEnd(self, reqId):
        super().contractDetailsEnd(reqId)
        print("ContractDetailsEnd. ReqId:", reqId)
        
        
def twsapi_main(ch, port, clientid):
    print('Starting TWS API activity')       
    tws = twsapi()
    
    print(f'Connecting to TWS API. Time elapsed: {time.perf_counter()-time_start} seconds.')
    tws.connect('127.0.0.1', port, clientid)  
    
    global choice
    choice = ch
    global nstocks
    nstocks = len(ch)
            
    Timer(5, tws.selloff).start()
    Timer(25, tws.buystocks).start()
    Timer(45, tws.setstoploss).start()
    Timer(50, tws.stop).start() 
    
    print(f'Starting run thread. Time elapsed: {time.perf_counter()-time_start} seconds.')
    tws.run()
    
    
def twsapi_test():
    tws2 = twsapi()
    tws2.connect('127.0.0.1', 7497, 18)
    global quantity
    quantity['KEYS'] = 0 
    Timer(2, tws2.buystock, ['KEYS']).start()
    Timer(7, tws2.setstoploss).start()
    Timer(9, tws2.stop).start() 
    tws2.run()
    

############global execution code
tz = pytz.timezone('US/Eastern')
while True:
    
    nyt = datetime.now(tz)
    print (f'Time in New York is {nyt}')
    
    if nyt.weekday() < 5 and nyt.hour == 15 and nyt.minute == 35:      
        #begin execution
        time_start = time.perf_counter()  
        print('Beginning execution')
        
        #check if US stock market is open by downloading financial data and checking if the last row is from the last 2 minutes
        testdata = yf.download(tickers=['AAPL'], start = nyt, interval = '1m')        
        if testdata.empty:
            print('The US stock market is closed. Execution aborted.')
        
        else:
            print('The US stock market is open. Proceeding')
            execfile("updatestockdata.py")
            execfile("gen_indicators.py")
            execfile("tradingMLprod.py")
            algs = []
            Timer(0, twsapi_main, [recommend[0].index[:1], 7497, 3, algs]).start()
            Timer(1, twsapi_main, [macd.iloc[-1].sort_values().index[:1], 7498, 4, algs]).start()       
            Timer(2, twsapi_main, [recommend[0].index[:4], 7499, 5, algs]).start()
            Timer(3, twsapi_main, [macd.iloc[-1].sort_values().index[:4], 7495, 6, algs]).start()   
            break
    
    else:
        time.sleep(30)