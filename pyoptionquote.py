#!/usr/bin/env python
# 
# @author: kefei dan zhou
# @date: 09-17-2009
#
#

import os
import sys
import urllib
import time
import copy
from parsers import ExpirationParser, OptionParser


def normalize_option_data(data, expiration):
    options = {}
    for line in data:
        options[line[0]] = {
            'type': 'C',
            'strike': float(line[8]),
            'last': float(line[1]),
            'change': float(line[3]),
            'bid': float(line[4]),
            'ask': float(line[5]),
            'volume': int(line[6]),
            'open_int': int(line[7]),
            'expiration': expiration,
        }

        options[line[9]] = {
            'type': 'P',
            'strike': float(line[8]),
            'last': float(line[10]),
            'change': float(line[12]),
            'bid': float(line[13]),
            'ask': float(line[14]),
            'volume': int(line[15]),
            'open_int': int(line[16]),
            'expiration': expiration,
        }

    return options


class OptionQuote(object):
    def __init__(self):
        self._expr_url = 'http://finance.yahoo.com/q/os?s=%s'
        self._option_url = "http://finance.yahoo.com/q/os?s=%s&m=%s"
        self._exp_parser = ExpirationParser()
        self._option_parser = OptionParser()

    def _convert_exp2str(self, expr):
        """
        Convert date object to YYYY-MM string format 
        @param expr expiration date as python DateTime object
        """
        return expr.strftime('%Y-%m')

    def _get_option_expirations(self, underlying):
        """
        Parser the main option page for list of expirations dates
        @param symbol symbol of the underlying stock
        @return list of expiration dates as Datetime obj
        """
        url = self._expr_url % underlying
        data = urllib.urlopen(url).read()
        self._exp_parser.reset()
        self._exp_parser.feed(data)
        self._exp_parser.close()
        return self._exp_parser.expirations

    def _get_option_by_expr(self, underlying, expr):
        """
        Parser yahoo option page for data
        @param underlying stock
        @param expr expiration date in YYYY-MM string format
        @return dict of option data for the given stock/expiration date
        """
        url = self._option_url % (underlying, expr)
        data = urllib.urlopen(url).read()
        self._option_parser.reset()
        self._option_parser.feed(data)
        self._option_parser.close()
        return normalize_option_data(self._option_parser.data[1:-1], expr)


class CachedOptionQuote(OptionQuote):
    def __init__(self, cache_timeout=60*60):
        """
        Caching layer on top of OptionQuote. 
        @param cache_timeout: Max time in second to keep data in cache. default
        to 1hour.
        """
        OptionQuote.__init__(self)
        self._cache = {}
        self._expirations = {}
        self._refresh_time = {}
        self._cache_timeout = cache_timeout

    def _get_option_expirations(self, underlying, force_reload=False):
        """
        Get expiration dates for the given stock, try to use cache if possible
        @param force_reload if false try to get data from cache first
        @return list of expiration dates as Datetime obj
        """
        if not force_reload and underlying in self._expirations:
            exps = self._expirations[underlying]
        else:
            exps = OptionQuote._get_option_expirations(self, underlying)
            self._expirations[underlying] = exps
        return exps

    def _get_option_by_expr(self, underlying, exp, force_reload=False):
        """
        Get data for option, try to use cache if possible
        @param force_reload if false try to get data from cache first
        @return dict of option data for the given stock/expiration date
        """
        if (not force_reload and (underlying,exp) in self._cache and
            time.time()-self._refresh_time[(underlying,exp)] < self._cache_timeout):
            options = self._cache[(underlying,exp)]
        else:
            options = OptionQuote._get_option_by_expr(self, underlying, exp)
            self._cache[(underlying,exp)] = options
            self._refresh_time[(underlying, exp)] = time.time()
        return options

    def get_options(self, underlying, options=[], expirations=[], 
            strike=lambda x:True, force_reload=False):
        """
        The main interface for retrieving option data. This function will return
        deepcopy of the data and store original in cache for future use
        @param underlying: stock symbol to retrieve option data for
        @param options: filter the results for only these options. if the list
            is empty, this param is ignored 
        @param expirations: filter the results for only these expirations. if
            the iterable is empty, this param is ignored
        @param strike: lambda function for selecting by strike price.
            default is select all. ex: lambda x:x>100 selects options with strike>100
        """
        result_set = {}
        if len(expirations) == 0:
            expirations = self._get_option_expirations(underlying)
        for exp in expirations:
            data = self._get_option_by_expr(underlying,
                    self._convert_exp2str(exp), force_reload)
            result_set.update(data)

        # filter for options
        for p in result_set.keys():
            if not strike(result_set[p]['strike']):
                del result_set[p]
        # filter for strike price and make deepcopy at same time
        if len(options) > 0:
            result_set2 = {}
            for p in options:
                if p in result_set:
                    result_set2[p] = copy.deepcopy(result_set[p])
            return result_set2
        else:
            return copy.deepcopy(result_set)
