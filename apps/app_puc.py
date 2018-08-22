#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 13:12:05 2018

@author: arnaud
"""

import dash_core_components as dcc
import dash_html_components as html
from models.services import module_puc
from dash.dependencies import Input, Output, State
import datetime

from app import app, commandes

puc = module_puc.PUC(commandes)

@app.callback(
    Output('graph_puc','figure'),
    [Input('button_valider','n_clicks')],
    [State('date_range_commandes','start_date'),
     State('date_range_commandes','end_date'),
     State('date_range_clients','start_date'),
     State('date_range_clients','end_date'),
     State('checkbox_cohorte','values')])
def maj_graph_puc(n_clicks, start_date_com, end_date_com, start_date_cli, end_date_cli, checkbox):
    # Correction du typage des inputs
    start_date_com = datetime.datetime.strptime(start_date_com, '%Y-%m-%d').date()
    end_date_com = datetime.datetime.strptime(end_date_com, '%Y-%m-%d').date()
    start_date_cli = datetime.datetime.strptime(start_date_cli, '%Y-%m-%d').date()
    end_date_cli = datetime.datetime.strptime(end_date_cli, '%Y-%m-%d').date()
    
    use_cohorts = not checkbox == []
    
    figure = puc.graph_puc_construct(start_date_com, end_date_com, start_date_cli, end_date_cli, use_cohorts)
    
    return figure