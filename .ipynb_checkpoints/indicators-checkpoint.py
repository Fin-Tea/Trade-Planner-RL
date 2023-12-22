import pandas as pd 


def calculate_rsi(data, n=14): 
   # print(data)
    # Calculate the price difference 
    delta = data.diff() 
 
    # Create a copy of the data to avoid changing the original data 
    d = delta.copy() 
 
    # Set negative values to zero 
    d[d < 0] = 0 
 
    # Calculate the exponential moving average 
    ema = pd.Series.ewm(d, span=n).mean() 
 
    # Calculate the relative strength 
    rs = pd.Series.ewm(delta.abs(), span=n).mean() / ema 
 
    # Calculate the RSI 
    rsi = 100 - (100 / (1 + rs)) 
 
    return float(rsi.iloc[-1])