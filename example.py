#!/usr/bin/env python

from datetime import datetime
from datetime import date

from pyoptionquote import CachedOptionQuote


optionquote = CachedOptionQuote()

# get all options data for C 
data = optionquote.get_options('C')

# get jan-11 options with strike > 5
exp = date(2011, 1, 1)
data = optionquote.get_options('C', expirations=[exp], strike=lambda x:x<5)
print 'C jan-11 options with strike < 5'
for option in data:
    print option, data[option]

# get specific options
data = optionquote.get_options('C', options=['COB.X', 'CCB.X'])
print 'COB.X and CCB.X'
for option in data:
    print option, data[option]


