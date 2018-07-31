# -*- coding: utf-8 -*-

#import gunicorn
import fonctions_core_bd as fcore
import fonctions_dates as fdate
import pandas as pd
import numpy as np
#import sqlalchemy
import datetime
import os
import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
#import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

###############################################################################
##################################### DATA ####################################
###############################################################################
    
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

# Extraction des commandes de Core
commandes1 = fcore.extract_core(req)

# Calcul du gross_revenue
commandes1['gross_revenue'] = commandes1.gross_sale/100 + commandes1.shipping_ht/100

# On n'a plus besoin des colones gross_sale et shipping_ht
commandes1 = commandes1.drop(['gross_sale','shipping_ht'], axis = 1)

# Conversion de l'identiant client en string
commandes1['client_id'] = commandes1['client_id'].apply(str)

# Importation depuis un csv des commandes trop anciennes pour être dans Core
commandes2 = pd.read_csv('old_commandes_shopify.csv', sep = ';', decimal = ',')
commandes2 = commandes2.drop('first_order_date', axis=1)

# Conversion des dates en datetime
commandes2.order_created_at = pd.to_datetime(commandes2.order_created_at)

# Ajout de la timezone aux colonnes de datetime
commandes2.loc[:,'order_created_at'] = commandes2.loc[:,'order_created_at'].dt.tz_localize('Europe/Paris')

# On ne garde pas les commandes déjà présentes dans l'extraction de Core
commandes2 = commandes2.loc[~commandes2['order_number'].isin(commandes1.order_number)]

# Un client a changé d'adresse email, on remplace l'ancienne par la nouvelle dans toutes les commandes
commandes2.loc[commandes2['email'] == 'amigafeeling@free.fr','email'] = 'ludovic.chirol@orange.fr'
commandes2.loc[commandes2['email'] == 'quentinrigo@gmail.com','email'] = 'blondinettedu71@gmail.com'

# Association client_id // email
email_id = commandes1.groupby(['client_id']).first().reset_index()[['client_id','email']].copy()

# On ajoute ces identifiants au df commandes2
commandes2 = pd.merge(commandes2, email_id, on='email', how='left')

# Pour ceux qui n'en ont pas on va utilser l'email comme identifiant
commandes2.loc[commandes2.client_id.isnull(),'client_id'] = commandes2.loc[commandes2.client_id.isnull(),'email']

# Fusion des dataframes
commandes = pd.concat([commandes2,commandes1], sort=True)

# Dans Core les commandes 8556 à 8620 sont erronées alors on corrige les montants grâce à un csv
commandes3 = pd.read_csv('corr_commandes_shopify.csv', sep = ';', decimal = ',')
for i in range(8556,8620+1):
    commandes.loc[commandes['order_number']==i,'gross_revenue'] = commandes3.loc[commandes3['order_number']==i,'gross_revenue'].values

# Suppression des données plus utiles
del [commandes1, commandes2, commandes3, email_id, req]

# On n'a pas besoin de l'heure, on va juste garder les dates
commandes['order_created_at'] = commandes.loc[:,'order_created_at'].dt.date

# On retire les commandes des équipiers
commandes = commandes.loc[~commandes.email.isin(email_equipier)]

# On retire les commandes refunded ou voided
commandes = commandes.loc[~commandes.financial_status.isin(['refunded','voided'])]

# On a plus besoin de financial_status
commandes = commandes.drop('financial_status', axis=1)

# On retire les commandes qui ne comportent que des cartes cadeaux
commandes = commandes.loc[~commandes.order_number.isin([7084,10201,10461,10606,11693]),:]

# Si un client a passé plus d'une commande en un jour on les fusionne
dagg = {'order_number' : ['min','count'],
        'gross_revenue' : 'sum'}
commandes = commandes.groupby(['client_id','email','order_created_at']).agg(dagg).reset_index()
# Applatissement des noms des colonnes
commandes.columns = ['_'.join(col).rstrip('_') for col in commandes.columns.values]
# On garde le order_number a titre indicatif, on crée la colonne fusion qui indique si la commande a été fusionnée avec une autre
commandes['fusion'] = commandes['order_number_count'] > 1
commandes = commandes.drop('order_number_count', axis = 'columns')
commandes = commandes.rename({'gross_revenue_sum' : 'gross_revenue',
                              'order_number_min' : 'order_number'}, axis = 'columns')

# Calcul de la date de première commande
def first_order(group):
    res = group['order_created_at'].min()
    group['first_order_date'] = res
    return group
commandes = commandes.groupby('client_id').apply(first_order)

# Rang de la commande
commandes = commandes.sort_values(['client_id','order_created_at'])
commandes['nieme'] = commandes.groupby('client_id').cumcount()+1

# Nombre de commandes
def orders_counting(group):
    res = group['nieme'].max()
    group['orders_count'] = res
    return group
