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
    
    
    
    def tableau_cohortes_construct(self, commandes_filtered_json, mesure):
        commandes_filtered = pd.read_json(commandes_filtered_json, orient = 'split', convert_dates = ['order_created_at','first_order_date','latest_order_date','cohorte','semaine'])

        # Conversion de l'age en jour en numéro de mois (0-30 jours --> mois 1)
        commandes_filtered['age'] = [math.floor(x/30) + 1 for x in commandes_filtered['age']]
        
        # Aggrégation
        tableau = commandes_filtered.groupby(['cohorte','age']).apply(self.agregation_cohortes, mesure = mesure).unstack().reset_index() #fill_value = 0
        
        # Mise en forme
        colonnes = [str(x) for x in np.arange(1,len(tableau.columns))]
        colonnes.insert(0, 'cohorte')
        tableau.columns = colonnes

        return tableau
    
    def tableau_cohortes_affich(self, tableau_cohortes_json, mesure):
        tableau = pd.read_json(tableau_cohortes_json, orient = 'split', convert_dates = ['cohorte'])
        
        # Conversion des dates en datetime
        tableau['cohorte'] = [datetime.datetime(x.year, x.month, x.day) for x in pd.to_datetime(tableau['cohorte'])]
        
        Ncol = len(tableau.columns)
        
        # Formatage des valeurs
        for col in tableau.columns[1:]:
            if mesure in ['gross_revenue', 'panier_moyen', 'gross_revenue_cli']:
                tableau[col] = util.format_montant(tableau[col])
            elif mesure in ['nb_com_cli']:
                tableau[col] = [str(x) if not math.isnan(x) else math.nan for x in round(tableau[col], 1)]
            else:
                tableau[col] = [str(int(x)) if not math.isnan(x) else math.nan for x in tableau[col]]
        
        
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