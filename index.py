#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 11:37:45 2018

@author: arnaud
"""

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from views import views_clv, views_index, views_puc

from app import app
from apps import app_clv, app_puc # Nécessaire même si non utilisé, meilleure méthode à trouver

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return views_index.generate_html()
    elif pathname == '/apps/app_clv':
        return views_clv.generate_html()
    elif pathname == '/apps/app_puc':
        return views_puc.generate_html()
    else:
        return '404'

if __name__ == '__main__':
    app.run_server(debug=True)