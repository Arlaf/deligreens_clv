#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 13:06:35 2018

@author: arnaud
"""

import dash_core_components as dcc
import dash_html_components as html

def generate_html():
    layout = html.Div([
        html.P('Superbe seconde page !!'),
        dcc.Link('Retour à l\'index', href = '/')
    ])
    return layout