#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 11:47:42 2018

@author: arnaud
"""

from models.services import methode_geo
from models.services import methode_cohortes
from models.services import seuils_absences
import pandas as pd
import datetime
from dash.dependencies import Input, Output, State
import dash_html_components as html
import utilitaires as util

from app import app, commandes

geo = methode_geo.MethodeGeo(commandes)
cohortes = methode_cohortes.Cohortes(commandes)
seuils = seuils_absences.PredictionDepart(commandes)

###############################################################################
################################## CONTROLLER #################################
###############################################################################

########################### METHODE GEOMETRIQUE ###############################

# Construction du df allcli
@app.callback(
    Output('stock_allcli','children'),
    [Input('button_valider', 'n_clicks')],
    [State('input_Nmois', 'value'),
     State('date_range','start_date'),
     State('date_range','end_date'),
     State('segmentation_nb_com_actif', 'value'),
     State('seuils_actif_inactif', 'value')])
def maj_allcli(n_clicks, Nmois, start_date, end_date, segmentation, seuils):
    # Correction du typage des inputs
    Nmois = int(Nmois)
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Création du dataframe des clients
    allcli = geo.allcli_construct(Nmois, start_date, segmentation, seuils)
    
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
#    tableau['Proportion'] = [util.format_pct(x) + ' %' for x in tableau['Proportion']]
    tableau['Proportion'] = util.format_pct(tableau['Proportion'])
    
    return util.generate_table(tableau)

# Construction et affichage du graph sur le poids des groupes de la méthode géométrique
@app.callback(
    Output('graph_poids_des_groupes', 'figure'),
    [Input('stock_tableau_geo', 'children'),
     Input('dropdown_column_plotted', 'value')])
def graph_poids(tableau_geo_json, colonne_choisie):    
    figure = geo.graph_poids_construct(tableau_geo_json, colonne_choisie)
    return figure

# MAJ des valeurs du dropdown
@app.callback(
    Output('dropdown_column_plotted','options'),
    [Input('stock_tableau_geo', 'children')])
def maj_dropdown_plotted_column(tableau_geo_json):
    options = geo.dropdown_options(tableau_geo_json)
    return options

# Paragraphe des détails de la méthode 1
@app.callback(
    Output('detail_date_methode_1', 'children'),
    [Input('date_range','start_date')])
def maj_P_details_methode1(start_date):
    # Correction du typage des inputs
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    return html.P(f'''Tous les clients ayant passé au moins une commandes après le {start_date.strftime('%d/%m/%y')} ont été inclus dans cette méthode.''')

# Construction et affichage du tableau détails géo
#@app.callback(
#    Output('tableau_segmentation','children'),
#    [Input('stock_allcli','children')],
#    [State('segmentation_nb_com','value')])
#def tableau_details_geo(allcli_json):
##    tableau_details = geo.tableau_details_construct(allcli_json)
#    tableau_details = pd.read_json(allcli_json, orient = 'split')
#    print(tableau_details)
#    return util.generate_table(tableau_details)

############################# METHODE COHORTE #################################

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

# Paragraphe des détails de la méthode 2
@app.callback(
    Output('detail_date_methode_2', 'children'),
    [Input('date_range','start_date'),
     Input('date_range','end_date')])
def maj_P_details_methode2(start_date, end_date):
    # Correction du typage des inputs
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    return html.P(f'''Tous les clients ayant passé leur première commande entre le {start_date.strftime('%d/%m/%y')} et le {end_date.strftime('%d/%m/%y')} ont été inclus dans cette méthode.''')

########################### CHOIX SEUIL DEPART ################################
    
@app.callback(
    Output('stock_df_delais', 'children'),
    [Input('button_seuil_depart', 'n_clicks')],
    [State('date_seuil', 'date')])
def stockage_df_delais(n_clicks, date_seuil):
    date_seuil = datetime.datetime.strptime(date_seuil, '%Y-%m-%d').date()
    df_delais = seuils.df_delais_construct(date_seuil)
    return df_delais.to_json(orient = 'split')

#@app.callback(
#    Output('graph_ecdf_global', 'figure'),
#    [Input('stock_df_delais','children')])
#def graph_ecdf_global(df_delais_json):
#    figure = seuils.graph_ecdf(df_delais_json)
#    return figure

@app.callback(
    Output('graph_ecdf_classe', 'figure'),
    [Input('stock_df_delais','children'),
     Input('seuils_actif_inactif', 'value'),
     Input('segmentation_nb_com_actif', 'value')])
def graph_ecdf_classe(df_delais_json, seuils_actif, segmentation):
    figure = seuils.graph_ecdf(df_delais_json, seuils_actif, segmentation)
    return figure

#@app.callback(
#    Output('graph_chances_retour_global', 'figure'),
#    [Input('stock_df_delais','children')])
#def graph_chances_retour_global(df_delais_json):
#    figure = seuils.graph_chances_de_revoir(df_delais_json, 0.2)
#    return figure

@app.callback(
    Output('graph_chances_retour_classe', 'figure'),
    [Input('stock_df_delais','children'),
     Input('segmentation_nb_com_actif', 'value'),
     Input('slider_pct', 'value') ])
def graph__chances_retour_classe(df_delais_json, segmentation, slider):
    figure = seuils.graph_chances_de_revoir(df_delais_json, slider/100, segmentation)
    return figure