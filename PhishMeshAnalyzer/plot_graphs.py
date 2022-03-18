import sys
sys.path.append('/home/sk-lab/Desktop/PhishProDetector/PhishMeshCrawler/')
import pandas as pd
import numpy as np
import json
from database import phish_db_layer
from matplotlib import pyplot as plt


def plot_pagewise_fields():

    def process_fields(rows):     
        elem_dict = {}
        elements = ','.join(rows).split(',')
        for e in elements:    
            if 'Unknown' not in e:        
                
                elem_dict[e] = elem_dict.get(e,0)+1        
        return json.dumps(elem_dict)

    def plot_pagewise_field_count(df_data):
        df_final = pd.DataFrame()

        for i,grp in df_data.iterrows():            
            page_rank = grp['page_rank']
            el_dict = json.loads(grp['page_elements'])
            
            if df_final.empty:
                df_final =pd.DataFrame(el_dict, index=[0])
                df_final = df_final.transpose().reset_index()
                df_final = df_final.rename(columns={"index":"fields", 0:"page_"+str(page_rank)})
                df_final.set_index('fields')
            else:
                df_final.reindex(list(el_dict.keys()))
                df_tmp =pd.DataFrame(el_dict, index=[0])
                df_tmp = df_tmp.transpose().reset_index()
                df_tmp = df_tmp.rename(columns={"index":"fields", 0:"page_"+str(page_rank)})
                df_final = df_final.merge(df_tmp,
                how = 'left', on = 'fields', suffixes = (False,False))
        
        ax = df_final.plot.bar(x='fields')
        ax.set_yscale('log')
        plt.show()

    page_fields = phish_db_layer.fetch_pagewise_fields()
    df_pages = pd.DataFrame(page_fields, columns=['site_id', 'page_elements', 'page_rank'])

    ### Group pages by theier page numbers and get the fields encountered per each groups
    df_grouped = df_pages.groupby(['page_rank'])['page_elements'].apply(lambda x: process_fields(x) ).reset_index()

    ### Plot the count of requested fields per page number
    plot_pagewise_field_count(df_grouped)
    
    # df_grouped2 = df_pages.sort_values(by = ['site_id', 'page_rank']).groupby(['site_id'])['page_elements'].apply(lambda x: '-->'.join(x) ).reset_index()
    # print(df_grouped2.head())
    # df_grouped2['page_count'] = df_grouped2['page_elements'].apply(lambda x : len(x.split('-->'))) 
    # df_grouped2.to_csv('pagewise_fields.csv')
    ### Filter the pages with more than 1 page count
    # site_ids = set(df_pages[df_pages['page_rank']>1]['site_id'].tolist())
    # df_filtered = df_pages[df_pages['site_id'].isin(site_ids)]
    # df_filtered = df_filtered.sort_values(by = ['site_id', 'page_rank'])
    # print(df_filtered.head())

plot_pagewise_fields()