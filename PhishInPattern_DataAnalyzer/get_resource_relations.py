
import networkx as nx
import sys
from networkx.algorithms.assortativity import neighbor_degree
import pandas as pd
import numpy as np
from pyppeteer import page
import tldextract
import matplotlib.pyplot as plt 
from networkx.algorithms import bipartite
from pprint import pprint
from calculate_hash import *
import ssdeep
import tarfile


containers_path = '../PhishMeshController/phish_containers_data/'
sha_file_hashes = defaultdict(list)
ssdeep_file_hashes = defaultdict(list)

def ignore_file(f):
    if f.endswith('.js') and all([x not in f for x in ['gremlin','jquery']]):
        return False
    return True

def calculate_res_hashes():
    global ssdeep_file_hashes, sha_file_hashes
    file_count = 0
    with open('../data/site_resource_details.csv','w') as fout:
        fout.write(','.join(['site_id', 'resource_file','ssdeep_hash', 'sha_hash'])+'\n')

    for d in os.listdir(containers_path)[:5000]:
        try:
            t = tarfile.open(containers_path+d+'/data.tar')
            # print(t)
            t.extractall()
            file_dir_path = './data/resources/'+d.replace('container_','')
            for f in os.listdir(file_dir_path):
                if ignore_file(f):
                    continue
                file_count = file_count+1
                sha_hash = calculate_sha_hash(file_dir_path+'/'+f, d+'_'+f )
                ssdeep_hash = calculate_ssdeep_hash(file_dir_path+'/'+f, d+'_'+f )
                sha_file_hashes[sha_hash].append(f)
                ssdeep_file_hashes[ssdeep_hash].append(f)
                with open('../data/site_resource_details.csv','a') as fout:
                    fout.write(','.join([file_dir_path.split('_')[-1], f.replace(',','_'), ssdeep_hash, sha_hash  ])+'\n')
            rmtree('./data')
            t.close()
        except Exception as te:
            print(te)

    print('Total Files :: ', file_count)
    print('SSDeep Hashes Count ::', len(ssdeep_file_hashes))
    print('SHA Hashes Count ::', len(sha_file_hashes))

    with open('../data/ssdeep_hashes.json','w') as f:
        json.dump(ssdeep_file_hashes, f, indent=4)

    with open('../data/sha_hashes.json','w') as f:
        json.dump(sha_file_hashes, f, indent=4)


