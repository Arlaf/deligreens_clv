# -*- coding: utf-8 -*-

import os
import dash
import dash_auth

from models import module_commandes

# Pour avoir les mois des dates en français
import locale
locale.setlocale(2,'')

commandes = module_commandes.Commandes().commandes

# Déclaration de l'application    
app = dash.Dash('auth')
auth = dash_auth.BasicAuth(app,
                           [[os.environ['appuser'], os.environ['apppass']]])

server = app.server

# Pour éviter les warnings dus au multipage layout
app.config.suppress_callback_exceptions = True

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})
