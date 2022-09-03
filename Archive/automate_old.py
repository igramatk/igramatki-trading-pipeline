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
        global buy 
        buy = True
        global stoplosssetup 
        stoplosssetup = True
        global i #order counter - we need it to avoid duplicate order ids, because self.nextorderid does not update in time
        i = 0
        global chosenStockBuyOrderId
        chosenStockBuyOrderId = 0
        
    def buystock(self):
            stock = Contract()
            stock.symbol = choice
            stock.secType = "STK"
            stock.exchange = "SMART"
            stock.currency = "USD"
            
            order = Order()
            order.action = "BUY"
            order.totalQuantity = quantity
            order.orderType = "MKT"
            
            global i
            global chosenStockBuyOrderId 
            chosenStockBuyOrderId = self.nextOrderId+i
            self.placeOrder(self.nextOrderId+i, stock, order)
            i += 1            
    
    def error(self, reqId, errorCode:int, errorString:str):
        print("ERROR ", reqId, errorCode, errorString)
        
        if errorCode == 201: #insufficient cash for initial margin
            global quantity
            quantity = quantity - 1
            self.buystock()
        
    def nextValidId(self, orderId):
        self.nextOrderId = orderId
        self.start()
        
    def start(self):       
        print(f'Cancelling all orders. Time elapsed: {time.perf_counter()-time_start} seconds.')
        self.reqGlobalCancel()

        print(f'Requesting account updates. Time elapsed: {time.perf_counter()-time_start} seconds.')
        self.reqAccountUpdates(True, "")

    def accountDownloadEnd(self, accountName: str):
        print("AccountDownloadEnd. Account:", accountName)

       #close all existing positions
        self.selloff()
      
    def selloff(self):    
        print(f'Closing all positions. Time elapsed: {time.perf_counter()-time_start} seconds.')
        
        for symbol in Portfolio:
              print(f'Selling ticker {symbol} from portfolio')  
              stock = Contract()
              stock.symbol = symbol
              stock.secType = Portfolio[symbol]['SecType']
              stock.exchange = "SMART"
              stock.currency = AccountInfo['Currency']
           
              order = Order()
              order.action = "SELL"
              order.totalQuantity = Portfolio[symbol]['Position']
              order.orderType = "MKT"
              
              global i
              self.placeOrder(self.nextOrderId+i, stock, order)
              i += 1
              
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
        print(f"Account updated - {key} is now {val}")
        
    def updateAccountTime(self, timeStamp: str):
        global AccountInfo
        AccountInfo["Time"] = timeStamp
        print(f"Account updated at time {timeStamp}.")

        #check if all positions are closed
        if float(AccountInfo['NetLiquidation']) - float(AccountInfo['TotalCashBalance']) < 5:
            print('There are no more non-cash assets in the account.')

            #spend all cash to buy chosen stock
            global buy 
            if buy:
                print(f'Buying chosen stock. Time elapsed: {time.perf_counter()-time_start} seconds.')
                
                cashamount = float(AccountInfo['AvailableFunds'])
                price = fulldata.iloc[-1].loc[choice]
                global quantity
                quantity = int(cashamount / price)
            
                self.buystock()
                buy = False #signal not do this part again after we did this once
    
    def orderStatus(self, orderId , status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print("OrderStatus. Id: ", orderId, ", Status: ", status, ", Filled: ", filled, ", Remaining: ", remaining, ", LastFillPrice: ", lastFillPrice)
        
        global stoplosssetup
        if status == 'Filled' and orderId == chosenStockBuyOrderId and stoplosssetup:
            print('Purchase price of stock is ',lastFillPrice)
            
            if recession.iloc[-1].loc['in recession']: 
                stoplossprice = round(lastFillPrice * 0.99, 2)
            else:
                stoplossprice = round(lastFillPrice * 0.93, 2)               
            #1% stop loss if in recession, otherwise 7%
            print('Setting up stop loss order at price ',stoplossprice)

            stock = Contract()
            stock.symbol = choice
            stock.secType = "STK"
            stock.exchange = "SMART"
            stock.currency = "USD"
            
            order = Order()
            order.action = "SELL"
            order.totalQuantity = quantity
            order.orderType = "STP"
            order.auxPrice = stoplossprice
            order.tif = "GTC"
            
            global i
            self.placeOrder(self.nextOrderId+i, stock, order)
            i += 1
            stoplosssetup = False
            
    def openOrder(self, orderId, contract, order, orderState):
        print("OpenOrder. ID:", orderId, contract.symbol, contract.secType, "@", contract.exchange, ":", order.action, order.orderType, order.totalQuantity, orderState.status)

        if order.orderType == "STP" and orderState.status == "PreSubmitted" and not buy:
            print(f'Stopping API connection. Time elapsed: {time.perf_counter()-time_start} seconds.')
            self.stop()

    def execDetails(self, reqId, contract, execution):
        print("ExecDetails. ", reqId, contract.symbol, contract.secType, contract.currency, execution.execId,
              execution.orderId, execution.shares, execution.lastLiquidity)

    def stop(self):
        self.reqAccountUpdates(False, "")
        self.done = True
        print(f'Disconnecting from TWS API. Time elapsed: {time.perf_counter()-time_start} seconds.')
        self.disconnect()

        
def twsapi_main():
    print('Starting TWS API activity')       
    tws = twsapi()
    
    print(f'Connecting to TWS API. Time elapsed: {time.perf_counter()-time_start} seconds.')
    tws.connect('127.0.0.1', 7497, 2)  
    
    #force-stop after 5 minutes if we're not finished by then - most likely because the exchange is closed
    Timer(300, tws.stop).start() 
    
    print(f'Starting run thread. Time elapsed: {time.perf_counter()-time_start} seconds.')
    tws.run()


############global execution code
time_start = time.perf_counter()  

tz = pytz.timezone('US/Eastern')
while True:
    
    nyt = datetime.now(tz)
    print (f'Time in New York is {nyt}')
    
    if nyt.weekday() < 5 and nyt.hour < 15 and nyt.minute < 35:      
        #begin execution
        print('Beginning execution')
        
        #check if US stock market is open by downloading financial data and checking if the last row is from the last 2 minutes
        testdata = yf.download(tickers=['AAPL'], start = nyt, interval = '1m')        
        if testdata.index[-1] < nyt-timedelta(minutes=2):
            print('The US stock market is closed. Execution aborted.')
        
        else:
            print('The US stock market is open. Proceeding')
            execfile("updatestockdata.py")
            execfile("tradingMLprod.py")        
            choice = recommend[0].index[0] 
            twsapi_main()
            #break
    
    else:
        time.sleep(30)