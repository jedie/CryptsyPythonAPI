
import urllib
import urllib2
import json
import time
import hmac
import hashlib
import datetime


class Api(object):
    """ API wrapper for the Cryptsy API. """
    def __init__(self, key, secret):
        self.API_KEY = key
        self.SECRET = secret

        # set in _public_api_query and _api_query,
        # used for verbose output in high level API
        self.last_api = None
        self.last_method = None

    def _request(self, url, request_data=None, headers=None):
        """ Do a public or authenticated API request """
        if headers is None:
            headers = {}

        request = urllib2.Request(url, request_data, headers)
        f = urllib2.urlopen(request)
        return json.loads(f.read())

    def _public_api_query(self, method, marketid=None):
        """ Call to the public api and return the loaded json. """
        # Used for verbose output in high level API
        self.last_api = "public API"
        self.last_method = method

        request_url = 'http://pubapi.cryptsy.com/api.php?method=%s' % method
        if marketid is not None:
            request_url += '&marketid=%d' % marketid

        return self._request(request_url)

    def _api_query(self, method, request_data=None):
        """ Call to the "private" api and return the loaded json. """
        # Used for verbose output in high level API
        self.last_api = "auth API"
        self.last_method = method

        if request_data is None:
            request_data = {}
        request_data['method'] = method
        request_data['nonce'] = int(round(time.time() * 1000))
        post_data = urllib.urlencode(request_data)

        signed_data = hmac.new(self.SECRET, post_data, hashlib.sha512)\
                          .hexdigest()
        headers = {
            'Sign': signed_data,
            'Key': self.API_KEY
        }

        return self._request('https://www.cryptsy.com/api', post_data, headers)

    def market_data(self, marketid=None, v2=False):
        """ Get market data for all markets.

        Defaults to the old version of getmarketdata. Set v2 to True to use
        getmarketdatav2.
        """
        if v2 is True:
            return self._public_api_query("marketdatav2")
        if marketid is not None:
            return self._public_api_query("singlemarketdata", marketid=marketid)
        return self._public_api_query("marketdata")

    def order_book_data(self, marketid=None):
        """ Get orderbook data for all markets, or for a single one.

        :param marketid: If provided, API will only return orderbook data for
            this specific market.
        """
        if marketid is None:
            return self._public_api_query("orderdata")
        return self._public_api_query("singleorderdata", marketid=marketid)

    def info(self):
        """ Get some information about the server and your account.

        Resultset contains:

        balances_available  Array of currencies and the balances availalbe for each
        balances_hold   Array of currencies and the amounts currently on hold for open orders
        servertimestamp Current server timestamp
        servertimezone  Current timezone for the server
        serverdatetime  Current date/time on the server
        openordercount  Count of open orders on your account
        """
        return self._api_query('getinfo')

    def markets(self):
        """ Get a list of all active markets.

        Resultset contains:

        marketid    Integer value representing a market
        label   Name for this market, for example: AMC/BTC
        primary_currency_code   Primary currency code, for example: AMC
        primary_currency_name   Primary currency name, for example: AmericanCoin
        secondary_currency_code Secondary currency code, for example: BTC
        secondary_currency_name Secondary currency name, for example: BitCoin
        current_volume  24 hour trading volume in this market
        last_trade  Last trade price for this market
        high_trade  24 hour highest trade price in this market
        low_trade   24 hour lowest trade price in this market
        """
        return self._api_query('getmarkets')

    def my_transactions(self):
        """ Get all your deposits and withdrawals from your account.

        Resultset contains:

        currency    Name of currency account
        timestamp   The timestamp the activity posted
        datetime    The datetime the activity posted
        timezone    Server timezone
        type    Type of activity. (Deposit / Withdrawal)
        address Address to which the deposit posted or Withdrawal was sent
        amount  Amount of transaction
        """
        return self._api_query('mytransactions')

    def market_trades(self, marketid):
        """ Get the last 1000 trades for this market, ordered descending by
        date.

        Resultset contains:

        datetime    Server datetime trade occurred
        tradeprice  The price the trade occurred at
        quantity    Quantity traded
        total   Total value of trade (tradeprice * quantity)

        :param marketid: Market for which you are querying.
        """
        return self._api_query('markettrades', request_data={'marketid': marketid})

    def market_orders(self, marketid):
        """ Return currently open sell and buy orders.

        Resultset contains two arrays, one for sell orders, one for buy orders,
        containing the following fields:

        sellprice   If a sell order, price which order is selling at
        buyprice    If a buy order, price the order is buying at
        quantity    Quantity on order
        total   Total value of order (price * quantity)

        :param marketid: Market ID for which you are querying.
        """
        return self._api_query('marketorders',
                               request_data={'marketid': marketid})

    def single_market_data(self, marketid):
        """ Return General Market Data from a single market """
        return self._public_api_query('singlemarketdata', marketid)

    def my_trades(self, marketid=None, limit=200):
        """ Get all your trades for this market, ordered descending by date.

        Resultset contains:

        tradeid An integer identifier for this trade
        tradetype   Type of trade (Buy/Sell)
        datetime    Server datetime trade occurred
        tradeprice  The price the trade occurred at
        quantity    Quantity traded
        total   Total value of trade (tradeprice * quantity)

        :param marketid: Marketid for which you are querying.
        :param limit: Maximum number of results, defaults to 200.
        """
        if marketid is None:
            return self._api_query('allmytrades')
        return self._api_query('mytrades', request_data={'marketid': marketid,
                                                         'limit': limit})

    def my_orders(self, marketid=None):
        """ Get all your orders, or your orders for a specific market.

        Resultset contains:

        orderid Order ID for this order
        created Datetime the order was created
        ordertype   Type of order (Buy/Sell)
        price   The price per unit for this order
        quantity    Quantity for this order
        total   Total value of order (price * quantity)

        :param marketid: If provided, orders will be filtered by this marketid.
        """
        if marketid is None:
            return self._api_query('allmyorders')
        return self._api_query('myorders', request_data={'marketid': marketid})

    def depth(self, marketid):
        """ Get an array of buy and sell orders on the given market
        representing the market depth.

        :param marketid: A market ID.
        """
        return self._api_query('depth', request_data={'marketid': marketid})

    def _create_order(self, marketid, ordertype, quantity, price):
        """ Creates an order for buying or selling coins.

        It is preferable to buy and sell coins using the Api.buy and Api.sell
        methods.

        :param marketid: Market to buy from.
        :param ordertype: Either Buy or Sell.
        :param quantity: Number of coins to buy.
        :param price: At this price.
        :returns: A dict containing the orderid of the created order.
        """
        return self._api_query('createorder',
                               request_data={'marketid': marketid,
                                             'ordertype': ordertype,
                                             'quantity': quantity,
                                             'price': price})

    def buy(self, marketid, quantity, price):
        """ Buy a specified number of coins on the given market. """
        return self._create_order(marketid, 'Buy', quantity, price)

    def sell(self, marketid, quantity, price):
        """ Sell a specified number of coins on the given market. """
        return self._create_order(marketid, 'Sell', quantity, price)

    def cancel_order(self, orderid):
        """ Cancel a specific order.

        :param orderid: The ID of the order you want to cancel.
        :returns: A succescode if succesfull.
        """
        return self._api_query('cancelorder', request_data={'orderid': orderid})

    def cancel_all_market_orders(self, marketid):
        """ Cancel all currently pending orders for a specific market.

        :param marketid: Market ID for wich you would like to cancel orders.
        """
        return self._api_query('cancelmarketorders',
                              request_data={'marketid': marketid})

    def cancel_all_orders(self):
        """ Cancel all currently pending orders. """
        return self._api_query('cancelallorders')

    def calculate_fees(self, ordertype, quantity, price):
        """ Calculate fees that would be charged for the provided inputs.

        :param ordertype: Order type you are calculating for (Buy/Sell)
        :param quantity: Amount of units you are buying/selling
        :param price: Price per unit you are buying/selling at
        :returns: A dict containing the fee and the net total with fees.
        """
        return self._api_query('calculatefees',
                               request_data={'ordertype': ordertype,
                                             'quantity': quantity,
                                             'price': price})

    def generate_new_address(self, currencyid=None, currencycode=None):
        """ Generate a new address for a currency. Expects either a currencyid
        OR a currencycode (not both).

        :param currencyid: ID of a currency on Cryptsy.
        :param currencycode: Code of a currency on Cryptsy.
        :throws ValueError: Fails if neither of the parameters are given.
        :returns: A dict containing the newly generated address.
        """
        if currencyid is not None:
            req = {'currencyid': currencyid}
        elif currencycode is not None:
            req = {'currencycode': currencycode}
        else:
            raise ValueError('You should specify either a currencyid or a'
                             'currencycode')

        return self._api_query('generatenewaddress', request_data=req)

    def my_transfers(self):
        """ Array of all transfers into/out of your account sorted by requested
        datetime descending.

        Resultset contains:

        currency	Currency being transfered
        request_timestamp	Datetime the transfer was requested/initiated
        processed	Indicator if transfer has been processed (1) or not (0)
        processed_timestamp	Datetime of processed transfer
        from	Username sending transfer
        to	Username receiving transfer
        quantity	Quantity being transfered
        direction	Indicates if transfer is incoming or outgoing (in/out)
        """
        self._api_query('mytransfers');

    def wallet_status(self):
        """ Array of Wallet Statuses

        Resultset contains:

        currencyid	Integer value representing a currency
        name	Name for this currency, for example: Bitcoin
        code	Currency code, for example: BTC
        blockcount	Blockcount of currency hot wallet as of lastupdate time
        difficulty	Difficulty of currency hot wallet as of lastupdate time
        version	Version of currency hotwallet as of lastupdate time
        peercount	Connected peers of currency hot wallet as of lastupdate time
        hashrate	Network hashrate of currency hot wallet as of lastupdate time
        gitrepo	Git Repo URL for this currency
        withdrawalfee	Fee charged for withdrawals of this currency
        lastupdate	Datetime (EST) the hot wallet information was last updated
        """
        self._api_query('getwalletstatus')

    def make_withdrawal(self, address, amount):
        """ Make a withdrawal to a trusted withdrawal address.

        :param address: Pre-approved address for which you are withdrawing to.
        :param amount: Amount you are withdrawing, maximum of 8 decimals.
        """
        self._api_query('makewithdrawal',
                        request_data={
                            'address': address,
                            'amount': amount
                        })


