#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 13:06:35 2018

@author: arnaud
"""

import dash_core_components as dcc
import dash_html_components as html
import datetime

def generate_html():
    layout = html.Div([
        dcc.Link('Retour à l\'index', href = '/'),
        html.H1('Power User Curve'),
        html.Label('Plage de date à étudier'),
        dcc.DatePickerRange(
            id='date_range_commandes',
            display_format = 'DD/MM/YY',
            start_date = datetime.date(2018, 4, 2),
            end_date = datetime.date(2018,7,1)
        ),
        html.Label('Etudier les clients arrivés entre'),
        dcc.DatePickerRange(
            id='date_range_clients',
            display_format = 'DD/MM/YY',
            start_date = datetime.date(2018, 1, 1),
            end_date = datetime.date(2018, 3, 31)
        ),
        html.Button(id = 'button_valider', n_clicks = 0, children = 'Valider'),
        dcc.Checklist(
            id = 'checkbox_cohorte',
            options = [{'label' : 'Distinguer les cohortes', 'value' : 'use_cohorts'}],
            values = []
        ),
        dcc.Graph(id = 'graph_puc'),
        
        # Divs invisibles qui stockeront les données intermédiaires
        html.Div(id = 'stock_commandes_filtered', style = {'display': 'none'})
    ])
    return layout