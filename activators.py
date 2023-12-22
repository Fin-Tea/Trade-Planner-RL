from enum import Enum
import re
import math
from statistics import fmean, stdev, median
import pandas as pd 
from indicators import calculate_rsi
from price_data_utils import load_price_data

class QualityType(Enum):
    HIGH = 1
    MED = 2
    LOW = 3

ONE_STDEV_UNIFORM = 0.341

""" input: financial instrument symbol, list of trades for that symbol 
    output: high, medium, low 
"""
def calc_instrument_quality(symbol, trades):
    # calculate win rate

    # calculate win/loss ratio (requires parsing pnl (assume this is already done so
    # this method is reusable across trading platforms))

    wins = []
    losses = []

    for trade in trades:
        if trade['symbol'] == symbol:
            pnl = float(trade['pnl'])
            if pnl >= 0:
                wins.append(pnl)
            else:
                losses.append(pnl)

    win_rate = len(wins) / len(trades)
    win_loss_ratio = math.inf
    if len(losses) > 0 and len(wins) > 0:
        win_loss_ratio = fmean(wins) / fmean(losses) 

    if len(wins) == 0:
        win_loss_ratio = 0 

    if win_rate > 0.50 and win_loss_ratio >= 2:
        return QualityType.HIGH

    if win_rate > 0.50 or win_loss_ratio >= 2:
        return QualityType.MED

    return QualityType.LOW 


""" input: list of trades with shape { symbol, pnl }
    output: dictionary of { symbol, instrumentQualityType }  
"""
def calc_instrument_qualities(trades):
    grouped_trades = {}
    qualities = {}

    for trade in trades:
        symbol = trade['symbol']

        symbol_trades = grouped_trades.get(symbol) or []
        symbol_trades.append(trade)

        grouped_trades[symbol] = symbol_trades

    for key, value in grouped_trades.items():
        quality = calc_instrument_quality(key, value)

        qualities[key] = quality

    return qualities


def calc_time_of_day_quality(symbol, trades, current_time=None):    
    # hourly bucket keys: ["0-1","1-2","2-3","3-4","4-5","5-6","6-7","7-8","8-9","9-10","10-11","11-12","12-13","13-14","14-15","15-16","16-17","17-18","18-19","19-20","20-21","21-22","22-23","23-0"]
    augmented_trades = [trade for trade in trades if trade['symbol'] == symbol]
    
    hourly_buckets = {}

    wins = [trade for trade in augmented_trades if float(trade['pnl']) >= 0]

    for trade in wins:
        open_hour = trade['open_datetime'].hour

        bucket_key = f'{open_hour}-{open_hour + 1}'

        hourly_bucket = hourly_buckets.get(bucket_key) or []
        hourly_bucket.append(trade)
        hourly_buckets[bucket_key] = hourly_bucket

    #print(hourly_buckets)
    
    temp_bucket = []
    best_bucket_key = ""
    quality_buckets = []

    for key, value in hourly_buckets.items():
        if len(value) > len(temp_bucket):
            temp_bucket = value
            best_bucket_key = key

    quality_buckets.append(best_bucket_key)

    for key, value in hourly_buckets.items():
        if len(value) == len(temp_bucket) and key not in quality_buckets:
              quality_buckets.append(key)

    print(quality_buckets)

    for trade in augmented_trades:
        open_hour = trade['open_datetime'].hour

        bucket_key = f'{open_hour}-{open_hour + 1}'

        quality = QualityType.LOW

        if bucket_key in quality_buckets:
            quality = QualityType.HIGH

        trade['time_of_day_quality'] = quality

    return augmented_trades


def calc_time_of_day_qualities(trades): 
    augmented_trades = []
    grouped_trades = {}

    for trade in trades:
        symbol = trade['symbol']

        symbol_trades = grouped_trades.get(symbol) or []
        symbol_trades.append(trade)

        grouped_trades[symbol] = symbol_trades

    for key, value in grouped_trades.items():
        trades_with_qualities = calc_time_of_day_quality(key, value)
        augmented_trades.extend(trades_with_qualities)

    return augmented_trades


def calc_market_conditions(trade, historical_price_data):
    start = -1
    end = -1

    for i, candle in enumerate(historical_price_data):
        if candle["candle_datetime"] >= trade["open_datetime"] and start == -1:
            start = i - 1

        if candle["candle_datetime"] >= trade["close_datetime"] and end == -1:
            end = i

    # handle edge cases
    if start == -1: 
        start = 0

    if end == -1:
        end = len(historical_price_data) - 1

    trade_candles = historical_price_data[start:end]

    if trade_candles:
        leading_index = start - 14
        if leading_index < 0:
            leading_index = 0
            
        leading_candles = historical_price_data[leading_index:start]
    
        total_volume = sum([t["volume"] for t in trade_candles])
    
        range_low = min([t["low"] for t in trade_candles])
        range_high = max([t["high"] for t in trade_candles])
        total_range = range_high - range_low
    
        # calculate the RSI at when the trade was opened
        leading_candles_df = pd.DataFrame([t['close'] for t in leading_candles])
    
        leading_rsi = calculate_rsi(leading_candles_df) if len(leading_candles) >= 14 else 50
    
        #print(leading_rsi)
    
        return { 'total_volume': total_volume, 'total_range': total_range, 'leading_rsi': leading_rsi }

    return { 'total_volume': -1, 'total_range': -1, 'leading_rsi': -1 }
    
    