#------------------------------------------------------------------------------


def convert_recursive(v):
    if isinstance(v, dict):
        for k, item in v.items():
            v[k] = convert_recursive(item)
        return v
    elif isinstance(v, list):
        return [convert_recursive(item) for item in v]
    elif isinstance(v, tuple):
        return tuple([convert_recursive(item) for item in v])

    try:
        return int(v)
    except ValueError:
        pass

    try:
        return float(v)
    except ValueError:
        pass

    try:
        return datetime.datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    return v




def only_non_zero(d):
    return dict([(k, v) for k, v in d.items() if v > 0])


class AccountBalance(dict):
    def __init__(self, api):
        balance = api.info()
        super(AccountBalance, self).__init__(balance)

    def print_balance(self):
        print "_"*79
        print "    AccountBalance"
        print " -"*39
        for key, values in sorted(self.items()):
            if key.startswith("balances"):
                print "%s:" % key.replace("_", " ")
                for currency, value in sorted(only_non_zero(values).items()):
                    print "%30.8f %s" % (value, currency)
            else:
                print "%s:" % key.replace("_", " ")
                print "%30s" % values


class CrypsyAPIError(Exception):
    pass


class HighLevelApi(Api):
    """
    High-Level crypsy API
    """
    def __init__(self, *args, **kwargs):

        # Display request information?
        self.verbose = kwargs.pop("verbose", False)

        super(HighLevelApi, self).__init__(*args, **kwargs)

        # Store the untouched last API result dict
        self.last_raw_result = None

        # Stores 'info' result
        self.balance = None

    def _request(self, url, request_data=None, headers=None):
        if self.verbose:
            print "Request %r method %r..." % (
                self.last_api, self.last_method
            ),
            start_time = time.time()

        result = super(HighLevelApi, self)._request(url, request_data, headers)
        self.last_raw_result = result.copy()
        if self.verbose:
            print "OK (response in %.2fsec)" % (time.time() - start_time)

        if "error" in result:
            raise CrypsyAPIError(result["error"])

        if result["success"] in ("0", 0):
            raise CrypsyAPIError("Unknown error. Raw response: %s" % repr(result))

        result = result["return"]
        result = convert_recursive(result)
        return result


    def get_balance(self):
        """
        Cached access to account balance
        """
        if self.balance is None:
            self.balance = AccountBalance(self)
        return self.balance

    def single_market_data(self, marketid):
        result = super(HighLevelApi, self).single_market_data(marketid)
