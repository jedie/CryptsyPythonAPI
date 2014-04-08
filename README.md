CryptsyPythonAPI
================

API for Cryptsy.com Exchange utilizing completely built-in functions and utilities of Python 2.7.

Note: the next version of this API wrapper will introduce A LOT of API changes
so be warned, here be dragons.

[![Dependency Status](https://gemnasium.com/jaapz/CryptsyPythonAPI.png)](https://gemnasium.com/jaapz/CryptsyPythonAPI)
[![Build Status](https://api.travis-ci.org/jaapz/CryptsyPythonAPI.png)](https://travis-ci.org/jaapz/CryptsyPythonAPI)
[![PyPI Version](https://pypip.in/v/Cryptsy/badge.png)](https://pypi.python.org/pypi/Cryptsy)
[![Coverage Status](https://coveralls.io/repos/jaapz/CryptsyPythonAPI/badge.png?branch=develop)](https://coveralls.io/r/jaapz/CryptsyPythonAPI?branch=develop)

Author's Note
-------------
This API wrapper is a fork of [ScriptProdigy's CryptsyPythonAPI](https://github.com/ScriptProdigy/CryptsyPythonAPI).

Example Usage
-------------
Create buy order for dgc, market id 26, then cancels all orders you have for dgc
```python
from Cryptsy import Api
exchange = Api('KEY HERE', 'SECRET HERE')
print(exchange.buy(26, 100, 0.00000001))       # Buy 100 dgc at .00000001 each
print(exchange.cancel_all_market_orders(26))   # Cancels all orders in market 26, dgc
```

High-Level API
--------------

Access crypsy API in a higher level:

 * All int, floar and datetime objects are evaluated (and not only raw strings)
 * Optional display all requests with response time
 * Additional objects like:
   * AccountBalance

High-Level API Example
----------------------
```python
from Cryptsy import HighLevelApi
api = HighLevelApi(
    your_api_key, your_secret,
    verbose=True # display all requests with response time
)
balance = api.get_balance() # Get AccountBalance instance
balance.print_balance() # print your balance

print api.last_raw_result # print raw dict of last request
```

Changelog
---------
Version 0.2:

 * moved from camelCase names to python_style names
 * added new methods: `buy`, `sell`, `my_transfers`, `wallet_status`, `make_withdrawal`
 * started implementing tests
 * nonce is now in milliseconds instead of seconds, to support multiple calls
   per second.

Todo
----
Some things that I intend to add in future versions:

 * MOAR TESTS
 * sphinx reference generation
 * error handling
 * add some unofficial api endpoints because the official ones may suck
 * add travis ci builds

Running the tests
-----------------
If you want to run the tests, first create a virtualenv and install all
requirements.

    virtualenv .env
    . .env/bin/activate
    pip install -r requirements.txt

Then, using pytest, run the tests:

    py.test test_cryptsy.py

Or with coverage reports:

    py.test --cov Cryptsy.py test_cryptsy.py

Development
----------
Development is done in the obviously named develop branch. If you want to
contribute, please do your commits in that branch so merging them isn't a
pain.

Donate
------
Support development by tipping me a beer (because programming with beer is
inherently better than programming without)!

[![Support via Gittip](https://rawgithub.com/chris---/Donation-Badges/master/gittip.jpeg)](https://www.gittip.com/jaapz)

License
-------
This piece of software is licensed under the GPL2 license, see `license`.
