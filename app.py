# -*- coding: utf-8 -*-

#import gunicorn
import fonctions_core_bd as fcore
import fonctions_dates as fdate
import pandas as pd
import numpy as np
import datetime
import math
import os
import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from plotly import tools
import plotly.plotly as py
import plotly.graph_objs as go

###############################################################################
###################### VARIABLES GLOBALES ET IMMUABLES ########################
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
commandes['order_created_at'] = commandes['order_created_at'].dt.date

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

    
# Cohorte du client
commandes['cohorte'] = commandes['first_order_date'].apply(lambda x: x.replace(day=1))

# Rang de la commande
commandes = commandes.sort_values(['client_id','order_created_at'])
commandes['nieme'] = commandes.groupby('client_id').cumcount()+1

# Nombre de commandes
def orders_counting(group):
    res = group['nieme'].max()
    group['orders_count'] = res
    return group
commandes = commandes.groupby('client_id').apply(orders_counting)

# Age en jour lors de la commandes
commandes['age'] = (commandes['order_created_at'] - commandes['first_order_date']).dt.days

# Date d'aujourd'hui
ajd = datetime.datetime.today().date()

###############################################################################
###################### MANIPULATION DYNAMIQUE DE DATA #########################
###############################################################################

# Filtre des commandes
def filtre_commandes(debut, fin):
    return  commandes.loc[(commandes['first_order_date'] >= debut) & (commandes['first_order_date'] <= fin),:].copy()

# Calcule les agrégats de toutes les commandes de chaque client
def agregation_par_client(group, Nmois):
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

# Création du dataframe des clients
def allcli_construct(Nmois, debut, fin):
    # Filtre des commandes
    df_commandes = filtre_commandes(debut, fin)
       
    # Agrégation
    allcli = df_commandes.groupby('client_id').apply(agregation_par_client, Nmois = Nmois).reset_index()
    
    # Calcul des durées
    allcli['age'] = (ajd - allcli['premiere']).dt.days
    allcli['ddv'] = (allcli['derniere'] - allcli['premiere']).dt.days
    allcli['pas_vu_depuis'] = (ajd - allcli['derniere']).dt.days
    
    # Le client est-il encore actif ?
        # 3 catégories de clients : 1 seule commande passées ; entre 2 et 5 ; 6 ou plus
    seuil_com1, seuil_com2 = [1, 5]
        # Nombres de jours nécessaires pour que les clients de chaque catégorie soient considérés comme parti
    seuil_jour1, seuil_jour2, seuil_jour3 = [30, 50, 70]
    allcli['actif'] = [ligne['pas_vu_depuis'] < seuil_jour1 if ligne['orders_count'] <= seuil_com1 else ligne['pas_vu_depuis'] < seuil_jour2 if ligne['orders_count'] <= seuil_com2 else ligne['pas_vu_depuis'] < seuil_jour3 for i, ligne in allcli.iterrows()]
    
    return allcli