commandes = commandes.groupby('client_id').apply(orders_counting)

# Date d'aujourd'hui
ajd = datetime.datetime.today().date()

# Nombre de mois étudiés (doit être pair)
X = 18

# Création du dataframe des clients
def allcli_construct():
    # Dictionnaire d'aggrégation
    dagg = {'order_created_at' : ['min', 'max', 'count'],
            'gross_revenue' : ['mean', 'sum']}
    
    # Aggrégation : une ligne par client
    allcli = commandes.groupby('client_id').agg(dagg).reset_index()
    # Applatissement des noms de colonnes
    allcli.columns = ['_'.join(col).rstrip('_') for col in allcli.columns.values]
    # On renomme les colonnes
    allcli = allcli.rename({'order_created_at_min' : 'premiere',
                           'order_created_at_max' : 'derniere',
                           'order_created_at_count' : 'orders_count',
                           'gross_revenue_mean' : 'panier_moyen',
                           'gross_revenue_sum' : 'value'}, axis = 'columns')
    
    # Calcul des durées
    allcli['age'] = (ajd - allcli['premiere']).dt.days
    allcli['ddv'] = (allcli['derniere'] - allcli['premiere']).dt.days
    allcli['pas_vu_depuis'] = (ajd - allcli['derniere']).dt.days
    
    # Le client est-il encore actif ?
    seuil_jour1, seuil_jour2, seuil_jour3 = [30, 50, 70]
    seuil_com1, seuil_com2 = [1, 5]
    allcli['actif'] = [ligne['pas_vu_depuis'] < seuil_jour1 if ligne['orders_count'] <= seuil_com1 else ligne['pas_vu_depuis'] < seuil_jour2 if ligne['orders_count'] <= seuil_com2 else ligne['pas_vu_depuis'] < seuil_jour3 for i, ligne in allcli.iterrows()]
    
    return allcli

###############################################################################
################################# LAYOUT/VIEW #################################
###############################################################################

# Déclaration de l'application    
app = dash.Dash('auth')
auth = dash_auth.BasicAuth(app,
                           [[os.environ['appuser'], os.environ['apppass']]])
server = app.server

# Layout
app.layout = html.Div([
        
        # Header
        html.Div([
            # Colonne Barre Latérale
            html.Div([
                html.H4('Onglet 1'),
                html.H4('Onglet 2')
            ], className = 'two columns'),
            # Colonne Formulaire
            html.Div([
                html.H1('Dashboard CLV'),
                # Ligne des labels
                html.Div([
                    html.Div([
                        html.Label('Sur combien de mois calculer la CLV :')
                    ], className = 'six columns'),
                    html.Div([
                        html.Label('Limiter l\'étude sur les clients qui ont passé leur première commande entre :')
                    ], className = 'six columns'),
                ], className = 'row'),
                # Ligne des inputs
                html.Div([
                        html.Div([
                            dcc.Input(id = 'input_X', type = 'number', value = '18')
                        ], className = 'six columns'),
                        html.Div([
                            dcc.DatePickerRange(
                                id='date_range',
                                min_date_allowed = datetime.date(2015, 1, 1),
                                max_date_allowed = ajd if ajd == fdate.lastday_of_month(ajd) else ajd - datetime.timedelta(ajd.day), # Dernier jour du dernier mois fini
                                # Par défaut : du 1er mars 2017 à il y a 4 mois
                                start_date = datetime.date(2017, 3, 1),
                                end_date = datetime.date(fdate.AddMonths(ajd,-4).year, fdate.AddMonths(ajd,-4).month, fdate.lastday_of_month(fdate.AddMonths(ajd,-4)).day)
                            )
                        ], className = 'six columns'),
                ], className = 'row'),
                # Ligne du bouton
                html.Div([
                    html.Button(id = 'button_valider', n_clicks = 0, children = 'Valider')
                ], className = 'row')
            ], className = ' ten columns')
        ], className = 'row'),
        
        # Body
        html.Div([
            html.Div([
                # Méthode 1
                html.Div([
                    html.H2('Méthode n°1')
                ], className = 'six columns'),
                # Méthode 2
                html.Div([
                    html.H2('Méthode n°2'),
                    html.Div(id = 'out')
                ], className = 'six columns'),
            ], className = 'row')
        ])
])

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})    

###############################################################################
################################## CONTROLLER #################################
###############################################################################

@app.callback(
        Output('out','children'),
        [Input('button_valider', 'n_clicks')],
        [State('input_X', 'value')])
def outoutoutotut(n_clicks,value):
    if n_clicks > 0:
        res = [html.H1(children = f'''Vous avez choisi {value} mois, cool.'''),
               html.H2(children = 'Moyenne de allcli = ' + str(allcli_construct()))]
        return res
    else:
        return None

if __name__ == '__main__':
    app.run_server(debug=True)