def calc_instrument_conditions_quality(symbol, trades, real_time_price_data=None, lookup_key='instrument_conditions_quality'):
    
    augmented_trades = [trade for trade in trades]

    historical_price_data = load_price_data(symbol)

    wins = [trade for trade in trades if trade['symbol'] == symbol and float(trade['pnl']) >= 0]
    volumes = [] # a list of volume sums during each trade
    ranges = [] # a list of high - low during each trade (with the idea of checking whether the current price range is within a standard deviation of the average of the ranges)
    RSIs = []
    
    for trade in wins:
        market_conditions = calc_market_conditions(trade, historical_price_data)
        if market_conditions['total_volume'] != -1:
            volumes.append(market_conditions['total_volume'])
            ranges.append(market_conditions['total_range'])
            RSIs.append(market_conditions['leading_rsi'])

    # print("volumes", volumes)
    # print("ranges", ranges)
    # print("RSI", RSIs)

    # calculate means & standard deviations
    if volumes and ranges and RSIs:
        # print("volumes, ranges, and RSI found")
        avg_volume = median(volumes)
        stdev_volume = avg_volume * ONE_STDEV_UNIFORM
        avg_volume_low = avg_volume - stdev_volume
        avg_volume_high = avg_volume + stdev_volume

        # print("avg_volume", avg_volume)
        # print("stdev_volume", stdev_volume)
        # print("avg_volume_low", avg_volume_low)
        # print("avg_volume_high", avg_volume_high)
        
    
        avg_range = median(ranges)
        stdev_range = avg_range * ONE_STDEV_UNIFORM
        avg_range_low = avg_range - stdev_range
        avg_range_high = avg_range + stdev_range

        # print("avg_range", avg_range)
        # print("stdev_range", stdev_range)
        # print("avg_range_low", avg_range_low)
        # print("avg_range_high", avg_range_high)
    
        avg_rsi = fmean(RSIs)
        stdev_rsi = avg_rsi * ONE_STDEV_UNIFORM
        avg_rsi_low = avg_rsi - stdev_rsi
        avg_rsi_high = avg_rsi + stdev_rsi

        # print("avg_rsi", avg_rsi)
        # print("stdev_rsi", stdev_rsi)
        # print("avg_rsi_low", avg_rsi_low)
        # print("avg_rsi_high", avg_rsi_high)
    
        for trade in augmented_trades:
            market_conditions = calc_market_conditions(trade, historical_price_data)
    
            total_trade_volume = market_conditions['total_volume']
            total_trade_range = market_conditions['total_range']
            leading_trade_rsi = market_conditions['leading_rsi']

            # print("total_trade_volume", total_trade_volume)
            # print("total_trade_range", total_trade_range)
            # print("leading_trade_rsi", leading_trade_rsi)
            
    
            quality = QualityType.LOW
    
            if avg_volume_low <= total_trade_volume and total_trade_volume <= avg_volume_high and avg_range_low <= total_trade_range and total_trade_range <= avg_range_high and avg_rsi_low <= leading_trade_rsi and leading_trade_rsi <= avg_rsi_high:
                quality = QualityType.HIGH
                # print("high quality instrument conditions")
    
            trade[lookup_key] = quality
            
    for trade in augmented_trades:
        if not trade.get(lookup_key):
            trade[lookup_key] = QualityType.LOW
            
            

    return augmented_trades

def calc_instrument_condition_qualities(trades):
    augmented_trades = []
    grouped_trades = {}

    for trade in trades:
        symbol = trade['symbol']

        symbol_trades = grouped_trades.get(symbol) or []
        symbol_trades.append(trade)

        grouped_trades[symbol] = symbol_trades

    for key, value in grouped_trades.items():
        trades_with_qualities = calc_instrument_conditions_quality(key, value)
        augmented_trades.extend(trades_with_qualities)

    return augmented_trades

def calc_market_condition_qualities(trades):
    # set the ES (e-mini S&P 500 futures instrument) as a proxy for the S&P 500/overall market
    return calc_instrument_conditions_quality("ES", trades, lookup_key='market_conditions_quality')


def calc_position_size_quality(symbol, trades):
    # position size is risk so this is a risk calculation
    # identify the average position size (perhaps median)
    # of the winning trades per instrument
    # and then check to see what position sizes are <= to that
    # position size to determine quality
    # what will happen in the future is that
    # if the position size quality is low
    # then the app will give a warning about it
    # it's not, "Don't trade this position size because it's riskier than usual"
    # it's, "Hey this may be a great trade for you overall. Know that you're
    # risking more than you normally do. Tip: Tigthen your risk if you're scaling."
    augmented_trades = [trade for trade in trades]

    winning_sizes = [int(trade['qty']) for trade in augmented_trades if trade['symbol'] == symbol and float(trade['pnl']) >= 0]

    avg_size = fmean(winning_sizes)

    print(avg_size)

    for trade in augmented_trades:

        quality = QualityType.LOW

        if int(trade['qty']) <= avg_size:
            quality = QualityType.HIGH

        trade['position_size_quality'] = quality
    
    return augmented_trades
    

def calc_position_size_qualities(trades):
    augmented_trades = []
    grouped_trades = {}

    for trade in trades:
        symbol = trade['symbol']

        symbol_trades = grouped_trades.get(symbol) or []
        symbol_trades.append(trade)

        grouped_trades[symbol] = symbol_trades

    for key, value in grouped_trades.items():
        trades_with_qualities = calc_position_size_quality(key, value)
        augmented_trades.extend(trades_with_qualities)

    return augmented_trades


def calc_profitability_qualities(trades):
    augmented_trades = [trade for trade in trades]

    for trade in augmented_trades:
        profitability_quality = QualityType.LOW
        
        if float(trade['pnl']) >= 0:
            profitability_quality = QualityType.HIGH

        trade['profitability_quality'] = profitability_quality

    return augmented_trades
            
    
    
    
        

    

        
        
        

            
            
        

    


    


    
    
    
    