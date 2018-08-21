# -*- coding: utf-8 -*-

import dash_core_components as dcc
import dash_html_components as html
import datetime
import utilitaires as util
import numpy as np

def generate_html(app):
    # Layout
    app.layout = html.Div([
            
#        # represents the URL bar, doesn't render anything
#        dcc.Location(id='url', refresh=False),  
#        # links
#        dcc.Link('Page CLV', href = '/clv'),
#        dcc.Link('Page new', href = '/new'),
        
        html.H1('Dashboard CLV'),
        dcc.Tabs(id="tabs", children=[
                
            ###################################################################
            ########################### Onglet CLV ############################
            ###################################################################
            
            dcc.Tab(label='Customer Lifetime Value', children=[
                # Header
                html.Div([
                    # Ligne input 1
                    html.Div([
                        html.Div([
                            html.Label('Sur combien de mois calculer la CLV')
                        ], className = 'six columns', style = {'vertical-align':'middle', 'text-align':'right'}),
                        html.Div([
                            dcc.Input(id = 'input_Nmois', type = 'number', value = '18')
                        ], className = 'six columns')
                        
                        
                    ], className = 'row'),
    
                    # ligne input 2
                    html.Div([
                        html.Div([
                            html.Label('Limiter l\'étude sur les clients qui ont passé leur première commande entre')
                        ], className = 'six columns', style = {'vertical-align':'middle', 'text-align':'right'}),
                        html.Div([
                            dcc.DatePickerRange(
                                    id='date_range',
                                    display_format = 'DD/MM/YY',
                                    min_date_allowed = datetime.date(2015, 1, 1),
                                    max_date_allowed = util.ajd if util.ajd == util.lastday_of_month(util.ajd) else util.ajd - datetime.timedelta(util.ajd.day), # Dernier jour du dernier mois fini
                                    # Par défaut : du 1er mars 2017 à il y a 4 mois
                                    start_date = datetime.date(2017, 3, 1),
                                    end_date = datetime.date(util.AddMonths(util.ajd,-4).year, util.AddMonths(util.ajd,-4).month, util.lastday_of_month(util.AddMonths(util.ajd,-4)).day)
                            ),
                            html.Button(id = 'button_valider', n_clicks = 0, children = 'Valider')
                        ], className = 'six columns')
                    ], className = 'row')
                ]),
                
                # Résultat des études
                html.Div([
                    # Colonne Méthode 1
                    html.Div([
                        html.H2('Méthode n°1'),
                        dcc.Tabs(id='tab_methode1', children=[
                            # Onglet Résultats (méthode 1)
                            dcc.Tab(label='Résultats', children=[
                                html.Div(id = 'tableau_groupes_value', className = 'row'),
                                html.Div([
                                    dcc.Graph(id = 'graph_poids_des_groupes'),
                                    html.Div([
                                        dcc.Dropdown(id = 'dropdown_column_plotted', clearable = False, options = {'label' : 'Value Totale', 'value' : 'Value Totale'}, value = 'Value Totale')
                                    ], style = {'width':'35%', 'textAlign':'center', 'margin' : '0 auto'})
                                ])
                            ]),
                            # Onglet Détails (méthode 1)
                            dcc.Tab(label='Détails', children=[
                                html.Div([
                                    html.P(['Utiliser la segmentation suivante pour créer les groupes de clients en fonction du nombre de commandes qu\'ils ont passées avant de partir ',
                                            dcc.Input(id = 'segmentation_nb_com', type = 'text', value = '1,2,3,4,5,6,9,20'),
                                            ' (Bornes inférieures de chaque groupe : entiers, dans l\'ordre croissant, séparés par des virgules et sans espace)']),
                                    html.Div(id = 'detail_date_methode_1'),
                                    html.P('Ils ont été regroupés selon leurs nombre de commandes (suivant la segmentation saisie ci-dessus) ainsi que selon s\'ils sont encore actifs ou non (grâce aux seuils d\'absence paramétrable dans l\onglet dédié)'),
                                    html.P("L'idée de cette méthode de calcul de la CLV (totale) est de prédire le nombre total de commandes qu'un nouveau client passera et à partir de là calculer sa valeur. Pour étudier le nombre de commandes total passées par les clients nous allons nous pencher sur un échantillon des clients : ceux qui ont effectivement atteint leur nombre final de commandes, c'est à dire ceux qui sont partis. En comptant simplement les clients de chaque catégorie on va pouvoir déterminer les chances qu'un nouveau client appartienne à chaque catégorie. On ajoute tout de même à cet échantillon les clients qui on atteint le dernier seuil de commandes saisi et qui sont toujours actifs. Ce sont nos clients les plus fidèles et bien qu'ils ne représentent pas la masse de nos clients, il ne faut pas les ignorer dans l'étude. Pour cette catégorie de client on ne connait pas leur nombre total de commandes puisqu'ils continuent d'en passer. On suppose donc qu'un fois ce dernier palier de commandes atteint, la probabilité de départ des clients après une commande est constante et donc que leur nombre de total de commande suivra une loi géométrique. Loi qu'on utilisera pour estimer leur nombre de commande moyen, chiffre sur lequel on se basera pour estimer la CLV totale de ces clients."),
                                    html.P("Les valeurs des clients à X mois sont elles des moyennes des données historiques, pas de prédiction nécessaires"),
#                                    html.Button(id = 'boutontest', n_clicks = 0, children = 'Valider'),
                                    html.Div(id = 'tableau_segmentation')
                                ], style = {'text-align':'justify'})
                            ])
                        ])
                    ], className = 'six columns'),
                    # Colonne Méthode 2
                    html.Div([
                        html.H2('Méthode n°2'),
                        dcc.Tabs(id='tab_methode2', children=[
                            # Onglet Résultats (méthode 2)
                            dcc.Tab(label='Résultats', children=[
                                html.Div([
                                    dcc.Graph(id = 'graph_cohortes')
                                ], className = 'row'),
                                html.Div(id = 'tableau_cohortes', className = 'row')
                            ]),
                            # Onglet Détails (méthode 2)
                            dcc.Tab(label='Détails', children=[
                                html.Div([
                                    html.P([
                                        'Ne conserver que les cohortes contenant au minimum ',
                                        dcc.Input(id = 'input_minimum_client', type = 'number', value = '20'),
                                        ' clients.'
                                    ]),
                                    html.Div(id = 'detail_date_methode_2'),
                                    html.P("Les clients ont été regroupés dans des cohortes qui correspondent au mois de leur première commande. Le gross revenue de chaque cohorte au fil des mois glissants a été calculé et nous nous sommes servi d'une regression logarithmique pour modéliser et prédire la suite des dépenses des cohortes et ainsi obtenir une estimation à x mois.")
                                ], style = {'text-align':'justify'})
                                
                            ]),
                        ])
                    ], className = 'six columns'),
                ], className = 'row'),
            ]),
            
            
            ###################################################################
            ################ Onglet choix des seuils de départ ################
            ###################################################################
    
            dcc.Tab(label='Détection des départs', children=[
                # Header
                html.Div([
                    html.Div([
                        html.Label('Regroupement des clients selon leur nombre de commandes'),
                        dcc.Input(id = 'segmentation_nb_com_actif', type = 'text', value = '1,2,6'),
                        html.Label('(Saisir les bornes inférieures de chaque groupe : chiffres entiers, dans l\'ordre croissant, séparés par des virgules et sans espace)')
                    ], className = 'three columns'),
                    html.Div([
                        html.Label('Se limiter aux clients arrivés après le :'),
                        dcc.DatePickerSingle(id='date_seuil', date = datetime.date(2017, 1, 1), display_format = 'DD/MM/YY')
                    ], className = 'three columns'),
                    html.Div([
                        html.Button(id = 'button_seuil_depart', n_clicks = 0, children = 'Valider')
                    ], className = 'three columns')
                ], className = 'row'),
                # Résultats
                html.Div([
#                    html.Div([
#                        html.Div([
#                            dcc.Graph(id = 'graph_ecdf_global')
#                        ], className = 'six columns'),
#                        html.Div([
#                            dcc.Graph(id = 'graph_chances_retour_global')
#                        ], className = 'six columns')
#                    ], className = 'row'),
                    html.Div([
                        html.Div([
                            dcc.Graph(id = 'graph_chances_retour_classe'),
                            html.Label('Hauteur de la barre horizontale'),
                            dcc.Slider(id = 'slider_pct', min = 0, max = 100, marks = {str(val) : str(val)+'%' for val in np.arange(0,105,5)}, value = 25)
                        ], className = 'six columns'),
                        html.Div([
                            dcc.Graph(id = 'graph_ecdf_classe'),
                            html.Label('Choix des seuils'),
                            dcc.Input(id = 'seuils_actif_inactif', type = 'text', value = '30,50,70'),
                            html.P("Ces seuils seront utilisés dans le reste de l'application pour déterminer si un client est toujours actif en se basant sur son nombre de commandes et sa durée d'absence.")
                        ], className = 'six columns'),
                    ], className = 'row')
                ], className = 'row')
                
            ]),
        
        
            # Divs invisibles qui stockeront les données intermédiaires
            html.Div(id = 'stock_allcli', style = {'display': 'none'}),
            html.Div(id = 'stock_tableau_geo', style = {'display': 'none'}),
            html.Div(id = 'stock_cohortes', style = {'display': 'none'}),
            html.Div(id = 'stock_tableau_cohortes', style = {'display': 'none'}),
            html.Div(id = 'stock_df_delais', style = {'display': 'none'})
        ])
    ], style = {'padding-left':'15px'})