def draw_resource_graph():

    df_resources = pd.read_csv('../data/site_resource_details.csv',header=0)

    # Create network graph from the dataframe connecting site domains and requested domains
    G_domains = nx.from_pandas_edgelist(df_resources, 'site_id', 'resource_file', ['resource_file'], create_using = nx.Graph())

    setA = df_resources['site_id'].unique()
    setB = df_resources['resource_file'].unique()
    G_domains.add_nodes_from(setA, bipartite = 0)
    G_domains.add_nodes_from(setB, bipartite = 1)
    density = nx.density(G_domains)
    print("Network density:", density)
    df_resources['cluster_component'] = -1    
    
    ### Calculate the number of domains that request each resource
    neighbors_count = [(n,len(list(G_domains.neighbors(n)))) for n in setB]

    print(len(G_domains.nodes()))
    ### Filter the top requested resource
    most_connected = sorted(neighbors_count, key = lambda x: x[1], reverse = True)[:100]
    most_connected = [(x,y) for (x,y) in most_connected if y>50]
    print(most_connected)
    for n,d in most_connected:
        G_domains.remove_node(n)
    print(len(G_domains.nodes()))
    # return

    ### Generate Connected componenets to see related domains
    S = [G_domains.subgraph(c).copy() for c in nx.connected_components(G_domains) ]
    print('Total No. of Clusters :: ', len(S))
    site_clusters = {}
    graph_id = 0
    for sgraph in S:
        density = nx.density(sgraph)
        print("Network density -",graph_id+1,' :: ', density)
       
        s_nodes = sgraph.nodes(data=True)
        site_nodes = [n for n,d in s_nodes if d['bipartite']==0]
        res_nodes =  [n for n,d in s_nodes if d['bipartite']==1]   

        pos = nx.spring_layout(sgraph, k=0.5, iterations=30)# scale=10)

        # nodes
        s_degree = [x[1]*10 for x in nx.degree(sgraph, site_nodes)]
        r_degree = [x[1]*10 for x in nx.degree(sgraph, res_nodes)]
        options = {"alpha": 0.5}
        nx.draw_networkx_nodes(sgraph, pos, nodelist=site_nodes, node_color="tab:grey", node_size= s_degree , **options)
        nx.draw_networkx_nodes(sgraph, pos, nodelist=res_nodes, node_color="tab:blue", node_size= r_degree , **options)
        # nx.draw_networkx_nodes(sgraph, pos, nodelist=top_nodes, node_color="tab:green", **options)
        nx.draw_networkx_labels(sgraph, pos, font_size=6 )
        nx.draw_networkx_edges(
            sgraph,
            pos,
            edgelist=sgraph.edges(),
            width=2,
            alpha=0.5,
            edge_color="tab:grey",
        )
        
        graph_id = graph_id+1
        # print(nx.degree(sgraph, site_nodes))
        site_clusters[graph_id] = {'sites': list(nx.degree(sgraph, site_nodes)), 'density': density , 'res_nodes': list(nx.degree(sgraph, res_nodes))}
        df_resources['cluster_component'] = df_resources.apply(lambda row : graph_id if row['site_id'] in s_nodes else row['cluster_component'], axis=1)
        # nx.draw(sgraph, pos= pos, labels = labelsdict, with_labels=True)

        # nx.write_gexf(sgraph,"../data/graph_plots/"+str(only_top)+'_'+str(graph_id)+".gexf")
        # plt.show()
        plt.tight_layout()
        s_nodes_len = len(site_nodes)
        if s_nodes_len>1 and s_nodes_len<200:
            plt.savefig("../data/graph_plots/"+str(graph_id)+'_'+str(s_nodes_len) +".pdf")
        plt.clf()
    
    with open('../data/site_resource_clusters.json', 'w') as fo:
        json.dump(site_clusters,fo, indent=2)


def draw_target_graph():

    df_resources = pd.read_csv('../data/target_domain_details.csv',header=0)

    # Create network graph from the dataframe connecting site domains and requested domains
    G_domains = nx.from_pandas_edgelist(df_resources, 'Source_Domain', 'Target_Domain',  create_using = nx.Graph())

    setA = df_resources['Source_Domain'].unique()
    setB = df_resources['Target_Domain'].unique()
    G_domains.add_nodes_from(setA, bipartite = 0)
    G_domains.add_nodes_from(setB, bipartite = 1)
    density = nx.density(G_domains)
    print("Network density:", density)
    df_resources['cluster_component'] = -1    
    
    ### Calculate the number of domains that request each resource
    neighbors_count = [(n,len(list(G_domains.neighbors(n)))) for n in setB]

    # print(len(G_domains.nodes()))
    # ### Filter the top requested resource
    # most_connected = sorted(neighbors_count, key = lambda x: x[1], reverse = True)[:100]
    # most_connected = [(x,y) for (x,y) in most_connected if y>50]
    # print(most_connected)
    # for n,d in most_connected:
    #     G_domains.remove_node(n)
    # print(len(G_domains.nodes()))
    

    ### Generate Connected componenets to see related domains
    S = [G_domains.subgraph(c).copy() for c in nx.connected_components(G_domains) ]
    print('Total No. of Clusters :: ', len(S))
    site_clusters = {}
    graph_id = 0
    for sgraph in S:
        density = nx.density(sgraph)
        print("Network density -",graph_id+1,' :: ', density)
       
        s_nodes = sgraph.nodes(data=True)
        site_nodes = [n for n,d in s_nodes if d['bipartite']==0]
        res_nodes =  [n for n,d in s_nodes if d['bipartite']==1]   

        pos = nx.spring_layout(sgraph, k=0.4, iterations=20)# scale=10)

        # nodes
        s_degree = [x[1]*20 for x in nx.degree(sgraph, site_nodes)]
        r_degree = [x[1]*20 for x in nx.degree(sgraph, res_nodes)]
        options = {"alpha": 0.5}
        nx.draw_networkx_nodes(sgraph, pos, nodelist=site_nodes, node_color="tab:red", node_size= s_degree , **options)
        nx.draw_networkx_nodes(sgraph, pos, nodelist=res_nodes, node_color="tab:blue", node_size= r_degree , **options)
        # nx.draw_networkx_nodes(sgraph, pos, nodelist=top_nodes, node_color="tab:green", **options)
        nx.draw_networkx_labels(sgraph, pos, font_size=8 )
        nx.draw_networkx_edges(
            sgraph,
            pos,
            edgelist=sgraph.edges(),
            width=2,
            alpha=0.5,
            edge_color="tab:grey",
        )
        
        graph_id = graph_id+1
        # print(nx.degree(sgraph, site_nodes))
        site_clusters[graph_id] = {'sites': list(nx.degree(sgraph, site_nodes)), 'density': density , 'res_nodes': list(nx.degree(sgraph, res_nodes))}
        df_resources['cluster_component'] = df_resources.apply(lambda row : graph_id if row['Source_Domain'] in s_nodes else row['cluster_component'], axis=1)
        # nx.draw(sgraph, pos= pos, labels = labelsdict, with_labels=True)

        # nx.write_gexf(sgraph,"../data/graph_plots/"+str(only_top)+'_'+str(graph_id)+".gexf")
        # plt.show()
        plt.margins(x=0.2)
        plt.tight_layout()
        s_nodes_len = len(site_nodes)
        if s_nodes_len>1 or  len(res_nodes)>1:
            print(graph_id, s_nodes_len, site_nodes)
            plt.savefig("../data/graph_plots/targets/"+str(graph_id)+'_'+str(s_nodes_len)+'_'+str(len(res_nodes)) +".pdf")
        plt.clf()
    
    # with open('../data/site_resource_clusters.json', 'w') as fo:
    #     json.dump(site_clusters,fo, indent=2)


