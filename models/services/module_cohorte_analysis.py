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
            c1 = util.format_montant([group['gross_revenue'].sum()])
        elif mesure == 'nb_com':
            c1 = [str(len(group))]
        elif mesure == 'nb_com_cli':
            c1 = [str(round(len(group)/group['client_id'].nunique(),1))]
        elif mesure == 'panier_moyen':
            c1 = util.format_montant([group['gross_revenue'].mean()])
        elif mesure == 'nb_cli':
            c1 = [str(group['client_id'].nunique())]
        elif mesure == 'gross_revenue_cli':
            c1 = util.format_montant([group['gross_revenue'].sum()/group['client_id'].nunique()])

        # Signaler les mois incomplets :
        mois_complets = (util.ajd - util.lastday_of_month(group['cohorte'][group.index[0]])).days//30
        if group['age'][group.index[0]] == mois_complets + 2:
            c1[0] = '0.0'
        elif group['age'][group.index[0]] == mois_complets + 1:
            c1[0] = '~~' + c1[0] + '~~'

        return pd.Series([c1], index = [mesure])
    
    
    
    def tableau_cohortes_construct(self, commandes_filtered_json, mesure):
        commandes_filtered = pd.read_json(commandes_filtered_json, orient = 'split', convert_dates = ['order_created_at','first_order_date','latest_order_date','cohorte','semaine'])

        # Conversion de l'age en jour en numéro de mois (0-30 jours --> mois 1)
        commandes_filtered['age'] = [math.floor(x/30) + 1 for x in commandes_filtered['age']]
# =============================================================================        
#         df = commandes_filtered.groupby(['cohorte','age']).apply(self.agregation_cohortes).unstack(fill_value = 0)
#         
#         if mesure == 'gross_revenue':
#             df_revenue = df.iloc[:,0:(len(df.columns)//2)]
#         else:
#             df_cli = df.iloc[:,(len(df.columns)//2):(len(df.columns))]
# =============================================================================
        
        tableau = commandes_filtered.groupby(['cohorte','age']).apply(self.agregation_cohortes, mesure = mesure).unstack(fill_value = 0).reset_index()
        
        # Mise en forme
        colonnes = ['Mois ' + str(x) for x in np.arange(1,len(tableau.columns))]
        colonnes.insert(0, 'Cohorte')
        tableau.columns = colonnes
        tableau['Cohorte'] = [x.strftime('%B %y').capitalize() for x in tableau['Cohorte']]
        
        return tableau