# Fonction d'agregation des clients selon leur nombre de commandes
def agregation_methode_geometrique(group, N, Nmois):
    c1 = len(group)/N
    c2 = group['value_totale'].mean()
    c3 = group['valueXpremiers'].mean()
    c4 = group['valueXmoitie'].mean()
    c5 = group['valueXderniers'].mean()
    colnames = ['Probabilité', 'Value Totale', 'Value ' + str(Nmois) + ' premiers mois', 'Value ' + str(Nmois//2) + ' premiers '+ str(Nmois//2) + ' derniers mois', 'Value ' + str(Nmois) + ' derniers mois']
    return pd.Series([c1,c2,c3,c4,c5], index = colnames)

# Génère le tableau de la méthode 1
def methode_geometrique_tableau(allcli_json, Nmois):
    allcli = pd.read_json(allcli_json, orient = 'split')
    # Reformatage des dates
    allcli['premiere'] = pd.to_datetime(allcli['premiere'])
    allcli['derniere'] = pd.to_datetime(allcli['derniere'])
    
    # Regrouper les orders_count en classes
    bins = [1, 2, 3, 4, 5, 6, 9, 20] + [np.inf]
    labels = ['1','2','3','4','5','6-8','9-19','20+']
    allcli['classe'] = pd.cut(allcli['orders_count'], bins, labels = labels, right=False)
    
    # On ne garde que les clients qui ne sont plus actifs ou qui ont atteint la dernière classe de nombre de commandes
    allcli = allcli.loc[~(allcli['actif']) | (allcli['classe'] == labels[len(labels)-1]),:]
    
    return allcli.groupby('classe').apply(agregation_methode_geometrique, N = len(allcli), Nmois = Nmois).reset_index()

# Fonction d'agregation des cohortes
def agregation_cohortes(group):
    c1 = int(group['client_id'].nunique())
    c2 = int(group['order_number'].count())
    c3 = group['gross_revenue'].sum()
    colnames = ['nb_cli','nb_com','gross_revenue']
    return pd.Series([c1,c2,c3], index = colnames)

# Regroupe les clients par cohorte
def df_cohortes_construct(debut, fin, min_cli):
    df = filtre_commandes(debut, fin)
    # Age aujourd'hui en mois arrondi à l'inférieur (on ne compte que les mois complets)
    df['age_actuel_mois'] = (ajd - df['first_order_date']).dt.days//30
    # on enlève les commandes du mois en cours pour chaque client (si un client est là depuis 1,2 mois on se limite à 1 mois de données)
    df = df.loc[df['age']/30 <= df['age_actuel_mois'],:]
    # Age du client en mois au moment de sa commande
    df['age_mois'] = (df['order_created_at'] - df['first_order_date']).dt.days//30
    
    # Agrégation
    df_cohortes = df.groupby(['cohorte', 'age_mois']).apply(agregation_cohortes).reset_index()
    
    # On retire les cohortes qui ne contiennent pas assez de clients
    df_cohortes = df_cohortes.groupby('cohorte').filter(lambda group: group['nb_cli'].max() >= min_cli)
    
    return df_cohortes 

# Création du graph des cohortes
def graph_cohortes_construct(df_cohortes_json, Nmois):
    df_cohortes = pd.read_json(df_cohortes_json, orient = 'split')
    # Reformatage des dates
    df_cohortes['cohorte'] = pd.to_datetime(df_cohortes['cohorte']).dt.date
    
    # Séparation des cohortes
    split_cohortes = df_cohortes.groupby('cohorte')
    split_cohortes = [split_cohortes.get_group(x)[['age_mois','gross_revenue']] for x in split_cohortes.groups]
    
    # Noms des cohortes
    titres = [x.strftime('%B %y') + f''' ({int(df_cohortes.loc[df_cohortes['cohorte'] == x, 'nb_cli'].max())} clients)''' for x in df_cohortes['cohorte'].unique()]
    
    # Création du graphique
    ncols = 2 # Nombre de colonnes du layout
        # Jusqu'à combien de mois va-t-on en X : max entre Nmois et l'age de la plus vieille cohorte
    max_mois = max(df_cohortes['age_mois'].max(), Nmois)
    figure = tools.make_subplots(rows = int(math.ceil(len(titres)/ncols)),
                                 cols = ncols,
                                 subplot_titles = titres,
                                 shared_xaxes = True)
    # Indices pour la position des sous-graph
    i = 1
    j = 1
    # Pour chaque cohorte
    for c in split_cohortes:
        # Calcul du modèle
        coef = np.polyfit(c['age_mois'], np.log(c['gross_revenue']), 1)

        # Courbe théorique
        trace_theo = go.Scatter(x = np.arange(max_mois+1),
                               y = np.exp(coef[0]*np.arange(max_mois+1)+coef[1]),
                               mode = 'lines',
                               marker = dict(color = 'rgb(255, 0, 0)'))
        figure.append_trace(trace_theo, i, j)
        
        # Courbe empirique
        trace_emp = go.Scatter(x = list(c['age_mois']),
                           y = list(c['gross_revenue']),
                           mode = 'markers',
                           marker = dict(color = 'rgb(0, 0, 0)'))
        figure.append_trace(trace_emp, i, j)
        
        if j == ncols:
            j = 1
            i = i+1
        else:
            j = j+1
    
    figure['layout'].update(title = 'Evolution des dépenses des cohortes',
                            showlegend = False,
                            height = 750)
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
    
###############################################################################
################################# LAYOUT/VIEW #################################
###############################################################################

def generate_table(dataframe, max_rows=20):
    #Given dataframe, return template generated using Dash components
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

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
                        dcc.Input(id = 'input_Nmois', type = 'number', value = '18')
                    ], className = 'six columns'),
                    html.Div([
                        dcc.DatePickerRange(
                            id='date_range',
                            display_format = 'DD/MM/YY',
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
    
    # Résultat des études
    html.Div([
        # Colonne Méthode 1
        html.Div([
            html.H2('Méthode n°1'),
            html.Div(id = 'tableau_groupes_value', className = 'row'),
            html.Div(id = 'graph_poids_des_groupes', className = 'row')
        ], className = 'five columns'),
        # Colonne Méthode 2
        html.Div([
            html.H2('Méthode n°2'),
            html.Div([
                dcc.Graph(id = 'graph_cohortes')
            ], className = 'row'),
            html.Div(id = 'tableau_cohortes', className = 'row'),
        ], className = 'seven columns'),
    ], className = 'row'),
    
    # Détails des études
    html.Div([
        # Colonne méthode 1
        html.Div([
            html.H4('Détails Méthode n°1')
        ], className = 'six columns'),
        # Colonne méthode 2
        html.Div([
            html.H4('Détails Méthode n°2'),
            html.P('Ne conserver que les cohortes contenant au minimum'),
            dcc.Input(id = 'input_minimum_client', type = 'number', value = '20'),
            html.P('clients.')
        ], className = 'six columns'),
    ], className = 'row'),
    
    # Divs invisibles qui stockera les données intermédiaires
    html.Div(id = 'stock_allcli', style = {'display': 'none'}),
    html.Div(id = 'stock_cohortes', style = {'display': 'none'})
    
])

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})    

