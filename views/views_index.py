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
        dcc.Link('Customer Lifetile Value', href = '/apps/app_clv'),
        html.Br(),
        dcc.Link('Power User Curve', href = '/apps/app_puc')
    ])
    
    return layout