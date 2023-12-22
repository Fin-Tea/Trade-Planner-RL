from datetime import datetime

DATE_FORMAT = '%Y%m%d %H%M%S'

directory = "./price_data/"

PRICE_DATA_FILES = {
    "ES": "ES 12-23.Last_10-10-2023_11-20-2023.txt",
    "MCL": "MCL 12-23.Last_10-10-2023_11-20-2023.txt",
    "MES": "MES 12-23.Last_10-10-2023_11-20-2023.txt",
    "MYM": "MYM 12-23.Last_10-10-2023_11-20-2023.txt",
    "NQ": "NQ 12-23.Last_10-10-2023_11-20-2023.txt"
}

# Ninja Trader always gives price & trade data in the local timezone of the trader
# Remember that this is the whole reason I created security_data as a service
# The price data should be loaded from there
def load_price_data(symbol):
    price_data = []
    keys = PRICE_DATA_FILES.keys()
     
    file_name = ""
     
    for key in keys:
        if symbol.startswith(key):
            file_name = PRICE_DATA_FILES[key]
            break
    
    if file_name:
        path = f'{directory}{file_name}'

        with open(path) as f:
            lines = f.readlines()
             
            for line in lines:
                raw_data = line.split(";")
                candle_data = {
                    'candle_datetime': datetime.strptime(raw_data[0], DATE_FORMAT), 
                    'open': float(raw_data[1]),
                    'high': float(raw_data[2]),
                    'low': float(raw_data[3]),
                    'close': float(raw_data[4]),
                    'volume': int(raw_data[5]),
                 }
                price_data.append(candle_data)
                 
    return price_data


        
        
        
     