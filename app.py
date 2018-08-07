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
#import plotly.plotly as py
import plotly.graph_objs as go

###############################################################################
###################### VARIABLES GLOBALES ET IMMUABLES ########################
###############################################################################

# Pour avoir les dates en français
import locale
locale.setlocale(2,'')
    
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

# Calcul des date de première et dernière commandes
def first_last_order(group):
    premiere = group['order_created_at'].min()
    derniere = group['order_created_at'].max()
    group['first_order_date'] = premiere
    group['lastest_order_date'] = derniere
    return group
# Ajout des colonnes date de première et dernière commandes
commandes = commandes.groupby('client_id').apply(first_last_order)

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

# Format d'affichage des montants
def format_montant(nb):
    return ['{:,.2f}'.format(x).replace(',', ' ') + ' €' for x in nb]

# Format d'affichage des pourcentages
def format_pct(pct):
    return '{:.1f}'.format(100*pct)

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

# Espérance géométrique du nombre de commandes
#def prevision_nb_commandes():
    

# Création du dataframe des clients
def allcli_construct(Nmois, debut):
    # On ne garde que les clients qui ont passé au moins une commande après la date choisie
    df_commandes = commandes.loc[commandes['lastest_order_date'] >= debut,:].copy()
       
    # Agrégation
    allcli = df_commandes.groupby('client_id').apply(agregation_par_client, Nmois = Nmois).reset_index()
    
    # Calcul des durées
    allcli['age'] = (ajd - allcli['premiere']).dt.days
    allcli['ddv'] = (allcli['derniere'] - allcli['premiere']).dt.days
    allcli['pas_vu_depuis'] = (ajd - allcli['derniere']).dt.days
    
    # Le client est-il encore actif ?
        # 3 catégories de clients : 1 seule commande passées ; entre 2 et 5 ; 6 ou plus
    seuil_com = [1, 5]
        # Nombres de jours nécessaires pour que les clients de chaque catégorie soient considérés comme parti
    seuil_jour = [30, 50, 70]
    allcli['actif'] = [ligne['pas_vu_depuis'] < seuil_jour[0] if ligne['orders_count'] <= seuil_com[0] else ligne['pas_vu_depuis'] < seuil_jour[1] if ligne['orders_count'] <= seuil_com[1] else ligne['pas_vu_depuis'] < seuil_jour[2] for i, ligne in allcli.iterrows()]
    
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
    tableau_geo = allcli.groupby('classe').apply(agregation_methode_geometrique, N = len(allcli), Nmois = Nmois).reset_index()
    
    # On place notre valeur estimée dans le tableau
    tableau_geo.loc[tableau_geo['classe'] == labels[len(labels)-1], 'Value Totale'] = value_estimee
    
    # Calcul d'une ligne moyenne
    ligne_moyenne = ['Moyenne', 1.0]
    for i in range(2,6):
        ligne_moyenne.append(sum(tableau_geo['Probabilité'] * tableau_geo.iloc[:,i]))
        
    # Ajout de la ligne moyenne
    tableau_geo = tableau_geo.append(pd.DataFrame([ligne_moyenne], columns =list(tableau_geo.columns)), ignore_index=True)
    return  tableau_geo

# Fonction d'agregation des clients en cohortes
def agregation_clients_cohortes(group):
    c1 = int(group['client_id'].nunique())
    c2 = int(group['order_number'].count())
    c3 = group['gross_revenue'].sum()
    colnames = ['nb_cli','nb_com','gross_revenue']
    return pd.Series([c1,c2,c3], index = colnames)

# input : un dataframe contenant les dépenses par mois d'une seule cohorte et le nombre de mois minimum jusqu'auquel faire les prévisions
# output : même dataframe avec la colonne des prévisions en plus
def modelisation_depenses_cohorte(cohorte, Nmois):
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
def df_cohortes_construct(debut, fin, Nmois, min_cli):
    # Filtrage des commandes selon les dates de première commande des clients
    df = commandes.loc[(commandes['first_order_date'] >= debut) & (commandes['first_order_date'] <= fin),:].copy()
    # Age aujourd'hui en mois arrondi à l'inférieur (on ne compte que les mois complets)
    df['age_actuel_mois'] = (ajd - df['first_order_date']).dt.days//30
    # on enlève les commandes du mois en cours pour chaque client (si un client est là depuis 1,2 mois on se limite à 1 mois de données)
    df = df.loc[df['age']/30 <= df['age_actuel_mois'],:]
    # Age du client en mois au moment de sa commande
    df['age_mois'] = (df['order_created_at'] - df['first_order_date']).dt.days//30
    
    # Agrégation
    df_cohortes = df.groupby(['cohorte', 'age_mois']).apply(agregation_clients_cohortes).reset_index()
    
    # On retire les cohortes qui ne contiennent pas assez de clients
    df_cohortes = df_cohortes.groupby('cohorte').filter(lambda group: group['nb_cli'].max() >= min_cli)
    
    # Séparation des cohortes
    split_cohortes = df_cohortes.groupby('cohorte')
    split_cohortes = [split_cohortes.get_group(x).reset_index(drop = True) for x in split_cohortes.groups]
    
    # On réinitialise le df_cohortes
    df_cohortes = pd.DataFrame()
    for cohorte in split_cohortes:
        df_cohortes = df_cohortes.append(modelisation_depenses_cohorte(cohorte, Nmois), sort = False).reset_index(drop = True)
    
    return df_cohortes 

