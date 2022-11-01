## Demo code source : https://www.datacamp.com/community/tutorials/social-network-analysis-python
import networkx as nx
import sys
from networkx.algorithms.assortativity import neighbor_degree
sys.path.append('/home/sk-lab/Desktop/PhishProDetector/PhishMeshCrawler/')
import pandas as pd
import numpy as np
import tldextract
from database import phish_db_layer
import matplotlib.pyplot as plt 
from networkx.algorithms import bipartite
from pprint import pprint
from calculate_hash import *

domains = {}
CRITICAL_INPUT_CATEGORY = {'Password', 'Card', 'ExpDate', 'SSN', 'Zip', 'CVV'}

data_file = '../data/request_url_relationship.txt'



def get_domain_request_relationship():
    
    ###
    ### Get FQDN from the URL
    ###
    def get_FQDN(url):
        if url == None:
            return ''
        ext = tldextract.extract(url)
        fqdn = '.'.join(ext[:3])
        return fqdn


    ###
    ### Calculate Context Triggered Piecewise Hash (CTPH) for the resource files and cluster the hashes to get similar files
    ###
    def add_ssdeep_hash_column(df_data):
        
        df_data = df_data.fillna({'res_file_path':''})
        df_data['res_file_path'] = df_data['res_file_path'].apply(lambda x: x.replace('container_',''))

        ## calculate ssdeep hashes for all resources                                                               
        f_hashes = []
        f_hash_cluster = defaultdict(set)

        for i,x in enumerate(df_data['res_file_path']):            
            fhash = calculate_ssdeep_hash('/Data/PhishMesh_Data/container_'+x[x.index('/resources/'):].split('/')[2]+'/data.tar', x[x.index('/resources/'):]) if 'resources' in x else ''
            f_hashes.append(fhash)            
            similar_hashes = cluster_ssdeep_hashes(fhash, set(f_hashes))
            if len(similar_hashes)>0:
                similar_hash = list(similar_hashes.keys()).pop()
                f_hash_cluster[similar_hash].add(i)
            else:
                f_hash_cluster[fhash].add(i)
            print(len(f_hashes))
        
        hash_clusters = [-1] * len(f_hashes) 

        cluster_id = 0
        for k,x in f_hash_cluster.items():           
            for ind in x:
                hash_clusters[ind] = 'SDC::'+str(cluster_id)

            cluster_id = cluster_id +1


        df_data['ssdeep_hashes'] = f_hashes
        df_data['ssdeep_clusters'] = hash_clusters
        
        return df_data

    ###
    ### Calulate required information per site level for further analysis
    ###
    def calculate_metadata(df_res):
        global CRITICAL_INPUT_CATEGORY

        ## Print detailed info on the fetched data
        print('Total Number of Sites ::', len(df_res['site_id'].unique()))
        print('Total Number of Top Sites ::', len(df_res[df_res['is_top_site']==1]['site_id'].unique())) 
        print('Total number of Phishing sites ::', len(df_res[df_res['is_top_site']==0]['site_id'].unique()))
       
        ## calculate additional metadata columns      
        df_res['site_domain'] = [get_FQDN(u) for u in df_res['site_url']]
        df_res['res_domain'] = ['R_'+get_FQDN(u) for u in df_res['resource_url']]  
        df_res = df_res.fillna({'page_elements':'', 'resource_url':''})
        df_res['page_unique_req_count'] = df_res.groupby(['site_id', 'page_url']).transform('nunique')['resource_url']       
        df_res['has_critical_input'] = df_res['page_elements'].apply(lambda x : 1 if x!=None and any([c in x for c in CRITICAL_INPUT_CATEGORY]) else 0)
        df_res['critical_page_count'] = df_res[['site_id','has_critical_input','page_elements']].groupby(['site_id','has_critical_input']).transform('nunique')['page_elements']
        df_res['critical_page_count'] = df_res.apply(lambda x: x['critical_page_count'] if x['has_critical_input']==1 else 0, axis=1) 
        df_res['third_party_unique_req_count'] = df_res.groupby(['site_id', 'page_url']).transform('nunique')['res_domain']
        # df_res = add_ssdeep_hash_column(df_res)
        
        df_top_sites = df_res[df_res['is_top_site']==1]
        print('------------------Top Sites Statistics-------------')        
        print(df_top_sites.describe())

        df_phishing_sites = df_res[df_res['is_top_site']==0]
        print('------------------Phishing Sites Statistics---------')
        print(df_phishing_sites.describe())
    
        return df_res

    ## get resource data from a dataframe
    res_det = phish_db_layer.fetch_requested_resources()

    ## store data from database ina  dataframe
    df_resources = pd.DataFrame(res_det , columns = ['site_id', 'site_url','page_count','page_elements','page_url','resource_url','res_file_hash','res_file_path', 'is_top_site'])
    
    df_resources = calculate_metadata(df_resources)
       
    return df_resources


