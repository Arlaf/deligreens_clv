#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 30 14:48:36 2018

@author: arnaud
"""

from models.services import module_cohorte_analysis
import datetime
from dash.dependencies import Input, Output, State
import utilitaires as util

from app import app, commandes

cohortes = module_cohorte_analysis.CohorteAnalysis(commandes)

@app.callback(
    Output('stock_commandes_filtered2', 'children'),
    [Input('button_valider', 'n_clicks')],
    [State('date_range_cohortes','start_date'),
     State('date_range_cohortes','end_date')])
def maj_commandes_filtered(n_clicks, start_date, end_date):
    # Correction du typage des inputs
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

    commandes_filtered = cohortes.selection_cohortes(start_date, end_date)
    
    return commandes_filtered.to_json(date_format = 'iso', orient = 'split')

@app.callback(
    Output('stock_tableau_cohortes2', 'children'),
    [Input('stock_commandes_filtered2','children'),
     Input('dropdown_mesure','value')])
def maj_tableau_cohortes(df_cohortes_json, mesure):
    tableau_cohortes = cohortes.tableau_cohortes_construct(df_cohortes_json, mesure)
    return tableau_cohortes.to_json(date_format = 'iso', orient = 'split')

@app.callback(
    Output('tableau_evolution_cohortes', 'children'),
    [Input('stock_tableau_cohortes2', 'children')],
    [State('dropdown_mesure','value')])
def affich_tableau_cohortes(tableau_cohortes_json, mesure):
    tableau = cohortes.tableau_cohortes_affich(tableau_cohortes_json, mesure)
    return util.generate_table(tableau)
    