# Création du graph des cohortes
def graph_cohortes_construct(df_cohortes_json, Nmois):
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
        
        if j == ncols:
            j = 1
            i = i+1
        else:
            j = j+1
    
    figure['layout'].update(title = 'Evolution des dépenses des cohortes',
                            showlegend = False,
                            height = 850)
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
def agregation_cohortes(group, Nmois):
    c1 = group['nb_cli'].max()
    c2 = group.loc[group['age_mois']<=Nmois, 'estimation'].sum()
    c3 = c2/c1
    colnames = ['Nombre de clients', 'Valeur de la cohorte à ' + str(Nmois) + ' mois', ' Valeur moyenne d\'un client']
    return pd.Series([c1,c2,c3], index = colnames)

# Création du tableau des cohortes
def tableau_cohortes_construct(df_cohortes_json, Nmois):
    df_cohortes = pd.read_json(df_cohortes_json, orient = 'split')
    # Reformatage des dates
    df_cohortes['cohorte'] = pd.to_datetime(df_cohortes['cohorte']).dt.date
    
    tableau = df_cohortes.groupby('cohorte').apply(agregation_cohortes, Nmois = Nmois).reset_index()
    
    return tableau
    
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
        ], className = 'six columns'),
        # Colonne Méthode 2
        html.Div([
            html.H2('Méthode n°2'),
            html.Div([
                dcc.Graph(id = 'graph_cohortes')
            ], className = 'row'),
            html.Div(id = 'tableau_cohortes', className = 'row'),
        ], className = 'six columns'),
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
            html.P([
                 'Ne conserver que les cohortes contenant au minimum ',
                 dcc.Input(id = 'input_minimum_client', type = 'number', value = '20'),
                 ' clients.'
            ]),
            
        ], className = 'six columns'),
    ], className = 'row'),
    
    # Divs invisibles qui stockera les données intermédiaires
    html.Div(id = 'stock_allcli', style = {'display': 'none'}),
    html.Div(id = 'stock_cohortes', style = {'display': 'none'}),
    html.Div(id = 'stock_tableau_cohortes', style = {'display': 'none'})
    
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
    allcli = allcli_construct(Nmois, start_date)
    
    return allcli.to_json(date_format = 'iso', orient = 'split')

# Construction et affichage du tableau de la méthode géométrique
@app.callback(
    Output('tableau_groupes_value', 'children'),
    [Input('stock_allcli', 'children')],
    [State('input_Nmois', 'value')])
def tableau_geo(allcli_json, Nmois):
    # Correction du typage des inputs
    Nmois = int(Nmois)
    
    tableau = methode_geometrique_tableau(allcli_json, Nmois)
    
    # Format d'affichage des nombres
    for col in tableau.drop(['Probabilité'],axis = 1).select_dtypes(include = ['float64']):
        tableau[col] = format_montant(tableau[col])
        
    # Format d'affichage des pourcentages
    tableau['Probabilité'] = [format_pct(x) + ' %' for x in tableau['Probabilité']]
    
    return generate_table(tableau)

# Construction du df cohortes
@app.callback(
    Output('stock_cohortes', 'children'),
    [Input('button_valider', 'n_clicks')],
    [State('date_range','start_date'),
     State('date_range','end_date'),
     State('input_Nmois', 'value'),
     State('input_minimum_client','value')])
def maj_cohortes(n_clicks, start_date, end_date, Nmois, min_cli):
    # Correction du typage des inputs
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    Nmois = int(Nmois)
    min_cli = int(min_cli)
    
    df_cohortes = df_cohortes_construct(start_date, end_date, Nmois, min_cli)
    
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

# Construction du tableau des cohortes
@app.callback(
    Output('stock_tableau_cohortes', 'children'),
    [Input('stock_cohortes','children')],
    [State('input_Nmois', 'value')])
def tableau_cohortes(df_cohortes_json, Nmois):
    # Correction du typage des inputs
    Nmois = int(Nmois)
    
    tableau = tableau_cohortes_construct(df_cohortes_json, Nmois)
    return tableau.to_json(date_format = 'iso', orient = 'split')

# Affichage du tableau des cohortes
@app.callback(
        Output('tableau_cohortes', 'children'),
        [Input('stock_tableau_cohortes', 'children')])
def affichage_tableau_cohortes(tableau_json):
    tableau = pd.read_json(tableau_json, orient = 'split')
    # Reformatage des dates
    tableau['cohorte'] = pd.to_datetime(tableau['cohorte']).dt.date
    
    # Formatage du mois de la cohorte pour l'affichage
    tableau['cohorte'] = [x.strftime('%B %y').capitalize() for x in tableau['cohorte']]
    
    # Formatage des nombres pour l'affichage
    for col in tableau.select_dtypes(include = ['float64']):
        tableau[col] = format_montant(tableau[col])
        
    tableau = tableau.rename({'cohorte' : 'Cohorte'}, axis = 'columns')
    return generate_table(tableau)

if __name__ == '__main__':
    app.run_server(debug=True)