# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
#import plotly.plotly as py
import plotly.graph_objs as go
import utilitaires as util

class MethodeGeo:
    
    def __init__(self, commandes):
        self.commandes = commandes

    # Calcule les agrégats de toutes les commandes de chaque client
    def agregation_par_client(self, group, Nmois):
        c1 = group['order_created_at'].min()
        c2 = group['order_created_at'].max()
        c3 = group['order_number'].count()
        c4 = group['gross_revenue'].mean()
        c5 = group['gross_revenue'].sum()
        # Valeur sur les X premiers mois
        c6 = group.loc[group['age'] <= Nmois*30, 'gross_revenue'].sum()
        # Valeur sur les X/2 premiers et derniers mois
        age_max = group['age'].max()
        c7 = group.loc[(group['age'] <= Nmois/2*30) | (group['age'] >= age_max - Nmois/2*30), 'gross_revenue'].sum()
        # Valeur sur les X premiers mois
        c8 = group.loc[group['age'] >= age_max - Nmois*30, 'gross_revenue'].sum()
        
        colnames = ['premiere', 'derniere', 'orders_count', 'panier_moyen', 'value_totale', 'valueXpremiers', 'valueXmoitie', 'valueXderniers']
        return pd.Series([c1,c2,c3,c4,c5,c6,c7,c8], index = colnames)
    
    # Espérance géométrique du nombre de commandes
    #def prevision_nb_commandes():
        
    
    # Création du dataframe des clients
    def allcli_construct(self, Nmois, debut):
        # On ne garde que les clients qui ont passé au moins une commande après la date choisie
        df_commandes = self.commandes.loc[self.commandes['lastest_order_date'] >= debut,:].copy()

        # Agrégation
        allcli = df_commandes.groupby('client_id').apply(self.agregation_par_client, (Nmois)).reset_index()
        
        # Calcul des durées
        allcli['age'] = (util.ajd - allcli['premiere']).dt.days
        allcli['ddv'] = (allcli['derniere'] - allcli['premiere']).dt.days
        allcli['pas_vu_depuis'] = (util.ajd - allcli['derniere']).dt.days
        
        # Le client est-il encore actif ?
            # 3 catégories de clients : 1 seule commande passées ; entre 2 et 5 ; 6 ou plus
        seuil_com = [1, 5]
            # Nombres de jours nécessaires pour que les clients de chaque catégorie soient considérés comme parti
        seuil_jour = [30, 50, 70]
        allcli['actif'] = [ligne['pas_vu_depuis'] < seuil_jour[0] if ligne['orders_count'] <= seuil_com[0] else ligne['pas_vu_depuis'] < seuil_jour[1] if ligne['orders_count'] <= seuil_com[1] else ligne['pas_vu_depuis'] < seuil_jour[2] for i, ligne in allcli.iterrows()]
        
        return allcli
    
    # Fonction d'agregation des clients selon leur nombre de commandes
    def agregation_methode_geometrique(self, group, N, Nmois):
        c1 = len(group)/N
        c2 = group['value_totale'].mean()
        c3 = group['valueXpremiers'].mean()
        c4 = group['valueXmoitie'].mean()
        c5 = group['valueXderniers'].mean()
        colnames = ['Proportion', 'Value Totale', 'Value ' + str(Nmois) + ' premiers mois', 'Value ' + str(Nmois//2) + ' premiers '+ str(Nmois//2) + ' derniers mois', 'Value ' + str(Nmois) + ' derniers mois']
        return pd.Series([c1,c2,c3,c4,c5], index = colnames)
    
    # Input : les valeurs sur lesquels segmenter dans un seul string
    # Output : les listes bins et labels adaptées pour regrouper une variable en classe
    def creation_classes(self, string_segmentation):
        # Conversion du string fourni par l'utilisateur en liste d'entiers
        bins = [int(x) for x in string_segmentation.split(',')] + [np.inf]
        # Création des labels correspondants à la segmentation
        labels = list()
        for i in range(len(bins)-1): # On ne boucle pas sur le dernier élément de bins qui est +Infinite
            if bins[i+1] - bins[i] == 1:
                labels.append(str(bins[i]))
            elif bins[i+1] == np.inf:
                labels.append(str(bins[i]) + '+')
            else:
                labels.append(str(bins[i]) + '-' + str(bins[i+1]-1))
        
        out = [bins, labels]
        return out
    
    # Génère le tableau de la méthode 1
    def methode_geometrique_tableau(self, allcli_json, Nmois, segmentation):
        allcli = pd.read_json(allcli_json, orient = 'split')
        # Reformatage des dates
        allcli['premiere'] = pd.to_datetime(allcli['premiere'])
        allcli['derniere'] = pd.to_datetime(allcli['derniere'])
        
        # Regrouper les orders_count en classes
        seg = self.creation_classes(segmentation)
        bins = seg[0]
        labels = seg[1]
        allcli['classe'] = pd.cut(allcli['orders_count'], bins, labels = labels, right=False)
        
        # On ne garde que les clients qui ne sont plus actifs ou qui ont atteint la dernière classe de nombre de commandes
        allcli = allcli.loc[~(allcli['actif']) | (allcli['classe'] == labels[len(labels)-1]),:]
        
        # Pour estimer la valeur totale des clients qui sont encore là après le seuil max de commandes :
        # On suppose qu'une fois qu'un client a atteint le seuil maximal de nombre commande, sa probabilité de départ après chaque nouvelle commandes est constante
        # Le nombre de commandes qu'il va passer avant de partir suit donc une loi géométrique
        # Recherche du paramètre p de cette loi
        clients_dernier_seuil = allcli.loc[allcli['classe'] == labels[len(labels)-1], :].copy()
        nb_dernieres_commandes = np.size(clients_dernier_seuil['actif']) - np.count_nonzero(clients_dernier_seuil['actif'])
        # Nombre commandes qu'on passé tous ces clients après avoir atteint le dernier seuil
        nb_commandes = clients_dernier_seuil['orders_count'].sum() - len(clients_dernier_seuil)*(bins[len(bins)-2]-1)
        # Probabilté p qu'un client de cette dernière catégorie nous quitte après chaque commande
        p = nb_dernieres_commandes / nb_commandes
        # Estimation du nombre moyen de commandes par clients :
        nb_com_estime = int(round(1/p)) + bins[len(bins)-2]-1
        # Panier moyen des clients de cette catégorie
        panier_moyen = clients_dernier_seuil['panier_moyen'].mean()
        # Value estimée
        value_estimee = panier_moyen * nb_com_estime
        
        # Création du tableau
        tableau_geo = allcli.groupby('classe').apply(self.agregation_methode_geometrique, N = len(allcli), Nmois = Nmois).reset_index()
        
        # On place notre valeur estimée dans le tableau
        tableau_geo.loc[tableau_geo['classe'] == labels[len(labels)-1], 'Value Totale'] = value_estimee
        
        # Calcul d'une ligne moyenne
        ligne_moyenne = ['Moyenne', 1.0]
        for i in range(2,6):
            ligne_moyenne.append(sum(tableau_geo['Proportion'] * tableau_geo.iloc[:,i]))
            
        # Ajout de la ligne moyenne
        tableau_geo = tableau_geo.append(pd.DataFrame([ligne_moyenne], columns =list(tableau_geo.columns)), ignore_index=True)
        
        tableau_geo = tableau_geo.rename({'classe' : 'Nombre de commandes'}, axis = 'columns')
        
        return  tableau_geo
    
    # Génère le graph du poids des groupes de la méthode géométrique
    def graph_poids_construct(self, tableau_geo_json):
        tableau_geo = pd.read_json(tableau_geo_json, orient = 'split')
        # La valeur a découper
        tot = float(tableau_geo['Value Totale'][-1:])
        
        labels = tableau_geo['Nombre de commandes'][:-1]
        values = (tableau_geo['Proportion'][:-1] * tableau_geo['Value Totale'][:-1])/tot
        
        trace = go.Pie(labels=labels, values=values)
        
        figure = go.Figure(data =[trace])
        
        return figure