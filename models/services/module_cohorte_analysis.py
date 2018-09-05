#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 30 14:03:22 2018

@author: arnaud
"""

import pandas as pd
import numpy as np
import datetime
import math
import utilitaires as util
import plotly.graph_objs as go

class CohorteAnalysis:
    
    def __init__(self, commandes):
        self.commandes = commandes
        
    def selection_cohortes(self, debut, fin):
        commandes_filtered = self.commandes.loc[(self.commandes['cohorte'] >= debut) & (self.commandes['cohorte'] <= fin),:].copy()
        
        # Ajout de la colonne semaine (qui contient en fait la date du lundi de la semaine en question)
        commandes_filtered['semaine'] = [d - datetime.timedelta(days=d.weekday()) for d in commandes_filtered['order_created_at']]
        
        return commandes_filtered
    
    
    
    # Fonction d'agrégation des cohortes
    def agregation_cohortes(self, group, mesure):
        if mesure == 'gross_revenue':
            c1 = group['gross_revenue'].sum()
        elif mesure == 'nb_com':
            c1 = len(group)
        elif mesure == 'nb_com_cli':
            c1 = len(group)/group['client_id'].nunique()
        elif mesure == 'panier_moyen':
            c1 = group['gross_revenue'].mean()
        elif mesure == 'nb_cli':
            c1 = group['client_id'].nunique()
        elif mesure == 'gross_revenue_cli':
            c1 = group['gross_revenue'].sum()/group['client_id'].nunique()

        return pd.Series([c1], index = [mesure])
    
    
    
    def tableau_cohortes_construct(self, commandes_filtered_json, mesure, affichage):
        commandes_filtered = pd.read_json(commandes_filtered_json, orient = 'split', convert_dates = ['order_created_at','first_order_date','latest_order_date','cohorte','semaine'])

        # Conversion de l'age en jour en numéro de mois (0-30 jours --> mois 1)
        commandes_filtered['age'] = [math.floor(x/30) + 1 for x in commandes_filtered['age']]
        
        # Aggrégation
        tableau = commandes_filtered.groupby(['cohorte','age']).apply(self.agregation_cohortes, mesure = mesure).unstack().reset_index() #fill_value = 0
        
        # Mise en forme
        colonnes = [str(x) for x in np.arange(1,len(tableau.columns))]
        colonnes.insert(0, 'cohorte')
        tableau.columns = colonnes
        
        # Transformation des valeurs en pourcentage si nécessaire
        Ncol = len(tableau.columns)
        # Pourcentage du premier mois
        if affichage == 'pct_total':
            for i in tableau.index:
                tot = tableau['1'][i]
                for j in np.arange(2, Ncol):
                    tableau.iloc[i,j] = tableau.iloc[i,j]/tot
        # Pourcentage du mois précédent
        elif affichage == 'pct_relatif':
            for i in tableau.index:
                for j in np.arange(2, Ncol)[::-1]: # [::-1] pour partir de la fin:
                    tableau.iloc[i,j] = tableau.iloc[i,j]/tableau.iloc[i,j-1]

        return tableau
    
    def tableau_cohortes_affich(self, tableau_cohortes_json, mesure, affichage):
        tableau = pd.read_json(tableau_cohortes_json, orient = 'split', convert_dates = ['cohorte'])
        
        # Conversion des dates en datetime
        tableau['cohorte'] = [datetime.datetime(x.year, x.month, x.day) for x in pd.to_datetime(tableau['cohorte'])]
        
        Ncol = len(tableau.columns)
        
        # Formatage des valeurs
        if affichage == 'valeur':
            for col in tableau.columns[1:]:
                if mesure in ['gross_revenue', 'panier_moyen', 'gross_revenue_cli']:
                    tableau[col] = util.format_montant(tableau[col])
                elif mesure in ['nb_com_cli']:
                    tableau[col] = [str(x) if not math.isnan(x) else math.nan for x in round(tableau[col], 1)]
                else:
                    tableau[col] = [str(int(x)) if not math.isnan(x) else math.nan for x in tableau[col]]
        # Pourcentage
        else:
            # La colonne du premier mois n'est pas en pourcentage donc est formatéé comme précédemment
            if mesure in ['gross_revenue', 'panier_moyen', 'gross_revenue_cli']:
                tableau['1'] = util.format_montant(tableau['1'])
            elif mesure in ['nb_com_cli']:
                tableau['1'] = [str(x) if not math.isnan(x) else math.nan for x in round(tableau['1'], 1)]
            else:
                tableau['1'] = [str(int(x)) if not math.isnan(x) else math.nan for x in tableau['1']]
            # Les colonnes suivantes sont des pourcentages
            for col in tableau.columns[2:]:
                tableau[col] = util.format_pct(tableau[col])
        
        # Signaler les mois incomplets :
        for i in tableau.index:
            date_fin_cohorte = util.lastday_of_month(tableau['cohorte'][i])
            mois_complets = (util.ajd - date_fin_cohorte).days//30
            for j in range(mois_complets + 1, Ncol):
                if isinstance(tableau.iloc[i,j], str) :
                    tableau.iloc[i,j] = '~ ' + tableau.iloc[i,j] + ' ~'
        
        # Formatage des cohortes
        tableau['cohorte'] = [x.strftime('%B %y').capitalize() for x in tableau['cohorte']]
        
        # Formatage des noms de colonnes
        tableau.columns = ['Cohorte'] + ['Mois ' + str(i) for i in range(1, Ncol)]
        
        return tableau
    
    # Label de la mesure
    correspondance = {'gross_revenue' : 'Gross revenue',
                      'gross_revenue_cli' : 'Gross revenue par client',
                      'nb_cli' : 'Nombre de clients',
                      'nb_com' : 'Nombre de commandes',
                      'nb_com_cli' : 'Nombre de commandes par client',
                      'panier_moyen' : 'Panier moyen'}
    
    def formatage(val, mesure, affichage):
        # Si on passe qu'une seule valeur on la met dans une liste pour la traiter comme quand on en passe plusieurs
        if not isinstance(val, (list, np.ndarray, pd.core.series.Series)):
            res = [val]
        
        # Formatage des valeurs
        if affichage == 'valeur':
            if mesure in ['gross_revenue', 'panier_moyen', 'gross_revenue_cli']:
                res = util.format_montant(res)
            elif mesure in ['nb_com_cli']:
                res = [str(x) if not math.isnan(x) else math.nan for x in round(res, 1)]
            else:
                res = [str(int(x)) if not math.isnan(x) else math.nan for x in res]
        # Formatage des pourcentages
        else:
            res = util.format_pct(res)
        
        # Opération inverse, si on a mis la valeur unique d'entrée dans une liste on l'en sort
        if not isinstance(val, (list, np.ndarray, pd.core.series.Series)):
            res = [res][0]
        return res
    
    def graph_cohortes(self, tableau_cohortes_json, mesure, affichage):
        tableau = pd.read_json(tableau_cohortes_json, orient = 'split', convert_dates = ['cohorte'])
        
        # Conversion des dates en datetime
        tableau['cohorte'] = [datetime.datetime(x.year, x.month, x.day) for x in pd.to_datetime(tableau['cohorte'])]
        
        # Pour le graphique on ne veut plus que le premier mois reste en valeur si les suivants sont en pourcentages
        if affichage in ['pct_total', 'pct_relatif']:
            tableau['1'] = 1.0
        
        label_mesure = self.correspondance[mesure]
        
        Ncol = len(tableau.columns)
        
        trace = []
        compteur = 0
        for i in tableau.index:
            compteur += 1
            y = list(tableau.iloc[i,1:])
            name = tableau.iloc[i,0].strftime('%B %y').capitalize()
            temp = go.Scatter(x = np.arange(1,Ncol),
                              y = y,
                              mode = 'lines+markers',
                              name = name,
                              hoverinfo = 'text',
                              text = [f"""<b>{name}</b><br>{x} """ for x in y],
                              # Par défaut on affiche seulement les 3 premières cohortes pour garder le graph lisible
                              visible = "legendonly" if compteur > 3 else True)
            trace += [temp]
            
        layout = {'title' : f"""Evolution de {label_mesure} par cohorte""",
                  'xaxis' : {'title' : 'Mois glissants',
                             'dtick' : 1},
                  'yaxis' : {'title' : label_mesure}}
            
        figure = go.Figure(data = trace, layout = layout)
        
        return figure