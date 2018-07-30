# -*- coding: utf-8 -*-
"""
Created on Thu Jul 19 15:52:21 2018

@author: arnaud
"""

import sqlalchemy
import pandas as pd
import numpy  as np
import os

# Pour l'exécution en local
#if os.environ.get('PWD') != '/app':
#import sys
#sys.path.append('/home/arnaud/Documents')
#import Linfo_core


# Convertit des datetime sans tz à la tz Europe
def convert_tz(dates):
    # les dates sans TZ sont en fait en UTC (sur Core)
    dates = dates.dt.tz_localize('utc')
    
    # Maintenant on peut les convertir à l'heure de Paris
    dates = dates.dt.tz_convert('Europe/Paris')
    return dates

# Execute une requête SQL sur la BD Core et renvoie un dataframe
def extract_core(req):
    credentials = {
        'username': os.environ.get('dbuser'),
        'password': os.environ.get('dbpass'),
        'host': os.environ.get('dbhost'),
        'database': os.environ.get('dbname')}
    
    # URL de création de l'engine
    connect_url = sqlalchemy.engine.url.URL(
        'postgresql+psycopg2',
        username=credentials['username'],
        password=credentials['password'],
        host=credentials['host'],
        database=credentials['database'])
    
    # Création de l'engine
    engine = sqlalchemy.create_engine(connect_url)
    
    # Exécution de la requête
    df = pd.read_sql_query(req, engine)
    
    # Si le résultat contient des datetime on les convertit à l'heure de Paris
    
    # Ajout de la timezone Paris aux colonnes de dates
    for col in df.select_dtypes(include=[np.datetime64]) :
        df[col] = convert_tz(df[col])
    
    return df