###############################################################################
################################## CONTROLLER #################################
###############################################################################

# Construction du df allcli
@app.callback(
    Output('stock_allcli','children'),
    [Input('button_valider', 'n_clicks')],
    [State('input_Nmois', 'value'),
     State('date_range','start_date'),
     State('date_range','end_date')])
def maj_allcli(n_clicks, Nmois, start_date, end_date):
    # Correction du typage des inputs
    Nmois = int(Nmois)
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Création du dataframe des clients
    allcli = allcli_construct(Nmois, start_date, end_date)
    
    return allcli.to_json(date_format = 'iso', orient = 'split')

# Construction et affichage du tableau de la méthode géométrique
@app.callback(
    Output('tableau_groupes_value', 'children'),
    [Input('stock_allcli', 'children')],
    [State('input_Nmois', 'value')])
def tableau(allcli_json, Nmois):
    # Correction du typage des inputs
    Nmois = int(Nmois)
    
    df = methode_geometrique_tableau(allcli_json, Nmois)
    return generate_table(df)

# Construction du df cohortes
@app.callback(
    Output('stock_cohortes', 'children'),
    [Input('button_valider', 'n_clicks')],
    [State('date_range','start_date'),
     State('date_range','end_date'),
     State('input_minimum_client','value')])
def maj_cohortes(n_clicks, start_date, end_date, min_cli):
    # Correction du typage des inputs
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    min_cli = int(min_cli)
    
    df_cohortes = df_cohortes_construct(start_date, end_date, min_cli)
    
    return df_cohortes.to_json(date_format = 'iso', orient = 'split')

# Construction et affichage du graph des cohortes
@app.callback(
    Output('graph_cohortes', 'figure'),
    [Input('stock_cohortes','children')],
    [State('input_Nmois', 'value')])
def graph_cohortes(df_cohortes_json, Nmois):
    # Correction du typage des inputs
    Nmois = int(Nmois)
    
    figure = graph_cohortes_construct(df_cohortes_json, Nmois)
    return figure

if __name__ == '__main__':
    app.run_server(debug=True)