def draw_domain_request_relationship(df_resources, only_top =None):
    
    ###
    ### calculte additional columns
    ###
    def calculate_additional_columns(df_res):

        phish_top_resource_domains = []
        legit_top_resource_domains = []
        with open('../data/phish_top_request_domains.csv', 'r') as f:
            phish_top_resource_domains = f.read().split('\n')
        
        with open('../data/legit_top_request_domains.csv', 'r') as f:
            legit_top_resource_domains = f.read().split('\n')
        
        if 'R_' in phish_top_resource_domains:
            phish_top_resource_domains.remove('R_')
        

        if 'R_' in legit_top_resource_domains:
            legit_top_resource_domains.remove('R_')
        
        ### create temp dataframe to store intermediate values
        df_temp = pd.DataFrame()
        df_temp['site_id'] = df_res['site_id']
        df_temp['is_top_legit_request_domain'] = df_res['res_domain'].apply(lambda x: x if x in legit_top_resource_domains else np.nan)
        df_temp['is_top_phish_request_domain'] = df_res['res_domain'].apply(lambda x: x if x in phish_top_resource_domains else np.nan)

        ### Columns to represent count of top requested_domains
        df_res['count_legit_top_request_domains'] = df_temp.groupby(['site_id'])['is_top_legit_request_domain'].transform('nunique')
        df_res['count_phish_top_request_domains'] = df_temp.groupby(['site_id'])['is_top_phish_request_domain'].transform('nunique')

        return df_res

    ## Filter data based on the parameter only_top
    if only_top != None:
        df_resources = df_resources[df_resources['is_top_site'] == only_top] 

    # Create network graph from the dataframe connecting site domains and requested domains
    G_domains = nx.from_pandas_edgelist(df_resources, 'site_domain', 'res_domain', ['is_top_site'], create_using = nx.Graph())

    legitimate_nodes = set(df_resources[df_resources['is_top_site'] == 1]['site_domain'].to_list())
    print(df_resources.info())

    setA = df_resources['site_domain'].unique()
    setB = df_resources['res_domain'].unique()
    G_domains.add_nodes_from(setA, bipartite = 0)
    G_domains.add_nodes_from(setB, bipartite = 1)
    density = nx.density(G_domains)
    print("Network density:", density)
    df_resources['cluster_component'] = -1    
    # nx.write_gexf(G_domains, '../data/graph_plots/domain_resources.gexf')
    
    ### Calculate the number of domains that request each resource
    neighbors_count = [(n,len(list(G_domains.neighbors(n)))) for n in setB]

    ### Filter the top requested resource
    most_connected = sorted(neighbors_count, key = lambda x: x[1], reverse = True)[:100]

    ### Generate Connected componenets to see related domains
    S = [G_domains.subgraph(c).copy() for c in nx.connected_components(G_domains) ]
    print('Total No. of Clusters :: ', len(S))

    graph_id = 0
    for sgraph in S:
        density = nx.density(sgraph)
        print("Network density -",graph_id+1,' :: ', density)
        l, r = nx.bipartite.sets(sgraph)
        s_nodes = sgraph.nodes()
        sites = '#--#'.join( l).replace('.','_') 
        
        top_nodes = [n for n in s_nodes if n in legitimate_nodes]        
        pos = nx.spring_layout(sgraph, scale=0.4)

        # nodes
        options = {"node_size": 80, "alpha": 0.5}
        nx.draw_networkx_nodes(sgraph, pos, nodelist=l, node_color="tab:red", **options)
        nx.draw_networkx_nodes(sgraph, pos, nodelist=r, node_color="tab:blue", **options)
        nx.draw_networkx_nodes(sgraph, pos, nodelist=top_nodes, node_color="tab:green", **options)
        nx.draw_networkx_labels(sgraph, pos, font_size=6)
        nx.draw_networkx_edges(
            sgraph,
            pos,
            edgelist=sgraph.edges(),
            width=2,
            alpha=0.5,
            edge_color="tab:grey",
        )
        
        graph_id = graph_id+1
        df_resources['cluster_component'] = df_resources.apply(lambda row : graph_id if row['site_domain'] in s_nodes else row['cluster_component'], axis=1)
        # nx.draw(sgraph, pos= pos, labels = labelsdict, with_labels=True)

        nx.write_gexf(sgraph,"../data/graph_plots/"+str(only_top)+'_'+str(graph_id)+".gexf")
        # plt.show()
        plt.tight_layout()
        plt.savefig("../data/graph_plots/"+str(only_top)+'_'+str(graph_id)+".pdf")
        plt.clf()
    df_resources['cluster_component'] = df_resources['cluster_component'].apply(lambda x: "C::"+str(x))

    if only_top == None:
        df_resources = calculate_additional_columns(df_resources)
        df_resources.to_csv('../data/domain_resources_cluster.csv', index=False)
    most_connected = set([x[0] for x in most_connected if x[1]>0 ])
    
    return most_connected



