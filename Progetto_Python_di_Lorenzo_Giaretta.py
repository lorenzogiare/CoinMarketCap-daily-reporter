import json
import time
from requests import Session
from datetime import date, datetime
import os


# https://coinmarketcap.com/api/documentation/v1/  --> coinmarketcap api documentation


class Reporter:

    def __init__(self, compact_report: bool, market_cap_min: str, api_key: str, daily_volume_min: int):
        self.api_key = api_key
        self.url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'  # endpoint url
        self.headers = {'Accepts': 'application/json',  # expected answer type (JSON)
                        'Accept-Encoding': 'deflate, gzip',  # for faster and more efficient data receiving
                        'X-CMC_PRO_API_KEY': api_key,  # API key for authentication
                        }
        self.session = Session()
        self.session.headers.update(self.headers)

        self.market_cap_min = market_cap_min
        self.daily_volume_min = daily_volume_min
        self.compact_report = compact_report

    # given parameters, returns data via request
    def get_data(self, parameters):
        response = self.session.get(url=self.url, params=parameters).json()
        return response['data']

    # returns slug, symbol and 24h volume of crypto with the highest daily volume
    def crypto_highest_daily_volume(self) -> dict:
        answer = {}
        parameters = {
            'sort': 'volume_24h',
            'limit': '1',
            'market_cap_min': self.market_cap_min
        }

        # requesting data
        data = reporter.get_data(parameters)[0]

        # assigning values of interest
        answer['slug'] = data['slug']
        answer['symbol'] = data['symbol']
        answer['volume_24h'] = round(data['quote']['USD']['volume_24h'], 2)

        return answer

    # returns slug, symbol, and 24h percent change of top 10 and worst 10 cryptos
    def ten_best_and_worst_performing(self) -> dict:
        answer = {
            'best_performing': {},
            'worst_performing': {}
        }
        parameters = {
            'limit': '5000',
            'sort': 'percent_change_24h',
            'market_cap_min': self.market_cap_min
        }

        # requesting data
        data = reporter.get_data(parameters)

        # getting data from top 10 crypto
        range_best = data[:10]
        for crypto in range_best:
            crypto_dict = {
                'slug': crypto['slug']
            }

            if not self.compact_report:
                crypto_dict['symbol'] = crypto['symbol']
                crypto_dict['percent_change_24h'] = round(crypto['quote']['USD']['percent_change_24h'], 2)

            answer['best_performing'][range_best.index(crypto) + 1] = crypto_dict

        # getting data from worst 10 crypto
        range_worst = data[-1:-11:-1]
        for crypto in range_worst:
            crypto_dict = {
                'slug': crypto['slug']
            }

            if not self.compact_report:
                crypto_dict['symbol'] = crypto['symbol']
                crypto_dict['percent_change_24h'] = round(crypto['quote']['USD']['percent_change_24h'], 2)

            answer['worst_performing'][range_worst.index(crypto) + 1] = crypto_dict

        return answer

    # returns total amount needed to buy the top 20 cryptos by cap, as well as slug, symbol and price of each one
    # also returns percent P/L if we were to have bought these cryptocurrencies the day before
    def amount_to_buy_and_pl_first_20_by_cap(self) -> dict:
        answer = {}

        if not self.compact_report:
            answer['top_20_by_cap'] = {}

        total_amount = 0
        total_price_change = 0
        parameters = {
            'sort': 'market_cap',
            'limit': '20'
        }

        # requesting data
        data = reporter.get_data(parameters)

        # iterating over each crypto
        for crypto in data:
            price = crypto['quote']['USD']['price']
            percent_change_24h = crypto['quote']['USD']['percent_change_24h']

            if not self.compact_report:
                crypto_dict = {
                    'slug': crypto['slug'],
                    'symbol': crypto['symbol'],
                    'price': round(price, 2)
                }

                # adding details of crypto
                answer['top_20_by_cap'][data.index(crypto) + 1] = crypto_dict

            total_amount += price
            price_change = price * (1 - ((1 + (percent_change_24h / 100)) ** -1))  # delta price from percent change
            total_price_change += price_change

        answer['total_amount'] = round(total_amount, 2)
        answer['total_daily_percent_profit_or_loss'] = round((total_price_change / total_amount) * 100, 2)

        return answer

    # returns total amount needed to buy every cryptocurrency with market cap higher than a fixed value (76mln)
    # as well as slug, symbol and price of every crypto that is being considered
    def amount_to_buy_crypto_over_volume_limit(self) -> dict:
        volume_limit = self.daily_volume_min
        answer = {}

        if not self.compact_report:
            answer['cryptos'] = {}

        parameters = {
            'sort': 'volume_24h',
            'volume_24h_min': volume_limit,
            'limit': '500'
        }
        total_amount = 0

        # requesting data
        data = reporter.get_data(parameters)

        for crypto in data:
            price = crypto['quote']['USD']['price']
            total_amount += price

            if not self.compact_report:
                crypto_dict = {
                    'slug': crypto['slug'],
                    'symbol': crypto['symbol'],
                    'price': round(price, 2)
                }

                answer['cryptos'][data.index(crypto) + 1] = crypto_dict

        answer['total_amount'] = round(total_amount, 2)

        return answer

    # puts together the report information in a dictionary
    @staticmethod
    def create_report_dictionary() -> dict:
        report = {
            'crypto_highest_daily_volume': reporter.crypto_highest_daily_volume(),
            'top_and_worst_10_performing_daily': reporter.ten_best_and_worst_performing(),
            'amount_to_buy_and_P/L_first_20': reporter.amount_to_buy_and_pl_first_20_by_cap(),
            'amount_to_buy_crypto_over_volume_limit': reporter.amount_to_buy_crypto_over_volume_limit(),
        }

        return report


# some options
market_cap_min = 1000000000  # market cap benchmark for analysis (except for specifically requested market cap values)
daily_volume_min = 76000000  # daily volume minimum requested in 'amount_to_buy_crypto_over_volume_limit' function
compact_report = True  # True will return an abbreviated version of the report
reporting_time = "13:10:00"  # execution time of the daily report
api_key = '******************************'  # <-- TYPE YOUR COINMARKETCAP API KEY HERE

reporter = Reporter(compact_report=compact_report, market_cap_min=str(market_cap_min), api_key=api_key, daily_volume_min=daily_volume_min)


# creates the JSON report file
def create_json_report():

    # checks if reports folder has already been created
    current_dir = os.getcwd()
    folder_dir = f'{current_dir}/daily_reports'

    if not os.path.exists(folder_dir):
        os.mkdir(folder_dir)  # creates directory

    report_dir = f'{current_dir}/daily_reports/{str(date.today().strftime("%d_%m_%Y"))}.json'

    # creates report file inside 'daily_reports' folder
    with open(report_dir, 'w') as report:
        report_dictionary = reporter.create_report_dictionary()
        json.dump(report_dictionary, report, ensure_ascii=False, indent=4)


# cycle for scheduling reports
while True:
    time_now = datetime.strptime(datetime.now().strftime("%H:%M:%S"), "%H:%M:%S")
    time_to_report = datetime.strptime(reporting_time, "%H:%M:%S")
    seconds_to_wait = (time_to_report - time_now).seconds

    print(f'current time: {time_now.strftime("%H:%M")}')
    print(f'reporting time: {time_to_report.strftime("%H:%M")}')
    print(f'waiting {seconds_to_wait // 3600} hours and {(seconds_to_wait % 3600)//60} minutes...\n')

    time.sleep(seconds_to_wait)
    create_json_report()
    print(f'REPORT DATED {date.today().strftime("%d/%m/%Y")} COMPLETED \n')
