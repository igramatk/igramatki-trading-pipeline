# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 21:53:31 2022

@author: Iulian
"""
from datetime import datetime, timedelta 
import pytz
import time
from threading import Timer
import sys
sys.path.append('E:\TWS API\source\pythonclient')
sys.path.append('E:\Trading\Code')
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
        self.AccountInfo = {}
        self.Portfolio = {}
        self.i = 0 #order counter - we need it to avoid duplicate order ids, because self.nextorderid does not update in time
        self.quantity = {}
        self.stock_by_orderid = {}
        
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
        
        for symbol in self.Portfolio:
            if symbol in self.choice:
                print(f'Ticker {symbol} is in choice. Keeping it in portfolio.')
                
            else:
              print(f'Selling ticker {symbol} from portfolio')  
              stock = Contract()
              stock.symbol = symbol
              stock.secType = self.Portfolio[symbol]['SecType']
              stock.exchange = "SMART"
              stock.primaryExchange = "NASDAQ"
              stock.currency = self.AccountInfo['Currency']
           
              order = Order()
              order.action = "SELL"
              order.totalQuantity = self.Portfolio[symbol]['Position']
              order.orderType = "MKT"
              
              self.placeOrder(self.nextOrderId+self.i, stock, order)
              self.i += 1
              
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
            order.totalQuantity = self.quantity[stock_to_buy]
            order.orderType = "MKT"
            # limitprice = round(fulldata.iloc[-1].loc[stock_to_buy] * 1.005, 2)
            # order.LmtPrice = limitprice
            # order.minTick = 0.00005
            # print(f'Buying {order.totalQuantity} shares of ticker {stock_to_buy} at limit price {limitprice}') 
                    
            self.stock_by_orderid[self.nextOrderId+self.i] = stock_to_buy
            self.placeOrder(self.nextOrderId+self.i, stock, order)
            self.i += 1            
    
    def buystocks(self):
            print(f'Buying chosen stock(s) {self.choice}. Time elapsed: {time.perf_counter()-time_start} seconds.')
            self.choice_remaining = [s for s in self.choice if not s in self.Portfolio] + [s for s in self.Portfolio if self.Portfolio[s]['Position']==0 and s in self.choice]
            self.nstocks_remaining = len(self.choice_remaining)
            print(f'Of these stocks, {self.choice_remaining} are not yet in the portfolio. Proceeding to buy these.')
            
            for s in self.choice_remaining:
                cashamount = float(self.AccountInfo['CashBalance']) / self.nstocks_remaining
                price = fulldata.iloc[-1].loc[s]
                self.quantity[s] = int(cashamount / price)
            
                self.buystock(s)
     
    def setstoploss(self):
        print(f'Setting stop-loss orders. Time elapsed: {time.perf_counter()-time_start} seconds.')
        for s in self.Portfolio:
            if self.Portfolio[s]['Position']>0:
                refprice = fulldata.iloc[-1][s] #today's price at algorithm start
                print(f'Reference price of stock {s} is {refprice}')
                
                if recession.iloc[-1].loc['in recession']: 
                    stoplossprice = round(refprice * self.sl_rec, 2)
                else:
                    stoplossprice = round(refprice * self.sl_norm, 2)               
                print('Setting up stop-loss order at price ',stoplossprice)
    
                stock = Contract()
                stock.symbol = s
                stock.secType = "STK"
                stock.exchange = "SMART"
                stock.primaryExchange = "NASDAQ"
                stock.currency = "USD"
                
                order = Order()
                order.action = "SELL"
                order.totalQuantity = self.Portfolio[s]['Position']
                order.orderType = "STP"
                order.auxPrice = stoplossprice
                order.tif = "GTC"
                
                self.placeOrder(self.nextOrderId+self.i, stock, order)
                self.i += 1
            
    def stop(self):
        self.reqAccountUpdates(False, "")
        self.done = True
        print(f'Disconnecting from TWS API. Time elapsed: {time.perf_counter()-time_start} seconds.')
        self.disconnect()

     
    def error(self, reqId, errorCode:int, errorString:str):
        print("ERROR ", reqId, errorCode, errorString)
        
        if errorCode == 201: #insufficient cash for initial margin
            s = self.stock_by_orderid[reqId]
            self.quantity[s] = int(self.quantity[s] * 0.99)
            self.buystock(s)
        
        if errorCode == 200: #stock contract is ambiguous
            s = self.stock_by_orderid[reqId]
            stock = Contract()
            stock.symbol = s
            stock.secType = "STK"
            stock.exchange = "SMART"
            stock.currency = "USD"
            self.reqContractDetails(reqId+1, stock)
            
      
    def updatePortfolio(self, contract: Contract, position: float, marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str):
        self.Portfolio[contract.symbol] = {"SecType": contract.secType, "Exchange": contract.exchange,
              "Position": position, "MarketPrice": marketPrice, "MarketValue": marketValue, "AverageCost": averageCost,
              "UnrealizedPNL": unrealizedPNL, "RealizedPNL": realizedPNL, "AccountName": accountName}
        print(f"{contract.symbol} updated in portfolio - position is now {position}. Account {accountName}")

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        self.AccountInfo[key] = val
        if key == 'CashBalance':
            print(f"Account {accountName} updated - {key} is now {val}")
        
    def updateAccountTime(self, timeStamp: str):
        self.AccountInfo["Time"] = timeStamp
        #print(f"Account updated at time {timeStamp}.")

    def accountDownloadEnd(self, accountName: str):
        print("AccountDownloadEnd. Account:", accountName)
      
    def orderStatus(self, orderId , status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        pass
        #print("OrderStatus. Id: ", orderId, ", Status: ", status, ", Filled: ", filled, ", Remaining: ", remaining, ", LastFillPrice: ", lastFillPrice)
        
    def openOrder(self, orderId, contract, order, orderState):
        pass
        #print("OpenOrder. ID:", orderId, contract.symbol, contract.secType, "@", contract.exchange, ":", order.action, order.orderType, order.totalQuantity, orderState.status)

    def execDetails(self, reqId, contract, execution):
        pass
        #print("ExecDetails. ", reqId, contract.symbol, contract.secType, contract.currency, execution.execId,
        #      execution.orderId, execution.shares, execution.lastLiquidity)

    def contractDetails(self, reqId, contractDetails):
        super().contractDetails(reqId, contractDetails)
        self.quirkycontract = contractDetails

    def contractDetailsEnd(self, reqId):
        super().contractDetailsEnd(reqId)
        print("ContractDetailsEnd. ReqId:", reqId)
        
        
def twsapi_main(ch, port, clientid, result, sl_norm=0.93, sl_rec=0.99):
    print('Starting TWS API activity')       
    tws = twsapi()
    
    print(f'Connecting to TWS API. Time elapsed: {time.perf_counter()-time_start} seconds.')
    tws.connect('127.0.0.1', port, clientid)  
    
    tws.choice = list(ch) #choice set of stocks to buy
    tws.nstocks = len(ch)
    tws.sl_norm = sl_norm #stop-loss factor (% of reference price) for normal times
    tws.sl_rec = sl_rec #stop loss factor for recessions (12-day STD of returns > 2)
            
    Timer(8, tws.selloff).start()
    Timer(38, tws.buystocks).start()
    Timer(68, tws.setstoploss).start()
    Timer(75, tws.stop).start() 
    
    print(f'Starting run thread. Time elapsed: {time.perf_counter()-time_start} seconds.')
    tws.run()
    
    result.append(tws)
    
    
def twsapi_test():
    tws2 = twsapi()
    tws2.connect('127.0.0.1', 7497, 18)
    tws2.quantity['KEYS'] = 10 
    Timer(2, tws2.buystock, ['KEYS']).start()
    Timer(7, tws2.setstoploss).start()
    Timer(9, tws2.stop).start() 
    tws2.run()
    return tws2


############global execution code
time_start = time.perf_counter()  #prevent code from breaking when running standalone subroutines 
tz = pytz.timezone('US/Eastern')
while True:
    
    nyt = datetime.now(tz)
    print (f'Time in New York is {nyt}')
    
    if nyt.weekday() < 5 and nyt.hour == 15 and nyt.minute == 42:      
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
            try:
                execfile("tradingMLprod.py")
                choice_retar = recommend[0]
            except:
                print('Error in training AR algorithm!')
            
            choice_bmacd = macd.iloc[-1].sort_values()
            algs = []
            
            Timer(0, twsapi_main, [choice_bmacd.index[:2], 7497, 3, algs, 0.998, 0.998]).start()
            Timer(1, twsapi_main, [choice_bmacd.index[:2], 7498, 4, algs, 0.99, 0.99]).start()       
            Timer(2, twsapi_main, [choice_bmacd.index[:2], 7499, 5, algs, 0.97, 0.97]).start()
            Timer(3, twsapi_main, [choice_bmacd.index[:2], 7495, 6, algs, 0.93, 0.93]).start()   
            Timer(4, twsapi_main, [choice_bmacd.index[:2], 7494, 7, algs, 0.5, 0.5]).start()   
            Timer(5, twsapi_main, [choice_bmacd.index[:2], 7496, 8, algs, 0.85, 0.85]).start()   
            
        break

    else:
        time.sleep(10)