from collections import defaultdict
from os import read
from matplotlib.colors import Colormap
from numpy.core.shape_base import block
import pandas as pd
from collections import defaultdict
from matplotlib import pyplot as plt
from difflib import SequenceMatcher
import tldextract
import numpy as np

all_fields_count = {}
multi_domains = []
max_pages = 0
all_fields = []

###
### Get FQDN from the URL
###
def get_FQDN(url):
    if url == None:
        return ''
    ext = tldextract.extract(url)
    fqdn = '.'.join(ext[:3])
    return fqdn

def plot_pagewise_fields(file_path, d_fname):
    global all_fields_count
    global multi_domains
    global all_fields
    global max_pages
    fields_count = defaultdict(dict)

    def get_common_strings(titles):
        if len(titles)>1:
            titles[0] = titles[0].replace('http://','').replace('https://','')
            titles[-1] = titles[-1].replace('http://','').replace('https://','')
            seq = SequenceMatcher(None, titles[0],titles[-1])
            match = seq.find_longest_match(0,len(titles[0]),0,len(titles[-1]))
            if match.size!=0:
                return titles[0][match.a:match.a+match.size]
            return ''
        return ''
    
    def get_site_domains(domains):
        for dom in domains[:-1]:
            dom = get_FQDN(dom)
            domains[-1] = get_FQDN(domains[-1])
            multi_domains.append(dom+','+domains[-1])

    def add_count(p_num,f):
        if 'Unkno' in f:
            f = 'Other'
        f = f.replace(' ','')
        p_num = 'Page_'+str(p_num+1)
        fields_count[p_num][f] = fields_count[p_num].get(f,0)+1
        all_fields_count[f] = all_fields_count.get(f,0)+1

    def get_session_based_evasion(p_elems):
        first_els = p_elems[0].split('--')
        if  'Unknown' in first_els: #len(set(first_els))==1 and
            other_elems = ''.join(p_elems).replace('--','').replace('Unknown','')
            if len(p_elems)>1 and len(other_elems)>0:
                # print(p_elems, first_els, other_elems)
                return True
        return False

    df_multi = pd.read_csv(file_path, header=0)
    df_multi = df_multi.fillna('Unknown')
    df_multi['field_group']  = df_multi['site_elements'].apply(lambda x: ' && '.join(['--'.join(sorted(list(set(e.split('--'))))) 
                                                                                    for e in x.split(' && ')]))
    df_multi['domain_count'] = df_multi.groupby(['field_group']).transform('nunique')['page_domains']
    n_multi_domain = df_multi[df_multi['domain_count']>1]['field_group'].nunique()
    
    print(df_multi['site_id'].nunique())
    print(n_multi_domain)
    # print(df_multi.head(10))
    print(df_multi['field_group'].nunique())

    
    df_multi['field_group'].apply(lambda x: [ add_count(p_num,f) for p_num,e in enumerate(x.split(' && ')) for f in e.split('--')])
    df_multi['page_domains_common'] = df_multi['page_domains'].apply(lambda x: get_common_strings(x.split(' && ')) )
    # df_multi.to_csv('test_data_with_target.csv')
    # print(list(df_multi['page_domains_common'].unique()))
    
    df_multi['page_domains'].apply(lambda x: get_site_domains(x.split(' && ')) )

    with open('../data/target_domain_details.csv','w') as fd:
        fd.write('Source_Domain,Target_Domain\n')
        fd.write('\n'.join(multi_domains))
    
    ### detect session based evasion
    df_multi ['session'] = df_multi['site_elements'].apply(lambda x:  get_session_based_evasion(x.split(' && ')))
    df_session = df_multi[df_multi['session']==True]
    df_session.to_csv('../data/session_evasion.csv', index=False)

    
    df_fields = pd.DataFrame.from_dict(fields_count)
    # print(df_session)
    max_pages = max(max_pages,len(fields_count.keys()))
    cols = []
    for i in range(max_pages,0,-1):
        cols.append('Page_'+str(i))
        if 'Page_'+str(i) not in df_fields.columns:
            df_fields['Page_'+str(i)] =[np.nan] * df_fields.shape[0]
    df_fields = df_fields[cols]
    df_fields = df_fields.sort_values(by=['Page_1'], ascending=False)
    if  len(all_fields)==0:
        all_fields = df_fields.index
    ## use same x-axis ordering for both graphs
    df_fields = df_fields.reindex(all_fields)
    

    ax = df_fields.plot.bar(subplots=True, colormap = 'Dark2', sharey=True, sharex=True)
    
    # ax[0].set_ylim((0,200))
    
    plt.yscale('log')
    for c in range(len(cols)):
        if c < max_pages - len(fields_count.keys()):
            ax[c].set_visible(False)
        ax[c].set_ylabel('Count')
        ax[c].set_yticks([10, 100, 1000])
    # plt.ylabel('Field Count')
    plt.xlabel('Field Categories')

    plt.tight_layout()
    # plt.show()
    
    plt.savefig('../data/paper_graphs/'+d_fname+'_page_fields.pdf')



if __name__ =='__main__':

    file_path = '../data/data_pages_multi_2.csv'
    plot_pagewise_fields(file_path,'multi_2')

    # file_path = '../data/data_pages_single.csv'
    # plot_pagewise_fields(file_path,'single_2')

    # # file_path = '../data/data_pages_top.csv'
    # # plot_pagewise_fields(file_path,'top')

    # # all_fields_count.pop('Other')
    # print(all_fields_count)
    # df_fields = pd.DataFrame.from_dict(all_fields_count, orient='index')
    # df_fields = df_fields.reset_index()
    # df_fields.columns = ['Field Category','Count']
    # df_fields.set_index('Field Category')
    # df_fields = df_fields.sort_values(by=['Count'], ascending=False)
    # print(df_fields)

    # df_fields.plot.barh(y='Count', x = 'Field Category')
    # plt.tight_layout()
    # # plt.show(block=True)
    # plt.savefig('../data/paper_graphs/fields_count.pdf')
