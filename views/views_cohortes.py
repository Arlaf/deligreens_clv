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
        html.Button(id = 'button_valider', n_clicks = 0, children = 'Valider', style = {'margin' : '0px 0px 0px 10px'}),
        html.Div([
            html.Div([
                html.Label('Mesure à afficher'),
                dcc.Dropdown(id = 'dropdown_mesure', clearable = False, options = [{'label' : 'Gross revenue', 'value' : 'gross_revenue'},
                                                                                   {'label' : 'Gross revenue par client', 'value' : 'gross_revenue_cli'},
                                                                                   {'label' : 'Nombre de clients', 'value' : 'nb_cli'},
                                                                                   {'label' : 'Nombre de commandes', 'value' : 'nb_com'},
                                                                                   {'label' : 'Nombre de commandes par client', 'value' : 'nb_com_cli'},
                                                                                   {'label' : 'Panier moyen', 'value' : 'panier_moyen'}], value = 'gross_revenue')
        ], className = 'three columns'),
            html.Div([
                html.Label('Afficher'),
                dcc.RadioItems(
                    id = 'radio_affichage',
                    value = 'valeur',
                    options = [{'label' : 'les valeurs', 'value' : 'valeur'},
                               {'label' : 'en pourcentage du 1er mois', 'value' : 'pct_total'},
                               {'label' : 'en pourcentage du mois précédent', 'value' : 'pct_relatif'}])
            ], className = 'three columns')
        ], className = 'row', style = {'margin' : '10px 0px 10px 0px'}),
        html.Div(id = 'tableau_evolution_cohortes'),
        html.Label('Les ~ ~ indiquent des valeurs qui sont encore susceptibles d\'augmenter', style = {'text-align' : 'right'}),
        dcc.Graph(id = 'graph_cohortes2'),
    
        # Divs invisibles qui stockeront les données intermédiaires
        html.Div(id = 'stock_commandes_filtered2', style = {'display': 'none'}),
        html.Div(id = 'stock_tableau_cohortes2', style = {'display': 'none'})
    ], style = {'margin' : '15px'})
    return layout