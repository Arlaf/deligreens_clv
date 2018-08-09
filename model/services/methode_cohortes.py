# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import utilitaires as util
import plotly.graph_objs as go
import math
from plotly import tools

class Cohortes:
    df_cohortes = pd.DataFrame()
    
    def __init__(self, commandes):
        self.commandes = commandes

    # Fonction d'agregation des clients en cohortes
    def agregation_clients_cohortes(self, group):
        c1 = int(group['client_id'].nunique())
        c2 = int(group['order_number'].count())
        c3 = group['gross_revenue'].sum()
        colnames = ['nb_cli','nb_com','gross_revenue']
        return pd.Series([c1,c2,c3], index = colnames)
    
    # input : un dataframe contenant les dépenses par mois d'une seule cohorte et le nombre de mois minimum jusqu'auquel faire les prévisions
    # output : même dataframe avec la colonne des prévisions en plus
    def modelisation_depenses_cohorte(self, cohorte, Nmois):
        # Calcul du modèle sur les vraies données
        coef = np.polyfit(cohorte['age_mois'], np.log(cohorte['gross_revenue']), 1)
        
        # Si besoin on rajoute des lignes pour atteindre le nombre minimum de mois
        if Nmois > cohorte['age_mois'].max():
            new_rows_data = {'cohorte' : cohorte['cohorte'][0],
                             'age_mois': np.arange(cohorte['age_mois'].max()+1, Nmois+1)}
            new_rows = pd.DataFrame(new_rows_data, columns=['cohorte','age_mois'])
            cohorte = cohorte.append(new_rows, sort = False).reset_index(drop= True)
        
        cohorte['estimation'] = np.exp(coef[0]*cohorte['age_mois']+coef[1])
        return cohorte
    
    # Regroupe les clients par cohorte
    def df_cohortes_construct(self, debut, fin, Nmois, min_cli):
        # Filtrage des commandes selon les dates de première commande des clients
        df = self.commandes.loc[(self.commandes['first_order_date'] >= debut) & (self.commandes['first_order_date'] <= fin),:].copy()
        # Age aujourd'hui en mois arrondi à l'inférieur (on ne compte que les mois complets)
        df['age_actuel_mois'] = (util.ajd - df['first_order_date']).dt.days//30
        # on enlève les commandes du mois en cours pour chaque client (si un client est là depuis 1,2 mois on se limite à 1 mois de données)
        df = df.loc[df['age']/30 <= df['age_actuel_mois'],:]
        # Age du client en mois au moment de sa commande
        df['age_mois'] = (df['order_created_at'] - df['first_order_date']).dt.days//30
        
        # Agrégation
        df_cohortes = df.groupby(['cohorte', 'age_mois']).apply(self.agregation_clients_cohortes).reset_index()
        
        # On retire les cohortes qui ne contiennent pas assez de clients
        df_cohortes = df_cohortes.groupby('cohorte').filter(lambda group: group['nb_cli'].max() >= min_cli)
        
        # Séparation des cohortes
        split_cohortes = df_cohortes.groupby('cohorte')
        split_cohortes = [split_cohortes.get_group(x).reset_index(drop = True) for x in split_cohortes.groups]
        
        # On réinitialise le df_cohortes
        df_cohortes = pd.DataFrame()
        for cohorte in split_cohortes:
            df_cohortes = df_cohortes.append(self.modelisation_depenses_cohorte(cohorte, Nmois), sort = False).reset_index(drop = True)
        
        return df_cohortes 
    
    # Création du graph des cohortes
    def graph_cohortes_construct(self, df_cohortes_json, Nmois):
        df_cohortes = pd.read_json(df_cohortes_json, orient = 'split')
        # Reformatage des dates
        df_cohortes['cohorte'] = pd.to_datetime(df_cohortes['cohorte']).dt.date
        
        # Séparation des cohortes
        split_cohortes = df_cohortes.groupby('cohorte')
        split_cohortes = [split_cohortes.get_group(x).reset_index(drop = True) for x in split_cohortes.groups]
        
        # Noms des cohortes
        titres = [x.strftime('%B %y').capitalize() + f''' ({int(df_cohortes.loc[df_cohortes['cohorte'] == x, 'nb_cli'].max())} clients)''' for x in df_cohortes['cohorte'].unique()]
        
        # Création du graphique
        ncols = 3 # Nombre de colonnes du layout
        figure = tools.make_subplots(rows = int(math.ceil(len(titres)/ncols)),
                                     cols = ncols,
                                     subplot_titles = titres,
                                     shared_xaxes = True)
        # Indices pour la position des sous-graph
        i = 1
        j = 1
        # Pour chaque cohorte
        for c in split_cohortes:
            # Courbe théorique
            trace_theo = go.Scatter(x = list(c['age_mois']),
                                   y = list(c['estimation']),
                                   mode = 'lines',
                                   marker = dict(color = 'rgb(255, 0, 0)'))
            figure.append_trace(trace_theo, i, j)
            
            # Courbe empirique
            trace_emp = go.Scatter(x = list(c['age_mois']),
                               y = list(c['gross_revenue']),
                               mode = 'markers',
                               marker = dict(color = 'rgb(0, 0, 0)'))
            figure.append_trace(trace_emp, i, j)
            
            # Ligne verticale
            trace_ligne = go.Scatter(x = [Nmois, Nmois],
                                     y = [0, c['gross_revenue'].max()],
                                     mode = 'lines',
                                     line = dict(dash = 'dot',
                                                 color = 'rgb(0,0,0)'),
                                     hoverinfo = 'none')
            figure.append_trace(trace_ligne, i, j)
            
            if j == ncols:
                j = 1
                i = i+1
            else:
                j = j+1
        
        figure['layout'].update(title = 'Evolution des dépenses des cohortes',
                                showlegend = False,
                                height = math.ceil(len(split_cohortes)/ncols)*180 # Hauteur de 180px par ligne
                                )
        
        #### CETTE METHODE N'AFFICHE UNE LIGNE VERTICALE QUE SUR LE PREMIERE GRAPH
        # Ajout d'une ligne verticale
    #    figure['layout']['shapes'] = [{'type' : 'line',
    #                                       'x0' : Nmois,
    #                                       'x1' : Nmois,
    #                                       'y0' : 0,
    #                                       'y1' : 1000000,
    #                                       'yref' : 'y1',
    #                                       'line' : {'dash' : 'dot',
    #                                                 'color' : 'rgb(0,0,0)'}}]
        return figure
    
    # Fonction d'agrégation des cohortes
    def agregation_cohortes(self, group, Nmois):
        c1 = group['nb_cli'].max()
        c2 = group.loc[group['age_mois']<=Nmois, 'estimation'].sum()
        c3 = c2/c1
        colnames = ['Nombre de clients', 'Valeur de la cohorte à ' + str(Nmois) + ' mois', ' Valeur moyenne d\'un client']
        return pd.Series([c1,c2,c3], index = colnames)
    
    # Création du tableau des cohortes
    def tableau_cohortes_construct(self, df_cohortes_json, Nmois):
        df_cohortes = pd.read_json(df_cohortes_json, orient = 'split')
        # Reformatage des dates
        df_cohortes['cohorte'] = pd.to_datetime(df_cohortes['cohorte']).dt.date
        
        tableau = df_cohortes.groupby('cohorte').apply(self.agregation_cohortes, Nmois = Nmois).reset_index()
        
        # Formatage du mois de la cohorte pour l'affichage
        tableau['cohorte'] = [x.strftime('%B %y').capitalize() for x in tableau['cohorte']]
        
        # Calcul d'une ligne moyenne
        N = sum(tableau['Nombre de clients'])
        ligne_moyenne = ['Moyenne', int(N), sum(tableau['Nombre de clients']*tableau.iloc[:,2])/N, sum(tableau['Nombre de clients']*tableau.iloc[:,3])/N]
        
        tableau = tableau.append(pd.DataFrame([ligne_moyenne], columns = list(tableau.columns)), ignore_index =True)
        
        tableau['Nombre de clients'] = tableau['Nombre de clients'].astype(int)
        
        # Formatage des nombres pour l'affichage
        for col in tableau.select_dtypes(include = ['float64']):
            tableau[col] = util.format_montant(tableau[col])
            
        tableau = tableau.rename({'cohorte' : 'Cohorte'}, axis = 'columns')
        
        return tableau