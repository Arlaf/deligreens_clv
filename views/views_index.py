#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 13:03:48 2018

@author: arnaud
"""

import dash_core_components as dcc
import dash_html_components as html

def generate_html():
    layout = html.Div([
        html.Div([
            html.H1("Dashboard sur les clients de Deligreens", style = {'text-align' : 'center', 'margin-top' : '15%'})
        ]),
        html.Div([
            dcc.Link('Customer Lifetime Value', href = '/apps/app_clv', style = {'margin-right' : '20px'}),
            dcc.Link('Power User Curve', href = '/apps/app_puc', style = {'margin-right' : '20px'}),
            dcc.Link('Analyse des cohortes', href = '/apps/app_cohortes')
        ], style = {'max-width' : '700px', 'text-align' : 'center', 'margin' : '0 auto'})
    ])
    
    return layout