import requests
import json
import hmac
import base64
import time
import datetime
import okex.exceptions as exceptions


class Client(object):

    API_URL = 'https://www.okex.com'
    CONTENT_TYPE = 'Content-Type'
    OK_ACCESS_KEY = 'OK-ACCESS-KEY'
    OK_ACCESS_SIGN = 'OK-ACCESS-SIGN'
    OK_ACCESS_TIMESTAMP = 'OK-ACCESS-TIMESTAMP'
    OK_ACCESS_PASSPHRASE = 'OK-ACCESS-PASSPHRASE'


    ACEEPT = 'Accept'
    COOKIE = 'Cookie'
    LOCALE = 'Locale='

    APPLICATION_JSON = 'application/json'

    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"

    SERVER_TIMESTAMP_URL = '/api/futures/v3/time'

    CURRENCIES_INFO = '/api/account/v3/currencies'
    WALLET_INFO = '/api/account/v3/wallet'
    CURRENCY_INFO = '/api/account/v3/wallet/'
    COIN_TRANSFER = '/api/account/v3/transfer'
    COIN_WITHDRAW = '/api/account/v3/withdrawals'
    COIN_FEE = '/api/account/v3/withdrawal/fee'
    COINS_WITHDRAW_RECORD = '/api/account/v3/withdrawal/history'
    COIN_WITHDRAW_RECORD = '/api/account/v3/withdrawal/history/'
    LEDGER_RECORD = '/api/account/v3/ledger'
    TOP_UP_ADDRESS = '/api/account/v3/deposit/address'
    COIN_TOP_UP_RECORDS = '/api/account/v3/deposit/history'
    COIN_TOP_UP_RECORD = '/api/account/v3/deposit/history/'

    SPOT_ACCOUNT_INFO = '/api/spot/v3/accounts'
    SPOT_COIN_ACCOUNT_INFO = '/api/spot/v3/accounts/'
    SPOT_LEDGER_RECORD = '/api/spot/v3/accounts/'
    SPOT_ORDER = '/api/spot/v3/orders'
    SPOT_REVOKE_ORDER = '/api/spot/v3/cancel_orders/'
    SPOT_REVOKE_ORDERS = '/api/spot/v3/cancel_batch_orders'
    SPOT_ORDERS_LIST = '/api/spot/v3/orders'
    SPOT_ORDER_INFO = '/api/spot/v3/orders/'
    SPOT_FILLS = '/api/spot/v3/fills'
    SPOT_COIN_INFO = '/api/spot/v3/products'
    SPOT_DEPTH = '/api/spot/v3/products/'
    SPOT_TICKER = '/api/spot/v3/products/ticker'
    SPOT_SPECIFIC_TICKER = '/api/spot/v3/products/'
    SPOT_DEAL = '/api/spot/v3/products/'
    SPOT_KLINE = '/api/spot/v3/products/'

    def __init__(self, api_key, api_seceret_key, passphrase, use_server_time=True):

        self.API_KEY = api_key
        self.API_SECRET_KEY = api_seceret_key
        self.PASSPHRASE = passphrase
        self.use_server_time = use_server_time


    def _request(self, method, request_path, params, cursor=False):

        
        request_path = request_path + self.parse_params_to_str(params)
        # url
        url = self.API_URL + request_path

        timestamp = self.get_timestamp()
        # sign & header
        if self.use_server_time:
            timestamp = self._get_timestamp()
        body = json.dumps(params) if method == self.POST else ""

        sign = self.sign(self.pre_hash(timestamp, method, request_path, str(body)), self.API_SECRET_KEY)
        header = self.get_header(self.API_KEY, sign, timestamp, self.PASSPHRASE)

        # send request
        response = None
        if method == self.GET:
            response = requests.get(url, headers=header)
        elif method == self.POST:
            response = requests.post(url, data=body, headers=header)
        elif method == self.DELETE:
            response = requests.delete(url, headers=header)

        # exception handle
        if not str(response.status_code).startswith('2'):
            raise exceptions.OkexAPIException(response)
        try:
            res_header = response.headers
            if cursor:
                r = dict()
                try:
                    r['before'] = res_header['OK-BEFORE']
                    r['after'] = res_header['OK-AFTER']
                except:
                    print("分页错误")
                return response.json(), r
            else:
                return response.json()
        except ValueError:
            raise exceptions.OkexRequestException('Invalid Response: %s' % response.text)

    def _request_without_params(self, method, request_path):
        return self._request(method, request_path, {})

    def _request_with_params(self, method, request_path, params, cursor=False):
        return self._request(method, request_path, params, cursor)

    def _get_timestamp(self):
        url = self.API_URL + self.SERVER_TIMESTAMP_URL
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['iso']
        else:
            return ""
    
    def sign(self,message, secretKey):
        mac = hmac.new(bytes(secretKey, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
        d = mac.digest()
        return base64.b64encode(d)


    def pre_hash(self,timestamp, method, request_path, body):
        return str(timestamp) + str.upper(method) + request_path + body


    def get_header(self,api_key, sign, timestamp, passphrase):
        header = dict()
        header[self.CONTENT_TYPE] = self.APPLICATION_JSON
        header[self.OK_ACCESS_KEY] = api_key
        header[self.OK_ACCESS_SIGN] = sign
        header[self.OK_ACCESS_TIMESTAMP] = str(timestamp)
        header[self.OK_ACCESS_PASSPHRASE] = passphrase

        return header


    def parse_params_to_str(self,params):
        url = '?'
        for key, value in params.items():
            url = url + str(key) + '=' + str(value) + '&'

        return url[0:-1]


    def get_timestamp(self):
        now = datetime.datetime.now()
        t = now.isoformat()
        return t + "Z"


    def signature(self,timestamp, method, request_path, body, secret_key):
        if str(body) == '{}' or str(body) == 'None':
            body = ''
        message = str(timestamp) + str.upper(method) + request_path + str(body)
        mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
        d = mac.digest()
        return base64.b64encode(d)
            
    def get_account_info(self):
        return self._request_without_params(self.GET, self.SPOT_ACCOUNT_INFO)

    def get_coin_account_info(self, symbol):
        return self._request_without_params(self.GET, self.SPOT_COIN_ACCOUNT_INFO + str(symbol))

    # query ledger record not paging
    def get_ledger_record(self, symbol, limit=1):
        params = {}
        if limit:
            params['limit'] = limit
        return self._request_with_params(self.GET, self.SPOT_LEDGER_RECORD + str(symbol) + '/ledger', params)

    # query ledger record with paging
    #def get_ledger_record_paging(self, symbol, before, after, limit):
    #    params = {'before': before, 'after': after, 'limit': limit}
    #    return self._request_with_params(GET, SPOT_LEDGER_RECORD + str(symbol) + '/ledger', params, cursor=True)

    # take order
    def take_order(self, otype, side, instrument_id, size, margin_trading=1, client_oid='', price='', funds='', ):
        params = {'type': otype, 'side': side, 'instrument_id': instrument_id, 'size': size, 'client_oid': client_oid,
                  'price': price, 'funds': funds, 'margin_trading': margin_trading}
        return self._request_with_params(self.POST, self.SPOT_ORDER, params)

    # revoke order
    def revoke_order(self, oid, instrument_id):
        params = {'instrument_id': instrument_id}
        return self._request_with_params(self.POST, self.SPOT_REVOKE_ORDER + str(oid), params)

    # revoke orders
    def revoke_orders(self, instrument_id, order_ids):
        params = {'instrument_id': instrument_id, 'order_ids': order_ids}
        return self._request_with_params(self.POST, self.SPOT_REVOKE_ORDERS, params)

    # query orders list
    #def get_orders_list(self, status, instrument_id, before, after, limit):
    #    params = {'status': status, 'instrument_id': instrument_id, 'before': before, 'after': after, 'limit': limit}
    #    return self._request_with_params(GET, SPOT_ORDERS_LIST, params, cursor=True)

    # query orders list v3
    def get_orders_list(self, status, instrument_id, froms='', to='', limit='100'):
        params = {'status': status, 'instrument_id': instrument_id, 'limit': limit}
        if froms:
            params['from'] = froms
        if to:
            params['to'] = to
        if instrument_id:
            params['instrument_id'] = instrument_id
        return self._request_with_params(self.GET, self.SPOT_ORDERS_LIST, params, cursor=True)

    # query order info
    def get_order_info(self, oid, instrument_id):
        params = {'instrument_id': instrument_id}
        return self._request_with_params(self.POST, self.SPOT_ORDER_INFO + str(oid), params)

    # query fills
    #def get_fills(self, order_id, instrument_id, before, after, limit):
    #    params = {'order_id': order_id, 'instrument_id': instrument_id, 'before': before, 'after': after, 'limit': limit}
    #    return self._request_with_params(GET, SPOT_FILLS, params, cursor=True)

    def get_fills(self, order_id, instrument_id, froms, to, limit='100'):
        params = {'order_id': order_id, 'instrument_id': instrument_id, 'from': froms, 'to': to, 'limit': limit}
        return self._request_with_params(self.GET, self.SPOT_FILLS, params, cursor=True)

    # query spot coin info
    def get_coin_info(self):
        return self._request_without_params(self.GET, self.SPOT_COIN_INFO)

    # query depth
    def get_depth(self, instrument_id, size='', depth=''):
        params = {}
        if size:
            params['size'] = size
        if depth:
            params['depth'] = depth
        print(params)
        return self._request_with_params(self.GET, self.SPOT_DEPTH + str(instrument_id) + '/book', params)

    # query ticker info
    def get_ticker(self):
        return self._request_without_params(self.GET, self.SPOT_TICKER)

    # query specific ticker
    def get_specific_ticker(self, instrument_id):
        return self._request_without_params(self.GET, self.SPOT_SPECIFIC_TICKER + str(instrument_id) + '/ticker')

    # query spot deal info
    #def get_deal(self, instrument_id, before, after, limit):
    #    params = {'before': before, 'after': after, 'limit': limit}
    #    return self._request_with_params(GET, SPOT_DEAL + str(instrument_id) + '/trades', params)

    def get_deal(self, instrument_id, froms, to, limit):
        params = {'from': froms, 'to': to, 'limit': limit}
        return self._request_with_params(self.GET, self.SPOT_DEAL + str(instrument_id) + '/trades', params)

    # query k-line info
    def get_kline(self, instrument_id, start, end, granularity):
        params = {'start': start, 'end': end, 'granularity': granularity}
        return self._request_with_params(self.GET, self.SPOT_KLINE + str(instrument_id) + '/candles', params)




