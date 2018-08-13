# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from statsmodels.distributions.empirical_distribution import ECDF
import plotly.graph_objs as go
import utilitaires as util

class PredictionDepart:
    
    def __init__(self, commandes):
        self.commandes = commandes
        
    def df_delais_construct(self, date_seuil):
        """ Création d'un df_delais : une ligne est un délai en jour, revenu = True si le client a repassé commande après ce délai, False sinon"""
        df_commandes = self.commandes.loc[self.commandes['first_order_date'] >= date_seuil,:].copy()
        
        df_delais = df_commandes.loc[~np.isnan(df_commandes['delai']), ['delai', 'nieme']].copy()
        df_delais['revenu'] = True
        
        df_temp = df_commandes.loc[np.isnan(df_commandes['delai']), ['pas_vu_depuis', 'nieme']].copy()
        df_temp = df_temp.rename({'pas_vu_depuis' : 'delai'}, axis = 'columns')
        df_temp['revenu'] = False
        
        df_delais = df_delais.append(df_temp)
        df_delais['delai'] = df_delais['delai'].astype(int)
        return df_delais
    
    
    def chances_de_recommander(self, df_delais, x):
        """ Quand on observe qu'un client n'a pas commandé depuis X jours, combien a-t-on de chances de le revoir commander ?"""
        # Nombre de retours après un délai > x
        nb_ret = sum((df_delais['delai'] > x) & (df_delais['revenu']))
        nb_tot = sum(df_delais['delai'] > x)
        return nb_ret/nb_tot
    
    def graph_ecdf(self, df_delais_json, segmentation=None):
        df_delais = pd.read_json(df_delais_json, orient = 'split')
        df_delais = df_delais.loc[df_delais['revenu'],:]
        
        if segmentation is None:  
            ecdf = ECDF(df_delais['delai'])
            trace = go.Scatter(x = ecdf.x,
                               y = ecdf.y,
                               mode = 'lines')
            trace = [trace]

        else:
            seg = util.creation_classes(segmentation)
            bins = seg[0]
            labels = seg[1]
            df_delais['classe'] = pd.cut(df_delais['nieme'], bins = bins, labels = labels, right=False)
            # Séparation des classes
            split_class = df_delais.groupby('classe')
            split_class = [split_class.get_group(x).reset_index(drop = True) for x in split_class.groups]
            
            trace = []
            for classe in split_class:
                ecdf = ECDF(classe['delai'])
                trace_i = go.Scatter(x = ecdf.x,
                                     y = ecdf.y,
                                     name = classe['classe'][0])
                trace += [trace_i]
        
        layout = {'title' : 'Répartition des délais entre 2 commandes'}
        figure = go.Figure(data =trace, layout = layout)
        return figure

        
    
    def graph_chances_de_revoir(self, df_delais_json, hauteur_barre, segmentation=None):
        df_delais = pd.read_json(df_delais_json, orient = 'split')
        
        x = np.arange(15,101)
        if segmentation is None:
            y = [self.chances_de_recommander(df_delais, i) for i in x]
            trace = go.Scatter(x = x,
                               y = y)
            trace = [trace]
        else:
            seg = util.creation_classes(segmentation)
            bins = seg[0]
            labels = seg[1]
            df_delais['classe'] = pd.cut(df_delais['nieme'], bins = bins, labels = labels, right=False)
            # Séparation des classes
            split_class = df_delais.groupby('classe')
            split_class = [split_class.get_group(x).reset_index(drop = True) for x in split_class.groups]
            trace = []
            for classe in split_class:
                y = [self.chances_de_recommander(classe, i) for i in x]
                trace_i = go.Scatter(x = x,
                                     y = y,
                                     name = classe['classe'][0],
                                     text = [f'''{classe['classe'][0]}<br>Jours d'absence = {x[i]}<br>Chances de retour = {round(y[i]*100,1)} %''' for i in range(len(x))],
                                     hoverinfo = 'text')
                trace += [trace_i]
        
        layout = {'title' : 'Chances qu\'un client repasse une commande après x jours sans commander',
                  'yaxis' : {'range' : [0,1]},
                  'shapes' : [{'type' : 'line',
                                'x0': x[0],
                                'y0': hauteur_barre,
                                'x1': x[len(x)-1],
                                'y1': hauteur_barre,
                                'line': {
                                    'color': 'rgb(50, 171, 96)',
                                    'width': 2,
                                    'dash': 'dash',
                                }}]}
        figure = go.Figure(data =trace, layout = layout)
        return figure
            