def prepare_and_scale_data(df_data):
    ## import section
    from sklearn.preprocessing import StandardScaler
    ##

    ## Preprocess data
    drop_columns = ['site_url','page_url','resource_url','page_elements','res_file_hash','res_file_path','is_top_site','site_domain','res_domain','has_critical_input', 'cluster_component']
    feature_columns = ['page_count','page_unique_req_count','critical_page_count','third_party_unique_req_count']
    
    ## group pages information per site to get per site information
    df_data_grouped = df_data.groupby(['site_id']).first().reset_index()
    df_data_processed = df_data_grouped.drop(drop_columns,axis=1)

    # convert categorical data to one-hot encoding
    df_clusters = pd.get_dummies(df_data_grouped['cluster_component'], prefix='cluster')
        
    ## Scale dataset
    scaler = StandardScaler()
    scaler.fit(df_data_processed)
    X_scale = scaler.transform(df_data_processed)
    df_scale = pd.DataFrame(X_scale, columns=df_data_processed.columns)
    df_data_processed = pd.concat([df_scale, df_clusters],axis=1)

    return df_data_grouped ,df_data_processed

def cluster_data():
    ## import section
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    import sklearn
    
    from sklearn.cluster import KMeans
    from sklearn import metrics
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score
    from sklearn.decomposition import PCA
    ## 

    

    def calculate_elbow(df_data_processed):
        sse = []
        k_list = range(1, 15)
        df_data_processed = df_data_processed.fillna(0)
        for k in k_list:
            km = KMeans(n_clusters=k)
            # print(df_data_processed.info())
            km.fit(df_data_processed)
            sse.append([k, km.inertia_])
            
        oca_results_scale = pd.DataFrame({'Cluster': range(1,15), 'SSE': sse})
        plt.figure(figsize=(12,6))
        plt.plot(pd.DataFrame(sse)[0], pd.DataFrame(sse)[1], marker='o')
        plt.title('Optimal Number of Clusters using Elbow Method (Scaled Data)')
        plt.xlabel('Number of clusters')
        plt.ylabel('Inertia')
        plt.show()
        for i in range(5,6):
            print(i)
            calculate_silhoutte_score(df_data_processed,i)
    
    def calculate_silhoutte_score(df_data_processed, num_clusters = 5):
        df_data_processed2 = df_data_processed.copy()
        # print(df_data_processed2.describe())
        kmeans_scale = KMeans(n_clusters=num_clusters, n_init=100, max_iter=400, init='k-means++', random_state=42).fit(df_data_processed2)
        print('KMeans Scaled Silhouette Score: {}'.format(silhouette_score(df_data_processed2, kmeans_scale.labels_, metric='euclidean')))
        labels_scale = kmeans_scale.labels_
        print('--------------------------------------')
        print(df_data_processed2.shape)
        print(df_data_grouped.shape)
        print(len(labels_scale))
        print('-------------------------------')
        df_data_grouped['target'] = labels_scale
        clusters_scale = pd.concat([df_data_processed2, pd.DataFrame({'cluster_scaled':labels_scale})], axis=1)
        draw_PCA(df_data_processed, labels_scale)

    def draw_PCA(df_data_processed, labels_scale):
        pca = PCA(n_components=len(df_data_processed.columns))
        pca.fit(df_data_processed)
        variance = pca.explained_variance_ratio_
        var = np.cumsum(np.round(variance, 3)*100)
        plt.figure(figsize=(12,6))
        plt.ylabel('% Variance Explained')
        plt.xlabel('# of Features')
        plt.title('PCA Analysis')
        plt.ylim(0,100.5)
        plt.plot(var)
        plt.show()
        
        pca2 = PCA(n_components=7).fit(df_data_processed)
        pca2d = pca2.transform(df_data_processed)
        plt.figure(figsize = (10,10))
        sns.scatterplot(pca2d[:,0], pca2d[:,1], 
                        hue=labels_scale, 
                        palette='Set1',
                        s=100, alpha=0.2).set_title('KMeans Clusters (4) Derived from Original Dataset', fontsize=15)
        plt.legend()
        plt.ylabel('PC2')
        plt.xlabel('PC1')
        plt.show()

   

    ## read data from file 
    df_data = pd.read_csv('../data/domain_resources_cluster.csv', header=0)
    
    # df_data = add_ssdeep_hash_column(df_data)

    # df_data.to_csv('../data/domain_resources_cluster.csv', index=False)
    # exit()    
   
    df_data_grouped , df_data_processed = prepare_and_scale_data(df_data)
    print(df_data_processed.shape)
    calculate_elbow(df_data_processed)
    df_data_grouped.to_csv('target_results.csv')

    # print(df_data_processed.head())


    


