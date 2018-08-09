import numpy as np

# Construction du df_delai
def df_delais_construct(commandes):
    # Création d'un df_delais : une ligne est un délai en jour, revenu = True si le client a repassé commande après ce délai, False sinon
    df_delais = commandes.loc[~np.isnan(commandes['delai']), ['delai']].copy()
    df_delais['revenu'] = True
    
    df_temp = commandes.loc[np.isnan(commandes['delai']), ['pas_vu_depuis']].copy()
    df_temp = df_temp.rename({'pas_vu_depuis' : 'delai'}, axis = 'columns')
    df_temp['revenu'] = False
    
    df_delais = df_delais.append(df_temp)
    return df_delais

# Quand on observe qu'un client n'a pas commandé depuis X jours, combien a-t-on de chances de le revoir commander ?
def chances_de_recommander(df_delais, x):
    # Nombre de retours après un délai > x
    nb_ret = sum((df_delais['delai'] > x) & (df_delais['revenu']))
    nb_tot = sum(df_delais['delai'] > x)
    return nb_ret/nb_tot