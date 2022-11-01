import pandas as pd


file_path = '../data/domain_resources_cluster.csv'

def generate_report():
    df_data_processed = pd.read_csv(file_path, header=0)

    df_legit = df_data_processed[df_data_processed['is_top_site']==1]
    df_phish = df_data_processed[df_data_processed['is_top_site']==0]
    # df_palo = df_data_processed[df_data_processed['']]

    print('==========Legitimate Site Data=================')
    print(df_legit.describe())
    print('===============================================')


    print('==========Phishing Site Data==================')
    print(df_phish.describe())
    print('===============================================')   


    # print('==========Phishing Site (Palo) Data=================')
    # print(df_palo.describe())
    # print('===============================================') 

generate_report()