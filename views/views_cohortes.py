#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 30 14:45:49 2018

@author: arnaud
"""

import dash_core_components as dcc
import dash_html_components as html
import datetime
import utilitaires as util

def generate_html():
    layout = html.Div([
        dcc.Link('Retour à l\'index', href = '/'),
        html.H1('Analyse des cohortes'),
        html.Label('Sélection des cohortes (bien inclure le 1er jour du mois)'),
        dcc.DatePickerRange(
            id='date_range_cohortes',
            display_format = 'DD/MM/YY',
            start_date = datetime.date(util.ajd.year-1, util.ajd.month, 1),
            end_date = util.ajd
        ),
        html.Button(id = 'button_valider', n_clicks = 0, children = 'Valider', style = {'margin' : '0px 0px 0px 5px'}),
        html.Label('Mesure à afficher', style = {'margin' : '10px 0px 0px 0px'}),
        html.Div([
            dcc.Dropdown(id = 'dropdown_mesure', clearable = False, options = [{'label' : 'Gross revenue', 'value' : 'gross_revenue'},
                                                                               {'label' : 'Gross revenue par client', 'value' : 'gross_revenue_cli'},
                                                                               {'label' : 'Nombre de clients', 'value' : 'nb_cli'},
                                                                               {'label' : 'Nombre de commandes', 'value' : 'nb_com'},
                                                                               {'label' : 'Nombre de commandes par client', 'value' : 'nb_com_cli'},
                                                                               {'label' : 'Panier moyen', 'value' : 'panier_moyen'}], value = 'gross_revenue')
        ], style = {'maxWidth':'300px'}),
        html.Div(id = 'tableau_evolution_cohortes'),
    
        # Divs invisibles qui stockeront les données intermédiaires
        html.Div(id = 'stock_commandes_filtered2', style = {'display': 'none'}),
        html.Div(id = 'stock_tableau_cohortes2', style = {'display': 'none'})
    ])
    return layout