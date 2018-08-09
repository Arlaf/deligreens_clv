# -*- coding: utf-8 -*-

import dash_core_components as dcc
import dash_html_components as html
import datetime
import utilitaires as util


def generate_html(app):
    # Layout
    app.layout = html.Div([
        dcc.Tabs(id="tabs", children=[
                
            # Onglet CLV
            dcc.Tab(label='CLV', children=[
                # Header
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
                                    max_date_allowed = util.ajd if util.ajd == util.lastday_of_month(util.ajd) else util.ajd - datetime.timedelta(util.ajd.day), # Dernier jour du dernier mois fini
                                    # Par défaut : du 1er mars 2017 à il y a 4 mois
                                    start_date = datetime.date(2017, 3, 1),
                                    end_date = datetime.date(util.AddMonths(util.ajd,-4).year, util.AddMonths(util.ajd,-4).month, util.lastday_of_month(util.AddMonths(util.ajd,-4)).day)
                                )
                            ], className = 'six columns'),
                    ], className = 'row'),
                    # Ligne du bouton
                    html.Div([
                        html.Button(id = 'button_valider', n_clicks = 0, children = 'Valider')
                    ], className = 'row')
                ], className = 'row'),
                
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
                                    dcc.Graph(id = 'graph_poids_des_groupes')
                                ], className = 'row')
                            ]),
                            # Onglet Détails (méthode 1)
                            dcc.Tab(label='Détails', children=[
                                html.P(['Utiliser la segmentation suivante pour créer les groupes de clients en fonction du nombre de commandes qu\'ils ont passées avant de partir ',
                                        dcc.Input(id = 'segmentation_nb_com', type = 'text', value = '1,2,3,4,5,6,9,20'),
                                        ' (Bornes inférieures de chaque groupe : entiers, dans l\'ordre croissant, séparés par des virgules et sans espace)']),
                                html.Div(id = 'tableau_segmentation')
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
                                html.P([
                                     'Ne conserver que les cohortes contenant au minimum ',
                                     dcc.Input(id = 'input_minimum_client', type = 'number', value = '20'),
                                     ' clients.'
                                ])
                            ]),
                        ])
                    ], className = 'six columns'),
                ], className = 'row'),
            ]),
            
            # Onglet
            dcc.Tab(label='Mort', children=[
                html.P(['Utiliser la segmentation suivante pour créer les groupes de clients en fonction du nombre de commandes qu\'ils ont passées ',
                        dcc.Input(id = 'segmentation_nb_com_actif', type = 'text', value = '1,2,6'),
                        ' (Bornes inférieures de chaque groupe : entiers, dans l\'ordre croissant, séparés par des virgules et sans espace)'
                ]),
                html.Label('Hauteur de la barre horizontale'),
                dcc.Slider(id = 'slider_pct', min = 0, max = 100, step = 5, value = 25)
            ]),
        
        
            # Divs invisibles qui stockeront les données intermédiaires
            html.Div(id = 'stock_allcli', style = {'display': 'none'}),
            html.Div(id = 'stock_tableau_geo', style = {'display': 'none'}),
            html.Div(id = 'stock_cohortes', style = {'display': 'none'}),
            html.Div(id = 'stock_tableau_cohortes', style = {'display': 'none'})
        ])
    ])
    