if __name__ == '__main__':

    
    df_resources = get_domain_request_relationship()
    # most_connected_phish = draw_domain_request_relationship(df_resources,0)
    # with open('../data/phish_top_request_domains.csv', 'w') as f:
    #     f.write('\n'.join(most_connected_phish))
    # most_connected_top = draw_domain_request_relationship(df_resources,1)
    # with open('../data/legit_top_request_domains.csv', 'w') as f:
    #     f.write('\n'.join(most_connected_top))
    
    draw_domain_request_relationship(df_resources)
    # cluster_data()
    



# G_asymmetric = nx.DiGraph()
# G_asymmetric.add_edge('A','B')
# G_asymmetric.add_edge('A','D')
# G_asymmetric.add_edge('C','A')
# G_asymmetric.add_edge('D','E')
# nx.spring_layout(G_asymmetric)
# nx.draw_networkx(G_asymmetric)



# sorted(betCent, key=betCent.get, reverse=True)[:5]

'''
def draw_domain_request_relationship():
    global domains, legitimate_nodes

    df_resources = get_domain_request_relationship()
    G_domains = nx.read_edgelist(data_file, create_using = nx.Graph(), nodetype=int)
    domain_names = {v:k for k,v in domains.items()}
    setA = [x for x in list(domain_names.keys()) if x < 100000]
    setB = [x for x in list(domain_names.keys()) if x > 100000]
    print([domain_names[x] for x in setA])
    G_domains.add_nodes_from(setA, bipartite = 0)
    G_domains.add_nodes_from(setB, bipartite = 1)

    S = [G_domains.subgraph(c).copy() for c in nx.connected_components(G_domains) ]
    print(len(S))
    graph_id = 0
    for sgraph in S:
        l, r = nx.bipartite.sets(sgraph)
        s_nodes = sgraph.nodes()
        sites = '#--#'.join(map(domain_names.get, l)).replace('.','_') 
        print(sites)
        top_nodes = [n for n in s_nodes if n in legitimate_nodes]
        print(top_nodes)
        # print(sgraph.edges())
        labelsdict = {}
        for node in s_nodes:
            labelsdict[node] = domain_names.get(node) 
        pos = {}
        pos.update((node, (1, index+10)) for index, node in enumerate(l))
        pos.update((node, (2, index+10)) for index, node in enumerate(r))
        print(pos)
        # nodes
        options = {"node_size": 80, "alpha": 0.5}
        nx.draw_networkx_nodes(sgraph, pos, nodelist=l, node_color="tab:red", **options)
        nx.draw_networkx_nodes(sgraph, pos, nodelist=r, node_color="tab:blue", **options)
        nx.draw_networkx_nodes(sgraph, pos, nodelist=l, node_color="tab:green", **options)
        nx.draw_networkx_labels(sgraph, pos, labels= labelsdict, font_size=6)
        nx.draw_networkx_edges(
            sgraph,
            pos,
            edgelist=sgraph.edges(),
            width=2,
            alpha=0.5,
            edge_color="tab:grey",
        )
        graph_id = graph_id+1
        # nx.draw(sgraph, pos= pos, labels = labelsdict, with_labels=True)

        # plt.show()
        plt.tight_layout()
        plt.savefig("../data/graph_plots/"+str(graph_id)+sites[:20]+".pdf")
        plt.clf()

    # l, r = nx.bipartite.sets(G_domains)
    pos = {}

    # Update position for node from each group
    pos.update((node, (1, index)) for index, node in enumerate(setA))
    pos.update((node, (2, index)) for index, node in enumerate(setB))

    nx.draw(G_domains, pos=pos, with_labels=True)
    plt.show()
     # l, r = nx.bipartite.sets(G_domains)
    # pos = {}

    # # Update position for node from each group
    # pos.update((node, (1, index)) for index, node in enumerate(setA))
    # pos.update((node, (2, index)) for index, node in enumerate(setB))

    # nx.draw(G_domains, pos=pos, with_labels=True)
    # plt.show()
    # pos = nx.spring_layout(G_domains)
    # betCent = nx.degree_centrality(G_domains)#, normalized=True, endpoints=True)
    # node_color = [20000.0 * G_domains.degree(v) for v in G_domains]
    # node_size =  [v * 10000 for v in betCent.values()]
    # plt.figure(figsize=(20,20))
    # nx.draw_networkx(G_domains, pos=pos, with_labels=False,
    #                  node_color=node_color,
    #                  node_size=node_size )
    # plt.axis('off')
    # plt.show()
    # most_connected = sorted(betCent, key=betCent.get, reverse=True)[:100]
    # degrees = nx.degree(G_domains)
    # print(degrees)
    # most_connected = sorted(degrees, key = lambda x: x[1], reverse = True)[:100]
    # print(most_connected)
    
    # print([(domain_names.get(x), nx.degree(G_domains, x)) for x in most_connected])
    # print([(domain_names.get(x), nx.degree(G_domains, x)) for (x,y) in most_connected])

'''
