#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 15:11:30 2018

@author: arnaud
"""
import pandas as pd
import numpy as np
#import utilitaires as util
import datetime
import plotly.graph_objs as go

class PUC:
    
    def __init__(self, commandes):
        self.commandes = commandes
    
    def graph_puc_construct(self, debut_com, fin_com, debut_cli, fin_cli, use_cohorts = False):
        
        Nsemaines = int(((fin_com - debut_com).days + 1)/7)
        
        # Filtrage des commandes : on ne garde que les commandes qui rentrent dans la plage de dates sélectionée
        commandes_filtered = self.commandes.loc[(self.commandes['order_created_at'] >= debut_com) & (self.commandes['order_created_at'] <= fin_com),:].copy()
        
        # Filtrage des clients : on ne garde que ceux qui sont arrivés dans la plage selectionnée
        commandes_filtered = commandes_filtered.loc[(commandes_filtered['first_order_date'] >= debut_cli) & (commandes_filtered['first_order_date'] <= fin_cli),:]
        
        # Nombre de clients
        Nclients = commandes_filtered['client_id'].nunique()
        
        # Ajout de la colonne semaine (qui contient en fait la date du lundi de la semaine en question)
        commandes_filtered['semaine'] = [d - datetime.timedelta(days=d.weekday()) for d in commandes_filtered['order_created_at']]
        
        # Dans combien de semaines différentes chaque client a-t-il passé commande ?
        df_cli = commandes_filtered.groupby(['client_id','cohorte']).agg({'semaine' : pd.Series.nunique}).reset_index()
        
        # Combien de clients ont passé des commandes sur 1 seule semaine ? Sur 2 ? Sur 3....
        if use_cohorts:
            df = df_cli.groupby(['semaine','cohorte']).agg({'client_id' : 'count'}).reset_index()
        else:
            df = df_cli.groupby('semaine').agg({'client_id' : 'count'}).reset_index()
        
        # Renommage des colonnes
        df = df.rename({'semaine' : 'nb_semaines',
                        'client_id' : 'nb_clients'}, axis = 'columns')
        
        if use_cohorts:
            trace = []
            x = np.arange(1,Nsemaines)
            for c in df['cohorte'].unique():
                # Nombre de clients de la cohorte actifs pendant la période choisie
                Ncli_cohorte = len(df_cli.loc[df_cli['cohorte'] == c,:])
                # Nombre de clients total de la cohorte
                Ncli_cohorte_tot = self.commandes.loc[self.commandes['cohorte'] == c, 'client_id'].nunique()
                y = np.asarray([0 if df.loc[(df['cohorte'] == c) & (df['nb_semaines'] == i),'nb_clients'].empty else df.loc[(df['cohorte'] == c) & (df['nb_semaines'] == i),'nb_clients'].reset_index(drop=True)[0] for i in x])
                temp = go.Scatter(x = x,
                                  y = y/Ncli_cohorte,   
                                  name = c.strftime('%B %y').capitalize(),
                                  mode = 'lines',
                                  hoverinfo = 'text',
                                  text = [f"""{c.strftime('%B %y').capitalize()} (Cohorte de {Ncli_cohorte_tot} clients à l'origine)<br>{Ncli_cohorte} clients actifs entre le {debut_com.strftime('%d/%m/%y')} et {fin_com.strftime('%d/%m/%y')} dont<br>{y[i]} ({round(100*y[i]/Ncli_cohorte,1)} %) actifs durant {x[i]} semaines différentes""" for i in range(len(x))])
                trace += [temp]
        else:
            trace = [go.Bar(x = df['nb_semaines'],
                           y = df['nb_clients']/Nclients,
                           hoverinfo = 'text',
                           text = [f"""{df['nb_clients'][i]} ({round(100*df['nb_clients'][i]/Nclients,1)} %) clients ont passé commande sur {df['nb_semaines'][i]} semaines différentes.""" for i in range(len(df))])]
        
        layout = {'title' : 'Nombre de semaines d\'activité des clients',
                   'xaxis' : {'dtick' : 1,
                             'title' : 'Nombre de semaines avec commande'},
                  'yaxis' : {'dtick' : 0.1,
                             'title' : 'Pourcentage de client'}}
        
        figure = go.Figure(data = trace, layout = layout)
        
        return figure