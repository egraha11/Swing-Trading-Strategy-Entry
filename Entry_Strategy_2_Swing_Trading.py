import yfinance as yf
import numpy as numpy
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
from matplotlib import pyplot as plt
import pandas_ta as ta
import numpy as np
import scipy.stats as st
import pymannkendall as mk
from Send_Email import SendText


class Entry_Strategy:

    def __init__(self):

        df_nasdaq = pd.read_csv("Nasdaq_Tickers.csv")
        df_nyse = pd.read_csv("NYSE_Tickers.csv")

        df = pd.concat([df_nasdaq, df_nyse])

        df = df.drop_duplicates(subset="Symbol", keep="first")

        self.end_time = dt.datetime.now()
        #self.end_time = dt.datetime(2024, 1, 23) #for back testing 
        self.start_time = self.end_time - relativedelta(months=3)

        self.tickers=list(df["Symbol"])
        self.stats = {"Symbol":[], "Mann-Kendall":[], "Sharpe":[], "Beta":[]}
        self.current_tickers=pd.read_csv("current_positions.csv")
        self.errors={"Symbol":[], "Error":[], "Date":[]}

        self.current_market = yf.download("^GSPC", start=self.start_time, end=self.end_time, progress=False)["Adj Close"].pct_change().dropna()[-1]
        self.market_percent_flips = []


    #define functions to be used on market aggragate as well as indiviual stocks
    def compute_percent_flips(self, pct_change):

        return pct_change.rolling(2).apply(lambda x: np.sign(x[0]) != np.sign(x[1])).value_counts()[1]/(len(pct_change)-1)
    
    def calculate_stats(self, df, symbol):

        stats = {"Mann-Kendall":[], "Sharpe":[], "Beta":[]}

        pct_change = df["Adj Close"].pct_change().dropna()

        #Mann-Kendall Test For Trend Detection
        print(mk.original_test(df["Adj Close"]).slope)
        stats["Mann-Kendall"].append(mk.original_test(df["Adj Close"]).slope)

        #sharpe ratio
        stats["Sharpe"].append(ta.sharpe_ratio(df["Adj Close"]))
        #beta (volitility in relation to market)
        try:
            stats["Beta"].append(yf.Ticker(symbol).info["beta"])
        except Exception as e:
            stats["Beta"].append("Not Available")

        return stats

    def strategy(self):

        for symbol in self.tickers[:100]:

            if symbol not in self.current_tickers["Symbol"]:

                try:
                    df = yf.download(symbol, start=self.start_time, end=self.end_time, progress=False)

                    stats = self.calculate_stats(df, symbol)

                    self.stats["Symbol"].append(symbol)
                    self.stats["Mann-Kendall"].append(stats["Mann-Kendall"])
                    self.stats["Sharpe"].append(stats["Sharpe"])
                    self.stats["Beta"].append(stats["Beta"])


                except Exception as e:
                    self.errors["Symbol"].append(symbol)
                    self.errors["Error"].append(e)
                    self.errors["Date"].append(self.end_time)

        df = pd.DataFrame.from_dict(self.stats)
        #only take top 20 stocks then sort
        df = df.sort_values("Mann-Kendall", ascending=False)
        df = df.iloc[:20, :]
        df = df.sort_values("Sharpe", ascending=False)

        print(df)

        #write errors to error log 
        pd.DataFrame.from_dict(self.errors).to_csv("error_log.csv", encoding='utf-8', index=False)
        

    #consolidate statistics and send email
    #def email(self):

        #print(self.buy_tickers) #for backtesting 
        #df["metric"] = df["metric"].round(2)

        #df["text data"] = df["Symbol"].str.cat(df[["TI", "metric"]].astype(str), sep=", ")

        #print(df["text data"])
        #print(df.dtypes)

        #email = SendText()
        #email.send_text(df["text data"].values)




entry_strategy = Entry_Strategy()
entry_strategy.strategy()
#entry_strategy.email()