def draw_field_relation_graph():

    import os 
    import itertools
    field_edges = []
    def get_edges(fields):
        nonlocal field_edges

        for x in fields.split(' && '):
            page_fields = x.split('--')
            page_fields = itertools.product(page_fields, page_fields)
            page_fields = [(x,y) for x,y in page_fields if x!=y]
            field_edges += page_fields

    df_multi = pd.read_csv('../data/data_pages_single.csv',header=0)
    df_multi = df_multi.fillna('Unknown')
    if True: #not os.path.exists('../data/fields_edges.csv'):
        df_multi['site_elements'].apply(lambda x: get_edges(x))
        with open('../data/fields_edges.csv', 'w') as f:
            for x,y in field_edges:
                f.write(x+','+y+'\n')

    df_resources = pd.read_csv('../data/fields_edges.csv', header = None)
    df_resources.columns = ['field_1', 'field_2']

    # Create network graph from the dataframe connecting site domains and requested domains
    G_domains = nx.from_pandas_edgelist(df_resources, 'field_1', 'field_2',  create_using = nx.Graph())

    setA = df_resources['field_1'].unique()
    setB = df_resources['field_2'].unique()
    # G_domains.add_nodes_from(setA, bipartite = 0)
    # G_domains.add_nodes_from(setB, bipartite = 1)
    density = nx.density(G_domains)
    print("Network density:", density)
    df_resources['cluster_component'] = -1    
    # nx.draw(G_domains)
    # plt.show()

    ### Calculate the number of domains that request each resource
    neighbors = [(n,list(G_domains.neighbors(n))) for n in setB]
    print(neighbors)

    s_nodes = G_domains.nodes(data=True)
    site_nodes = [n for n,d in s_nodes]
    pos = nx.spring_layout(G_domains, k=0.9, iterations=30)# scale=10)
    s_degree = [x[1]*20 for x in nx.degree(G_domains, site_nodes)]
    
    options = {"alpha": 0.5}

    nx.draw_networkx_nodes(G_domains, pos, node_color="tab:red", node_size= s_degree , **options)
    # nx.draw_networkx_nodes(sgraph, pos, nodelist=res_nodes, node_color="tab:blue", node_size= r_degree , **options)
    # nx.draw_networkx_nodes(sgraph, pos, nodelist=top_nodes, node_color="tab:green", **options)
    nx.draw_networkx_labels(G_domains, pos, font_size=8 )

    # weights = [sgraph[u][v]['weight'] for u,v in sgraph.edges()]
    minLineWidth = 0.25
    from collections import Counter
    c = Counter(G_domains.edges()) 
    # print(c)
    for u, v, d in G_domains.edges(data=True):
        # print(c[u,v])
        # print(u,v,d)
        d['weight'] = c[u, v]
    weights = nx.get_edge_attributes(G_domains,'weight').values()  
    # print(sgraph.edges())
    nx.draw_networkx_edges(
        G_domains,
        pos,
        edgelist=G_domains.edges(),
        # width=list(weights),
        alpha=0.5,
        edge_color="tab:grey",
    )
    # nx.write_gexf(sgraph,"../data/graph_plots/"+str(only_top)+'_'+str(graph_id)+".gexf")
    # plt.show()
    plt.margins(x=0.2)
    plt.tight_layout()
    # s_nodes_len = len(site_nodes)
    # if s_nodes_len>1 or  len(res_nodes)>1:
    #     print(graph_id, s_nodes_len, site_nodes)
    #     plt.savefig("../data/graph_plots/targets/"+str(graph_id)+'_'+str(s_nodes_len)+'_'+str(len(res_nodes)) +".pdf")
    plt.show()
    



