# -*- coding: utf-8 -*-

#import gunicorn
#import fonctions_core_bd as fcore
#import fonctions_dates as fdate
import pandas as pd
#import numpy as np
import datetime
#import math
import os
import dash
import dash_auth
from dash.dependencies import Input, Output, State
import utilitaires as util

from model import df_commandes
from model.services import methode_geo
from model.services import methode_cohortes
import views

# Pour avoir les dates en français
import locale
locale.setlocale(2,'')

commandes = df_commandes.Commandes().commandes
geo = methode_geo.MethodeGeo(commandes)
cohortes = methode_cohortes.Cohortes(commandes)

# Déclaration de l'application    
app = dash.Dash('auth')
auth = dash_auth.BasicAuth(app,
                           [[os.environ['appuser'], os.environ['apppass']]])

views.generate_html(app)

server = app.server

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})



######################## Controller

# Construction du df allcli
@app.callback(
    Output('stock_allcli','children'),
    [Input('button_valider', 'n_clicks')],
    [State('input_Nmois', 'value'),
     State('date_range','start_date'),
     State('date_range','end_date')])
def maj_allcli(n_clicks, Nmois, start_date, end_date):
    # Correction du typage des inputs
    Nmois = int(Nmois)
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Création du dataframe des clients
    allcli = geo.allcli_construct(Nmois, start_date)
    
    return allcli.to_json(date_format = 'iso', orient = 'split')

# Construction du tableau de la méthode géométrique
@app.callback(
    Output('stock_tableau_geo', 'children'),
    [Input('stock_allcli', 'children')],
    [State('input_Nmois', 'value'),
     State('segmentation_nb_com', 'value')])
def tableau_geo(allcli_json, Nmois, segmentation):
    # Correction du typage des inputs
    Nmois = int(Nmois)
    
    tableau = geo.methode_geometrique_tableau(allcli_json, Nmois, segmentation)
    return tableau.to_json(date_format = 'iso', orient = 'split')
    
    
    
# Affichage du tableau de la méthode géométrique
@app.callback(
    Output('tableau_groupes_value','children'),
    [Input('stock_tableau_geo','children')])
def affich_tableau_geo(tableau_json):
    tableau = pd.read_json(tableau_json, orient = 'split')
    
    # Format d'affichage des nombres
    for col in tableau.drop(['Proportion'],axis = 1).select_dtypes(include = ['float64']):
        tableau[col] = util.format_montant(tableau[col])
        
    # Format d'affichage des pourcentages
    tableau['Proportion'] = [util.format_pct(x) + ' %' for x in tableau['Proportion']]
    
    return util.generate_table(tableau)

# Construction et affichage du graph sur le poids des groupes de la méthode géométrique
@app.callback(
    Output('graph_poids_des_groupes', 'figure'),
    [Input('stock_tableau_geo', 'children')])
def graph_poids(tableau_geo_json):    
    figure = geo.graph_poids_construct(tableau_geo_json)
    return figure


# Construction du df cohortes
@app.callback(
    Output('stock_cohortes', 'children'),
    [Input('button_valider', 'n_clicks')],
    [State('date_range','start_date'),
     State('date_range','end_date'),
     State('input_Nmois', 'value'),
     State('input_minimum_client','value')])
def maj_cohortes(n_clicks, start_date, end_date, Nmois, min_cli):
    # Correction du typage des inputs
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    Nmois = int(Nmois)
    min_cli = int(min_cli)
    
    df_cohortes = cohortes.df_cohortes_construct(start_date, end_date, Nmois, min_cli)
    
    return df_cohortes.to_json(date_format = 'iso', orient = 'split')

# Construction et affichage du graph des cohortes
@app.callback(
    Output('graph_cohortes', 'figure'),
    [Input('stock_cohortes','children')],
    [State('input_Nmois', 'value')])
def graph_cohortes(df_cohortes_json, Nmois):
    # Correction du typage des inputs
    Nmois = int(Nmois)
    
    figure = cohortes.graph_cohortes_construct(df_cohortes_json, Nmois)
    return figure

# Construction du tableau des cohortes
@app.callback(
    Output('stock_tableau_cohortes', 'children'),
    [Input('stock_cohortes','children')],
    [State('input_Nmois', 'value')])
def tableau_cohortes(df_cohortes_json, Nmois):
    # Correction du typage des inputs
    Nmois = int(Nmois)
    
    tableau = cohortes.tableau_cohortes_construct(df_cohortes_json, Nmois)
    return tableau.to_json(date_format = 'iso', orient = 'split')

# Affichage du tableau des cohortes
@app.callback(
        Output('tableau_cohortes', 'children'),
        [Input('stock_tableau_cohortes', 'children')])
def affichage_tableau_cohortes(tableau_json):
    tableau = pd.read_json(tableau_json, orient = 'split')
    # Reformatage des dates
#    tableau['cohorte'] = pd.to_datetime(tableau['cohorte']).dt.date

    return util.generate_table(tableau)

if __name__ == '__main__':
    app.run_server(debug=True)