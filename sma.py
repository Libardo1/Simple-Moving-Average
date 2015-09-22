from pyalgotrade.tools import yahoofinance
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import ma
from pyalgotrade import strategy
from pyalgotrade import plotter
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.utils import stats

import os, sys

class StrategySMA(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, smaPeriod, order, cash):
        strategy.BacktestingStrategy.__init__(self, feed, cash)
        self.position = None
        self.instrument = instrument
        self.setUseAdjustedValues(True)
        self.sma = ma.SMA(feed[instrument].getPriceDataSeries(), smaPeriod)
        print 'smaPeriod: ' + str(smaPeriod)
        print 'order: ' + str(order)

    def getSMA(self):
        return self.sma

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info('BUY ' + str(order) + ' ' + tick + ' at $%.2f/share' % (execInfo.getPrice()))

    def onEnteredCanceled(self, position):
        self.position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info('SELL ' + str(order) + ' ' + tick + ' at $%.2f/share' % (execInfo.getPrice()))
        self.position = None

    def onExitCanceled(self, position):
        self.position.exitMarket()

    def onBars(self, bars):
        if self.sma[-1] == None:
            return

        bar = bars[self.instrument]

        if self.position is None:
            if bar.getPrice() < self.sma[-1]:
                self.position = self.enterLong(self.instrument, order, True)

        elif bar.getPrice() > self.sma[-1] and not self.position.exitActive():
            self.position.exitMarket()

def main(tick, year, cash, smaPeriod, order):
    print 'Welcome, ' + os.environ['USER'] + '!'
    print 'Backtesting ' + tick + ' in ' + str(year)

    # Download daily bars
    filename = tick + '-' + str(year) + '.csv'
    yahoofinance.download_daily_bars(tick, year, filename)

    # Load CSV file
    feed = yahoofeed.Feed()
    feed.addBarsFromCSV(tick, filename)

    # Evaluate Strategy
    strategySMA = StrategySMA(feed, tick, smaPeriod, order, cash)

    # Attach a returns analyzers to the strategy.
    retAnalyzer = returns.Returns()
    strategySMA.attachAnalyzer(retAnalyzer)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strategySMA.attachAnalyzer(sharpeRatioAnalyzer)

    # Attach the plotter to the strategy.
    plt = plotter.StrategyPlotter(strategySMA)
    # Include the SMA in the instrument's subplot to get it displayed along with the closing prices.
    plt.getInstrumentSubplot(tick).addDataSeries("SMA", strategySMA.getSMA())

    # Set portfolio cash
    strategySMA.getBroker().setCash(cash)
    initial = strategySMA.getBroker().getEquity()

    # Run the strategy
    strategySMA.run()

    # Print the results
    print '*' * 60
    print 'Initial portfolio value: $%.2f' % initial

    final = strategySMA.getBroker().getEquity()
    print 'Final portfolio value: $%.2f' % final

    net = final - initial
    if net > 0:
        print 'Net gain: $%.2f' % net
    else:
        print 'Net loss: $%.2f' % net

    percentage = (final - initial) / initial * 100
    if percentage > 0:
        print 'Percentage gain: +%.2f%%' % percentage
    else:
        print 'Percentage loss: %.2f%%' % percentage

    #print 'Final portfolio value: $%.2f' % strategySMA.getResult()
    print 'Annual return: %.2f%%' % (retAnalyzer.getCumulativeReturns()[-1] * 100)
    print 'Average daily return: %.2f%%' % (stats.mean(retAnalyzer.getReturns()) * 100)
    print 'Std. dev. daily return: %.4f' % (stats.stddev(retAnalyzer.getReturns()))
    print 'Sharpe ratio: %.2f' % (sharpeRatioAnalyzer.getSharpeRatio(0))

    # Plot the strategy
    plt.plot()

if __name__ == '__main__':
    tick = 'ms.mi'
    year = 2015
    cash = 100000
    smaPeriod = 10
    order = 10000
    main(tick, year, cash, smaPeriod, order)
