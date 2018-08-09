# -*- coding: utf-8 -*-

import fonctions_core_bd as fcore
import pandas as pd
import numpy as np
import utilitaires as util

class Commandes:
    commandes = pd.DataFrame()
    
    def __init__(self):
  
        # Liste des équipiers
        email_equipier = ['dumontet.thibaut@gmail.com', 'dumontet.julie@gmail.com', 'laura.h.jalbert@gmail.com', 'rehmvincent@gmail.com', 'a.mechkar@gmail.com', 'helena.luber@gmail.com', 'martin.plancquaert@gmail.com', 'badieresoscar@gmail.com', 'steffina.tagoreraj@gmail.com', 'perono.jeremy@gmail.com', 'roger.virgil@gmail.com', 'boutiermorgane@gmail.com', 'idabmat@gmail.com', 'nadinelhubert@gmail.com', 'faure.remi@yahoo.fr', 'maxime.cisilin@gmail.com', 'voto.arthur@gmail.com', 'pedro7569@gmail.com']
        
        req = """SELECT  o.order_number,
                      	o.client_id,
                        c.email,
                      	o.created_at AS order_created_at,
                      	SUM(CEILING(li.quantity * li.selling_price_cents/(1+tax_rate))) AS gross_sale,
                        o.total_shipping_cents/1.2 AS shipping_ht,
                        o.financial_status
          FROM orders o, line_items li, clients c
          WHERE o.id = li.order_id AND o.client_id = c.id
          GROUP BY  o.order_number,
                  	o.client_id,
                    c.email,
                  	o.created_at,
                    o.total_shipping_cents/1.2,
                    o.financial_status
          ORDER BY  order_created_at"""
        
        # Extraction des self.commandes de Core
        commandes1 = fcore.extract_core(req)
        
        # Calcul du gross_revenue
        commandes1['gross_revenue'] = commandes1.gross_sale/100 + commandes1.shipping_ht/100
        
        # On n'a plus besoin des colones gross_sale et shipping_ht
        commandes1 = commandes1.drop(['gross_sale','shipping_ht'], axis = 1)
        
        # Conversion de l'identiant client en string
        commandes1['client_id'] = commandes1['client_id'].apply(str)
        
        # Importation depuis un csv des self.commandes trop anciennes pour être dans Core
        commandes2 = pd.read_csv('data/old_commandes_shopify.csv', sep = ';', decimal = ',')
        commandes2 = commandes2.drop('first_order_date', axis=1)
        
        # Conversion des dates en datetime
        commandes2.order_created_at = pd.to_datetime(commandes2.order_created_at)
        
        # Ajout de la timezone aux colonnes de datetime
        commandes2.loc[:,'order_created_at'] = commandes2.loc[:,'order_created_at'].dt.tz_localize('Europe/Paris')
        
        # On ne garde pas les self.commandes déjà présentes dans l'extraction de Core
        commandes2 = commandes2.loc[~commandes2['order_number'].isin(commandes1.order_number)]
        
        # Un client a changé d'adresse email, on remplace l'ancienne par la nouvelle dans toutes les self.commandes
        commandes2.loc[commandes2['email'] == 'amigafeeling@free.fr','email'] = 'ludovic.chirol@orange.fr'
        commandes2.loc[commandes2['email'] == 'quentinrigo@gmail.com','email'] = 'blondinettedu71@gmail.com'
        
        # Association client_id // email
        email_id = commandes1.groupby(['client_id']).first().reset_index()[['client_id','email']].copy()
        
        # On ajoute ces identifiants au df commandes2
        commandes2 = pd.merge(commandes2, email_id, on='email', how='left')
        
        # Pour ceux qui n'en ont pas on va utilser l'email comme identifiant
        commandes2.loc[commandes2.client_id.isnull(),'client_id'] = commandes2.loc[commandes2.client_id.isnull(),'email']
        
        # Fusion des dataframes
        self.commandes = pd.concat([commandes2,commandes1], sort=True)
        
        # Dans Core les self.commandes 8556 à 8620 sont erronées alors on corrige les montants grâce à un csv
        commandes3 = pd.read_csv('data/corr_commandes_shopify.csv', sep = ';', decimal = ',')
        for i in range(8556,8620+1):
            self.commandes.loc[self.commandes['order_number']==i,'gross_revenue'] = commandes3.loc[commandes3['order_number']==i,'gross_revenue'].values
        
        # Suppression des données plus utiles
        del [commandes1, commandes2, commandes3, email_id, req]
        
        # On n'a pas besoin de l'heure, on va juste garder les dates
        self.commandes['order_created_at'] = self.commandes['order_created_at'].dt.date
        
        # On retire les self.commandes des équipiers
        self.commandes = self.commandes.loc[~self.commandes.email.isin(email_equipier)]
        
        # On retire les self.commandes refunded ou voided
        self.commandes = self.commandes.loc[~self.commandes.financial_status.isin(['refunded','voided'])]
        
        # On a plus besoin de financial_status
        self.commandes = self.commandes.drop('financial_status', axis=1)
        
        # On retire les self.commandes qui ne comportent que des cartes cadeaux
        self.commandes = self.commandes.loc[~self.commandes.order_number.isin([7084,10201,10461,10606,11693]),:]
        
        # Si un client a passé plus d'une commande en un jour on les fusionne
        dagg = {'order_number' : ['min','count'],
                'gross_revenue' : 'sum'}
        self.commandes = self.commandes.groupby(['client_id','email','order_created_at']).agg(dagg).reset_index()
        # Applatissement des noms des colonnes
        self.commandes.columns = ['_'.join(col).rstrip('_') for col in self.commandes.columns.values]
        # On garde le order_number a titre indicatif, on crée la colonne fusion qui indique si la commande a été fusionnée avec une autre
        self.commandes['fusion'] = self.commandes['order_number_count'] > 1
        self.commandes = self.commandes.drop('order_number_count', axis = 'columns')
        self.commandes = self.commandes.rename({'gross_revenue_sum' : 'gross_revenue',
                                      'order_number_min' : 'order_number'}, axis = 'columns')
        
        # Calcul des date de première et dernière self.commandes
        def first_last_order(group):
            premiere = group['order_created_at'].min()
            derniere = group['order_created_at'].max()
            group['first_order_date'] = premiere
            group['lastest_order_date'] = derniere
            return group
        # Ajout des colonnes date de première et dernière self.commandes
        self.commandes = self.commandes.groupby('client_id').apply(first_last_order)
        
        # Cohorte du client
        self.commandes['cohorte'] = self.commandes['first_order_date'].apply(lambda x: x.replace(day=1))
        
        # Rang de la commande
        self.commandes = self.commandes.sort_values(['client_id','order_created_at'])
        self.commandes['nieme'] = self.commandes.groupby('client_id').cumcount()+1
        
        # Nombre de self.commandes
        def orders_counting(group):
            res = group['nieme'].max()
            group['orders_count'] = res
            return group
        self.commandes = self.commandes.groupby('client_id').apply(orders_counting)
        
        # Délai avec la self.commandes suivante
        def calcul_delai(group):
            if len(group)>1:
                res = (group['order_created_at'].shift(-1) - group['order_created_at']).dt.days
                group['delai'] = res
            else:
                group['delai'] = np.NaN
            return group
        self.commandes = self.commandes.groupby('client_id').apply(calcul_delai)
        
        # Age en jour lors de la self.commandes
        self.commandes['age'] = (self.commandes['order_created_at'] - self.commandes['first_order_date']).dt.days
        
        # Pas vu depuis : pour les dernières self.commandes de chaque client : depuis combien de temps le client n'a pas commandé
        self.commandes.loc[np.isnan(self.commandes['delai']),'pas_vu_depuis'] = (util.ajd - self.commandes.loc[np.isnan(self.commandes['delai']), 'order_created_at']).dt.days
        