#         markets = self._api_query(method, request_data)
#         ["return"]["markets"]
        return result




if __name__ == "__main__":
    from pprint import pprint
#     d = {u'serverdatetime': u'2014-04-08 09:22:47', u'balances_available': {u'NYAN': 0.0, u'EXE': 0.0, u'TIX': 0.0, u'BC': 0.0, u'XJO': 0.0, u'NAN': 0.0, u'RYC': 0.0, u'DRK': 0.0, u'HBN': 0.0, u'CPR': 0.0, u'SXC': 0.0, u'MEOW': 0.0, u'SPT': 0.0, u'CENT': 0.0, u'TAG': 0.0, u'CLR': 0.0, u'LYC': 0.0, u'SPA': 0.0, u'SAT': 0.0, u'NXT': 0.0, u'BQC': 0.0, u'XPM': 0.0, u'IXC': 0.0, u'DBL': 0.0, u'ZEIT': 0.0, u'MAX': 0.0, u'ALF': 0.0, u'MZC': 0.0, u'PHS': 0.0, u'FST': 0.0, u'PYC': 0.0, u'FFC': 0.0, u'EMD': 0.0, u'BEN': 0.0, u'CMC': 0.0, u'CRC': 0.0, u'DEM': 0.0, u'FLO': 0.0, u'LKY': 0.0, u'YBC': 0.0, u'BET': 0.0, u'AMC': 0.0, u'BUK': 0.0, u'MEC': 0.0, u'OSC': 0.0, u'MNC': 0.0, u'PTS': 0.0, u'FLAP': 0.0, u'TRC': 0.0, u'CSC': 0.0, u'FTC': 0.0, u'LEAF': 0.0, u'ANC': 0.0, u'DOGE': 0.0, u'MOON': 0.0, u'BTE': 0.0, u'BTG': 0.0, u'NVC': 0.0, u'BTC': 0.0, u'BTB': 0.0, u'LK7': 0.0, u'GLC': 0.0, u'GLD': 0.0, u'NEC': 0.0, u'DVC': 0.0, u'GLX': 0.0, u'XNC': 0.0, u'BCX': 0.0, u'CTM': 0.0, u'NET': 0.0, u'SMC': 0.0, u'COL': 0.0, u'RED': 0.0, u'DGB': 0.0, u'DGC': 0.0, u'TEK': 0.0, u'CGB': 0.0, u'CASH': 0.0, u'KDC': 0.0, u'ASC': 0.0, u'NBL': 0.0, u'JKC': 0.0, u'FRC': 0.0, u'SRC': 0.0, u'ADT': 0.0, u'CAP': 0.0, u'FRK': 0.0, u'ELC': 0.0, u'GME': 0.0, u'LTC': 0.05607079, u'RDD': 0.0, u'AUR': 0.0, u'ELP': 0.0, u'MINT': 0.0, u'YAC': 0.0, u'UNO': 0.0, u'ZED': 0.0, u'MEM': 0.0, u'HVC': 0.0, u'SBC': 0.0, u'GDC': 0.0, u'NMC': 0.0, u'ZET': 0.0, u'TAK': 0.0, u'ORB': 0.0, u'BAT': 0.0, u'HYC': 0.0, u'MST': 0.0, u'IFC': 0.0, u'VTC': 0.0, u'CAT': 0.0, u'WDC': 0.0, u'LOT': 0.0, u'PPC': 0.0, u'DMD': 0.0, u'EAC': 0.0, u'QRK': 0.0, u'42': 0.0, u'TGC': 0.0, u'RPC': 0.0, u'PXC': 0.0, u'TIPS': 0.0, u'UTC': 0.0, u'CNC': 0.0, u'STR': 0.0, u'CACH': 0.0, u'ZCC': 0.0, u'NRB': 0.0, u'KGC': 0.0, u'Points': 0.00853, u'ARG': 0.0, u'POT': 0.0, u'EZC': 0.0}, u'balances_hold': {u'PPC': 45.68529191, u'XPM': 16.36380436, u'MEM': 200.0, u'AUR': 16.42351408, u'DOGE': 34352.91600716, u'LTC': 6.12378988, u'FTC': 1.06459434, u'Points': 0.0106425, u'IFC': 1139.05522289, u'TIPS': 8204.37674}, u'servertimezone': u'EST', u'balances_hold_btc': {u'PPC': 0.0, u'XPM': 0.0, u'MEM': 0.0, u'AUR': 0.0, u'DOGE': 0.0, u'LTC': 0.0, u'FTC': 0.0, u'Points': 0.0, u'IFC': 0.0, u'TIPS': 0.0}, u'openordercount': 33, u'servertimestamp': 1396963367, u'balances_available_btc': {u'NYAN': 0.0, u'EXE': 0.0, u'TIX': 0.0, u'BC': 0.0, u'XJO': 0.0, u'NAN': 0.0, u'RYC': 0.0, u'DRK': 0.0, u'HBN': 0.0, u'CPR': 0.0, u'SXC': 0.0, u'MEOW': 0.0, u'SPT': 0.0, u'CENT': 0.0, u'TAG': 0.0, u'CLR': 0.0, u'LYC': 0.0, u'SPA': 0.0, u'SAT': 0.0, u'NXT': 0.0, u'BQC': 0.0, u'XPM': 0.0, u'IXC': 0.0, u'DBL': 0.0, u'ZEIT': 0.0, u'MAX': 0.0, u'ALF': 0.0, u'MZC': 0.0, u'PHS': 0.0, u'FST': 0.0, u'PYC': 0.0, u'FFC': 0.0, u'EMD': 0.0, u'BEN': 0.0, u'CMC': 0.0, u'CRC': 0.0, u'DEM': 0.0, u'FLO': 0.0, u'LKY': 0.0, u'YBC': 0.0, u'BET': 0.0, u'AMC': 0.0, u'BUK': 0.0, u'MEC': 0.0, u'OSC': 0.0, u'MNC': 0.0, u'PTS': 0.0, u'FLAP': 0.0, u'TRC': 0.0, u'CSC': 0.0, u'FTC': 0.0, u'LEAF': 0.0, u'ANC': 0.0, u'DOGE': 0.0, u'MOON': 0.0, u'BTE': 0.0, u'BTG': 0.0, u'NVC': 0.0, u'BTC': 0.0, u'BTB': 0.0, u'LK7': 0.0, u'GLC': 0.0, u'GLD': 0.0, u'NEC': 0.0, u'DVC': 0.0, u'GLX': 0.0, u'XNC': 0.0, u'BCX': 0.0, u'CTM': 0.0, u'NET': 0.0, u'SMC': 0.0, u'COL': 0.0, u'RED': 0.0, u'DGB': 0.0, u'DGC': 0.0, u'TEK': 0.0, u'CGB': 0.0, u'CASH': 0.0, u'KDC': 0.0, u'ASC': 0.0, u'NBL': 0.0, u'JKC': 0.0, u'FRC': 0.0, u'SRC': 0.0, u'ADT': 0.0, u'CAP': 0.0, u'FRK': 0.0, u'ELC': 0.0, u'GME': 0.0, u'LTC': 0.00140799, u'RDD': 0.0, u'AUR': 0.0, u'ELP': 0.0, u'MINT': 0.0, u'YAC': 0.0, u'UNO': 0.0, u'ZED': 0.0, u'MEM': 0.0, u'HVC': 0.0, u'SBC': 0.0, u'GDC': 0.0, u'NMC': 0.0, u'ZET': 0.0, u'TAK': 0.0, u'ORB': 0.0, u'BAT': 0.0, u'HYC': 0.0, u'MST': 0.0, u'IFC': 0.0, u'VTC': 0.0, u'CAT': 0.0, u'WDC': 0.0, u'LOT': 0.0, u'PPC': 0.0, u'DMD': 0.0, u'EAC': 0.0, u'QRK': 0.0, u'42': 0.0, u'TGC': 0.0, u'RPC': 0.0, u'PXC': 0.0, u'TIPS': 0.0, u'UTC': 0.0, u'CNC': 0.0, u'STR': 0.0, u'CACH': 0.0, u'ZCC': 0.0, u'NRB': 0.0, u'KGC': 0.0, u'Points': 6.45e-06, u'ARG': 0.0, u'POT': 0.0, u'EZC': 0.0}}
    d = {u'serverdatetime': u'2014-04-08 09:25:22', u'balances_available': {u'NYAN': u'0.00000000', u'EXE': u'0.00000000', u'TIX': u'0.00000000', u'BC': u'0.00000000', u'XJO': u'0.00000000', u'NAN': u'0.00000000', u'RYC': u'0.00000000', u'DRK': u'0.00000000', u'HBN': u'0.00000000', u'CPR': u'0.00000000', u'SXC': u'0.00000000', u'MEOW': u'0.00000000', u'SPT': u'0.00000000', u'CENT': u'0.00000000', u'TAG': u'0.00000000', u'YAC': u'0.00000000', u'LYC': u'0.00000000', u'SPA': u'0.00000000', u'SAT': u'0.00000000', u'NXT': u'0.00000000', u'BQC': u'0.00000000', u'XPM': u'0.00000000', u'IXC': u'0.00000000', u'DBL': u'0.00000000', u'ZEIT': u'0.00000000', u'MAX': u'0.00000000', u'MEM': u'0.00000000', u'MZC': u'0.00000000', u'PHS': u'0.00000000', u'FST': u'0.00000000', u'PYC': u'0.00000000', u'FFC': u'0.00000000', u'EMD': u'0.00000000', u'BEN': u'0.00000000', u'CMC': u'0.00000000', u'CRC': u'0.00000000', u'DEM': u'0.00000000', u'FLO': u'0.00000000', u'LKY': u'0.00000000', u'YBC': u'0.00000000', u'BET': u'0.00000000', u'AMC': u'0.00000000', u'BUK': u'0.00000000', u'OSC': u'0.00000000', u'MNC': u'0.00000000', u'PTS': u'0.00000000', u'FLAP': u'0.00000000', u'TRC': u'0.00000000', u'CSC': u'0.00000000', u'FTC': u'0.00000000', u'LEAF': u'0.00000000', u'ANC': u'0.00000000', u'DOGE': u'0.00000000', u'MOON': u'0.00000000', u'BTE': u'0.00000000', u'BTG': u'0.00000000', u'NVC': u'0.00000000', u'BTC': u'0.00000000', u'BTB': u'0.00000000', u'LK7': u'0.00000000', u'GLC': u'0.00000000', u'GLD': u'0.00000000', u'NEC': u'0.00000000', u'DVC': u'0.00000000', u'GLX': u'0.00000000', u'XNC': u'0.00000000', u'BCX': u'0.00000000', u'CTM': u'0.00000000', u'NET': u'0.00000000', u'SMC': u'0.00000000', u'COL': u'0.00000000', u'RED': u'0.00000000', u'DGB': u'0.00000000', u'DGC': u'0.00000000', u'TEK': u'0.00000000', u'CGB': u'0.00000000', u'CASH': u'0.00000000', u'KDC': u'0.00000000', u'ASC': u'0.00000000', u'NBL': u'0.00000000', u'JKC': u'0.00000000', u'FRC': u'0.00000000', u'SRC': u'0.00000000', u'ADT': u'0.00000000', u'MST': u'0.00000000', u'FRK': u'0.00000000', u'ELC': u'0.00000000', u'GME': u'0.00000000', u'LTC': u'0.05607079', u'RDD': u'0.00000000', u'AUR': u'0.00000000', u'ZED': u'0.00000000', u'ELP': u'0.00000000', u'MINT': u'0.00000000', u'CLR': u'0.00000000', u'UNO': u'0.00000000', u'MEC': u'0.00000000', u'ALF': u'0.00000000', u'HVC': u'0.00000000', u'SBC': u'0.00000000', u'GDC': u'0.00000000', u'NMC': u'0.00000000', u'ZET': u'0.00000000', u'TAK': u'0.00000000', u'ORB': u'0.00000000', u'BAT': u'0.00000000', u'HYC': u'0.00000000', u'CAP': u'0.00000000', u'IFC': u'0.00000000', u'VTC': u'0.00000000', u'CAT': u'0.00000000', u'WDC': u'0.00000000', u'LOT': u'0.00000000', u'PPC': u'0.00000000', u'DMD': u'0.00000000', u'EAC': u'0.00000000', u'QRK': u'0.00000000', u'42': u'0.00000000', u'TGC': u'0.00000000', u'RPC': u'0.00000000', u'PXC': u'0.00000000', u'TIPS': u'0.00000000', u'UTC': u'0.00000000', u'CNC': u'0.00000000', u'STR': u'0.00000000', u'CACH': u'0.00000000', u'ZCC': u'0.00000000', u'NRB': u'0.00000000', u'KGC': u'0.00000000', u'Points': u'0.00853000', u'ARG': u'0.00000000', u'POT': u'0.00000000', u'EZC': u'0.00000000'}, u'balances_hold': {u'PPC': u'45.68529191', u'XPM': u'16.36380436', u'MEM': u'200.00000000', u'Points': u'0.01064250', u'DOGE': u'34352.91600716', u'LTC': u'6.12378988', u'FTC': u'1.06459434', u'AUR': u'16.42351408', u'IFC': u'1139.05522289', u'TIPS': u'8204.37674000'}, u'servertimezone': u'EST', u'balances_hold_btc': {u'PPC': u'0.00000000', u'XPM': u'0.00000000', u'MEM': u'0.00000000', u'Points': u'0.00000000', u'DOGE': u'0.00000000', u'LTC': u'0.00000000', u'FTC': u'0.00000000', u'AUR': u'0.00000000', u'IFC': u'0.00000000', u'TIPS': u'0.00000000'}, u'openordercount': 33, u'servertimestamp': 1396963522, u'balances_available_btc': {u'NYAN': u'0.00000000', u'EXE': u'0.00000000', u'TIX': u'0.00000000', u'BC': u'0.00000000', u'XJO': u'0.00000000', u'NAN': u'0.00000000', u'RYC': u'0.00000000', u'DRK': u'0.00000000', u'HBN': u'0.00000000', u'CPR': u'0.00000000', u'SXC': u'0.00000000', u'MEOW': u'0.00000000', u'SPT': u'0.00000000', u'CENT': u'0.00000000', u'TAG': u'0.00000000', u'YAC': u'0.00000000', u'LYC': u'0.00000000', u'SPA': u'0.00000000', u'SAT': u'0.00000000', u'NXT': u'0.00000000', u'BQC': u'0.00000000', u'XPM': u'0.00000000', u'IXC': u'0.00000000', u'DBL': u'0.00000000', u'ZEIT': u'0.00000000', u'MAX': u'0.00000000', u'MEM': u'0.00000000', u'MZC': u'0.00000000', u'PHS': u'0.00000000', u'FST': u'0.00000000', u'PYC': u'0.00000000', u'FFC': u'0.00000000', u'EMD': u'0.00000000', u'BEN': u'0.00000000', u'CMC': u'0.00000000', u'CRC': u'0.00000000', u'DEM': u'0.00000000', u'FLO': u'0.00000000', u'LKY': u'0.00000000', u'YBC': u'0.00000000', u'BET': u'0.00000000', u'AMC': u'0.00000000', u'BUK': u'0.00000000', u'OSC': u'0.00000000', u'MNC': u'0.00000000', u'PTS': u'0.00000000', u'FLAP': u'0.00000000', u'TRC': u'0.00000000', u'CSC': u'0.00000000', u'FTC': u'0.00000000', u'LEAF': u'0.00000000', u'ANC': u'0.00000000', u'DOGE': u'0.00000000', u'MOON': u'0.00000000', u'BTE': u'0.00000000', u'BTG': u'0.00000000', u'NVC': u'0.00000000', u'BTC': u'0.00000000', u'BTB': u'0.00000000', u'LK7': u'0.00000000', u'GLC': u'0.00000000', u'GLD': u'0.00000000', u'NEC': u'0.00000000', u'DVC': u'0.00000000', u'GLX': u'0.00000000', u'XNC': u'0.00000000', u'BCX': u'0.00000000', u'CTM': u'0.00000000', u'NET': u'0.00000000', u'SMC': u'0.00000000', u'COL': u'0.00000000', u'RED': u'0.00000000', u'DGB': u'0.00000000', u'DGC': u'0.00000000', u'TEK': u'0.00000000', u'CGB': u'0.00000000', u'CASH': u'0.00000000', u'KDC': u'0.00000000', u'ASC': u'0.00000000', u'NBL': u'0.00000000', u'JKC': u'0.00000000', u'FRC': u'0.00000000', u'SRC': u'0.00000000', u'ADT': u'0.00000000', u'MST': u'0.00000000', u'FRK': u'0.00000000', u'ELC': u'0.00000000', u'GME': u'0.00000000', u'LTC': u'0.00140799', u'RDD': u'0.00000000', u'AUR': u'0.00000000', u'ZED': u'0.00000000', u'ELP': u'0.00000000', u'MINT': u'0.00000000', u'CLR': u'0.00000000', u'UNO': u'0.00000000', u'MEC': u'0.00000000', u'ALF': u'0.00000000', u'HVC': u'0.00000000', u'SBC': u'0.00000000', u'GDC': u'0.00000000', u'NMC': u'0.00000000', u'ZET': u'0.00000000', u'TAK': u'0.00000000', u'ORB': u'0.00000000', u'BAT': u'0.00000000', u'HYC': u'0.00000000', u'CAP': u'0.00000000', u'IFC': u'0.00000000', u'VTC': u'0.00000000', u'CAT': u'0.00000000', u'WDC': u'0.00000000', u'LOT': u'0.00000000', u'PPC': u'0.00000000', u'DMD': u'0.00000000', u'EAC': u'0.00000000', u'QRK': u'0.00000000', u'42': u'0.00000000', u'TGC': u'0.00000000', u'RPC': u'0.00000000', u'PXC': u'0.00000000', u'TIPS': u'0.00000000', u'UTC': u'0.00000000', u'CNC': u'0.00000000', u'STR': u'0.00000000', u'CACH': u'0.00000000', u'ZCC': u'0.00000000', u'NRB': u'0.00000000', u'KGC': u'0.00000000', u'Points': u'0.00000645', u'ARG': u'0.00000000', u'POT': u'0.00000000', u'EZC': u'0.00000000'}}
#     pprint(d)
    d = convert_recursive(d)
    pprint(d)
