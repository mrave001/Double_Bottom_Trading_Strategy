import backtrader as bt
import datetime
import math
import numpy as np

cerebro = bt.Cerebro()
cerebro.broker.setcash(25000.00)


class GenericCSV_Extended(bt.feeds.GenericCSVData):
    # Add a 'VWAP' line to the inherited ones from the base class
    lines = ('VWAP', 'RSI')

    # VWAP in GenericCSVData has index 8 ... add 1
    # add the parameter to the parameters inherited from the base class
    params = (('VWAP', 9),('RSI', 6))


# Initializing a data feed for Down_trend_Break_Out algo backtesting
datapath = '/Users/Miguel/VirEnv/KeshigTrading/Trading_Algos_Python/Stock_Data/TQQQ_15m_2021.csv'
data = GenericCSV_Extended(
    dataname=datapath,
    fromdate=datetime.datetime(2021, 1, 5),
    todate=datetime.datetime(2022, 1, 5),
    timeframe=bt.TimeFrame.Minutes,
    compression=60,
    dtformat='%m/%d/%Y %H:%M',
)

cerebro.adddata(data)

'''
Implementing the VWAP_Delta algo as a bt-integrated backtesting strategy
'''


class RSI_Rebound(bt.Strategy):

    def log(self, txt, date=None):
        '''Instantiating a logging function for this strategy'''
        date = date or self.datas[0].datetime.datetime(0).strftime('%Y-%m-%d %H:%M:%S')
        print('%s, %s' % (date, txt))

    def __init__(self):
        # Keeping a reference to headers of interest in the datas[0] dataseries
        self.open_data = self.datas[0].open
        self.close_data = self.datas[0].close
        self.atr = bt.ind.ATR(period=1)
        self.VWAP = self.datas[0].VWAP
        self.RSI = self.datas[0].RSI
        self.Delta = (self.datas[0].close - self.datas[0].VWAP)
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.avg_percent_gain = []
        self.avg_dollar_gain = []

        self.avg_percent_gain_winning = []
        self.avg_percent_gain_losing = []

        self.initial_account_balance = self.broker.getvalue()

        self.percentages = {
            'avgpercentgain': '',
            'avgdollargain': ''
        }

    def notify_trade(self, trade):
        if trade.isclosed:
            # Checking performance upon position close; compare with portfolio value
            print(
                'Realized PNL: %.2f' % trade.pnl + ', ' +
                'Portfolio Value: %.2f' % cerebro.broker.getvalue()
            )
            if (trade.pnl < 0 and abs(trade.pnl) > 2 * self.atr):
                print('NET LOSS WARNING... ')

    def notify_order(self, order):

        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                print('BUY EXECUTED AT; Price: %.2f' % order.executed.price)
                print('position size buy: %.2f' % self.position.size)

            elif order.issell():
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

                print('Buy Price: ' + str(self.buyprice))
                print('Sell Price: ' + str(order.executed.price))

                # get the current average of this trade
                difference_dollaramount_buy_sell = order.executed.price - self.buyprice
                difference_percentamount_buy_sell = ((order.executed.price - self.buyprice) / self.buyprice) * 100

                self.avg_dollar_gain.append(difference_dollaramount_buy_sell)
                self.avg_percent_gain.append(difference_percentamount_buy_sell)

                print('--------------------------------------------------------')

                print('difference_dollaramount_buy_sell:')
                print(difference_dollaramount_buy_sell)

                print('difference_percentamount_buy_sell')
                print(difference_percentamount_buy_sell)

                if (self.buyprice < order.executed.price):
                    self.losing_trades += 1
                    self.avg_percent_gain_winning.append(difference_percentamount_buy_sell)
                else:
                    self.winning_trades += 1
                    self.avg_percent_gain_losing.append(difference_percentamount_buy_sell)

                self.total_trades += 1
                print('SELL EXECUTED AT; Price: %.2f' % order.executed.price)
                print('Position Size Sell: %.2f' % self.position.size)

                print('Total number of trades: ' + str(self.total_trades))
                print('Total number of winning trades: ' + str(self.winning_trades))
                print('Total number of losing trades: ' + str(self.losing_trades))

                # Get avg of list
                print('Average Percent Gain Per Trade: ')
                print(self.Average(self.avg_percent_gain))

                print('Average Dollar Gain Per Trade: ')
                print(self.Average(self.avg_dollar_gain))

                if (len(self.avg_percent_gain_winning)):
                    print('Average Percent Winning: ')
                    print(self.Average(self.avg_percent_gain_winning))

                if (len(self.avg_percent_gain_losing)):
                    print('Average Percent Losing: ')
                    print(self.Average(self.avg_percent_gain_losing))

                print('--------------------------------------------------------')
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

    # Python program to get average of a list
    def Average(self, lst):
        return sum(lst) / len(lst)

    def show_statistics(self):
        print('Total Number of Trades: ' + str(self.total_trades))

    def next(self):
        # Logging headers of interest from the reference
        # self.log(
        #     'Open: %.2f' % self.open_data[0]
        #     + ', ' + 'Close: %.2f' % self.close_data[0]
        #     + ', ' + 'ATR: %.2f' % self.atr[0]
        #     + ', ' + 'VWAP: %.2f' % self.VWAP[0]
        #     + ', ' + 'Delta: %.2f' % self.Delta[0]
        # )

        # Parameters for this algo
        PS = math.trunc(self.broker.getvalue() / self.open_data[0])
        ATRPF = 6  # 'ATR Daily Profit Factor'
        ATRLF = 4  # 'ATR Daily Stop Loss Factor'
        TPF = 6  # 'Take Profit Factor' per trade
        SLF = 2.5  # 'Stop Loss Factor' per trade
        crypto_trade = 1  # Set to 1 if Crypto
        SF = 0.01  # Slippage factor for data stream
        # Cheapo factor for limit buy order(s) Also working like a risk on/off parameter
        CF, CF2 = 0, 3
        #B1, B2, MP = 0, 0, 0
        VWDy, Two_Short, Two_Long, PB2Ex, Lsize, MPy = 5, 1, 7, 5, 100, 5

        L = np.array(self.RSI.get(size=Lsize))
        # L = self.RSI.get(size=200)
        L2 = np.sort(L)  # Sorting lowest to highest
        B1, B2 = L2[0:1], L2[1:2]
        PB1, PB2 = 0, 0

        # Checking if avg RSI is under 50 and Position size = 0
        if np.mean(L) < 50 and self.position.size == 0:
            if abs(B1 - B2) <= VWDy:  # If bottoms are within y axis window
                for i in range(0, L.size + 1, 1):
                    if L[i:i+1] == B1:
                        PB1 = i  # Position of Bottom 1 Note: Possibility for improvement w/ a break
                    elif L[i:i+1] == B2:
                        PB2 = i  # Position of Bottom 2 Note: if the case the first element is a bottom it won't buy

                if Two_Short < abs(PB1 - PB2) < Two_Long and PB1 > 0 and PB2 > 0 and L.size > 0 and PB2 > PB1:
                    Lmid = L[PB1:PB2+1]
                    if Lmid.size > 0:
                        MP = np.max(Lmid)
                        for k in range(0, L.size + 1, 1):
                            if L[k:k + 1] == MP:
                                PMP = k  # Position of Mid Point

                        # Checking value of MP for possible W shape
                        if 0 <= abs((MP - ((B1+B2)/2))) <= MPy:
                            # PB2Ex is a guess to the ending of W
                            for j in range(1, PB2Ex + 1, 1):
                                if L[(PB2+j):(PB2+j+1)] >= MP:
                                    #print('Possible W', '\n')
                                    self.order = self.buy_bracket(
                                        size=PS,
                                        limitprice=self.data.open[j] +
                                        (TPF * self.atr[j]),
                                        price=(
                                            self.data.open[j] - (CF*self.data.open[j]) - CF2),
                                        stopprice=(
                                            self.data.open[j] - (SLF * self.atr[j]))
                                    )

                        #Next step is too find mid point between B1 and B2

        # print(PB1,'\n', PB2,'\n')
        #if L[L.size:L.size+1]
        # if L.size>0:
        #     print(np.min(L))
        #print(L)












        # def second_smallest(L):
        #     m1 = m2 = float('inf')
        #     for x in L:
        #         if x <= m1:
        #             m1, m2 = x, m1
        #         elif x < m2:
        #             m2 = x
        #     return m2
        # print(self.VWAP[0])
        # print(len(lastdataclose))
        # print('\n ','This is the complete numpy array: \n ', L, '\n')
        # print('This is the sorted  numpy array :\n ', L2, '\n')
        # print(L2)
        # print('These are the lowest two values of the array :\n ', L3, '\n')
        # print(f'This is the difference b/w the two min values: {L4}', '\n')
cerebro.addstrategy(RSI_Rebound)

print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.run()
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

cerebro.plot(plotname='RIOT 1/5/21 - 1/5/22')
