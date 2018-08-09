# -*- coding: utf-8 -*-

import dash_html_components as html
import datetime

# Date d'aujourd'hui
ajd = datetime.datetime.today().date()

# Format d'affichage des montants
def format_montant(nb):
    return ['{:,.2f}'.format(x).replace(',', ' ') + ' €' for x in nb]

# Format d'affichage des pourcentages
def format_pct(pct):
    return '{:.1f}'.format(100*pct)

def generate_table(dataframe, max_rows=20):
    #Given dataframe, return template generated using Dash components
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )
    
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
