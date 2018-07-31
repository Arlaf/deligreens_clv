#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime

def lastday_of_month(d):
    #Takes a datetime.date and returns the date for the last day in the same month.
    return datetime.date(d.year, d.month+1, 1) - datetime.timedelta(1)

def AddMonths(d,x):
    # Ajoute x mois à la date d (x peut être négatif)
    newmonth = ((( d.month - 1) + x ) % 12 ) + 1
    newyear  = d.year + ((( d.month - 1) + x ) // 12 )
    # Si le numéro du jour ne rentre pas dans le mois on prend le dernier jour du mois
    if d.day > lastday_of_month(datetime.date(newyear, newmonth, 1)).day:
        newday = lastday_of_month(datetime.date(newyear, newmonth, 1)).day
    else:
        newday = d.day
    return datetime.date( newyear, newmonth, newday)