def draw_field_graph():

    fields_per_page =  []
    
    def get_pagewise_fields(x):
        for s in x.split(' && '):
            fields_per_page.append(s.split('--'))
        
    from gensim.models import Word2Vec
    from sklearn.decomposition import PCA
    from matplotlib import pyplot
    from sklearn.manifold import TSNE
    import numpy as np

    # define training data
    sentences = []

    df_multi = pd.read_csv('../data/data_pages_multi_2.csv', header=0)
    df_multi = df_multi.fillna('Unknown')
    df_multi['fields'] = df_multi['site_elements'].apply(lambda x: get_pagewise_fields(x)) 
    sentences = fields_per_page
    print(len(sentences))
    
    # train model
    model = Word2Vec(sentences, min_count=1)
    # fit a 2d PCA model to the vectors
    X = model[model.wv.vocab]

    pca = PCA(n_components=2)
    result = pca.fit_transform(X)
    # create a scatter plot of the projection
    # pyplot.scatter(result[:, 0], result[:, 1])
    words = list(model.wv.vocab)
    # print(words)
    # for i, word in enumerate(words):
    #     pyplot.annotate(word, xy=(result[i, 0], result[i, 1]))
    # pyplot.show()
    embedding_clusters = []
    word_clusters = []
    for word in words:
        embeddings = []
        words = []
        for similar_word, _ in model.most_similar(word, topn=30):
            words.append(similar_word)
            embeddings.append(model[similar_word])
        embedding_clusters.append(embeddings)
        word_clusters.append(words)
    
    

    embedding_clusters = np.array(embedding_clusters)
    n, m, k = embedding_clusters.shape
    tsne_model_en_2d = TSNE(perplexity=15, n_components=2, init='pca', n_iter=3500, random_state=32)
    embeddings_en_2d = np.array(tsne_model_en_2d.fit_transform(embedding_clusters.reshape(n * m, k))).reshape(n, m, 2)

    import matplotlib.cm as cm
    

    def tsne_plot_similar_words(title, labels, embedding_clusters, word_clusters, a, filename=None):
        pyplot.figure(figsize=(16, 9))
        colors = cm.rainbow(np.linspace(0, 1, len(labels)))
        for label, embeddings, words, color in zip(labels, embedding_clusters, word_clusters, colors):
            x = embeddings[:, 0]
            y = embeddings[:, 1]
            plt.scatter(x, y, alpha=a, label=label)
            for i, word in enumerate(words):
                plt.annotate(word, alpha=0.5, xy=(x[i], y[i]), xytext=(5, 2),
                            textcoords='offset points', ha='right', va='bottom', size=8)
        # pyplot.legend(loc=4)
        # pyplot.title(title)
        pyplot.grid(False)
        if filename:
            plt.savefig(filename, format='png', dpi=150, bbox_inches='tight')
        plt.show()


    tsne_plot_similar_words('Similar words from Google News', words, embeddings_en_2d, word_clusters, 0.7,
                            'similar_words.png')

if __name__=='__main__':

    # calculate_res_hashes()
    # draw_resource_graph()

    # draw_target_graph()

    draw_field_relation_graph()

    draw_field_graph()