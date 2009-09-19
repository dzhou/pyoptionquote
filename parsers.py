#!/usr/bin/env python
#
# @author: kefei dan zhou
# @date: 09-17-2009
#
#

import time
from datetime import datetime
from HTMLParser import HTMLParser


class OptionParser(HTMLParser):
    def __init__(self):
        """
        Parse Yahoo option page to get option data.
        This parse pages of straddle view by expiration dates. example page:
        'http://finance.yahoo.com/q/os?s=C'
        """
        HTMLParser.__init__(self)
        self.reset()

    def reset(self):
        """
        Reset parser. Must be called if parser is used for more than one HTML
        page
        """
        HTMLParser.reset(self)
        self.data = [[]]
        self.record = False

    def handle_starttag(self, tag, attrs):
        if tag == 'tr' and len(self.data[-1]) > 0:
            self.data.append([])
        if tag == 'table':
            self.record = False

    def handle_data(self, data):
        """
        Note: start at field 'Open Int' and end when we reach the next table
        data process:
        1. Remove comma in large integers
        2. Any N/A data field will be converted to -1 to simplify the float
        conversion later on
        """
        if data == 'Open Int':
            self.record = True

        if self.record:
            if data == 'N/A':
                self.data[-1].append(-1)
            else:
                self.data[-1].append(data.replace(',',''))


class ExpirationParser(HTMLParser):
    def __init__(self):
        """
        Parse Yahoo option page for expiration dates
        """
        HTMLParser.__init__(self)
        self.reset()

    def reset(self):
        """
        Reset parser. Must be called if parser is used for more than one HTML
        page
        """
        HTMLParser.reset(self)
        self.record = False
        self.expirations = []

    def handle_data(self, data):
        """
        Note: expiration dates are located btw 'View By Expiration' line and option
        table starting with field 'Symbol'
        """
        if data.find('View By Expiration') > -1:
            self.record = True
        elif data == 'Symbol':
            self.record = False

        if self.record:
            try:
                self.expirations.append(datetime.strptime(data,"%b %y"))
            except:
                pass
