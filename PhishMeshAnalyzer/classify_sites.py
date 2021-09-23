import pandas as pd
import numpy as np 
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import precision_score

def prepare_and_scale_data(df_data):
    ## import section
    from sklearn.preprocessing import StandardScaler
    ##

    ## Preprocess data
    drop_columns = ['site_id','site_url','page_url','resource_url','page_elements','res_file_hash','res_file_path','is_top_site','site_domain',
                    'res_domain','has_critical_input', 'cluster_component']#,'ssdeep_hashes', 'ssdeep_clusters']
    feature_columns = ['page_count','page_unique_req_count','critical_page_count','third_party_unique_req_count']
    
    ## group pages information per site to get per site information
    df_data_grouped = df_data.groupby(['site_id']).first().reset_index()
    df_data_processed = df_data_grouped.drop(drop_columns,axis=1)

    # convert categorical data to one-hot encoding
    df_clusters = pd.get_dummies(df_data_grouped['cluster_component'], prefix='cluster')
    # df_ssdeep_clusters = pd.get_dummies(df_data_grouped['ssdeep_clusters'], prefix='SDC')
        
    ## Scale dataset
    scaler = StandardScaler()
    scaler.fit(df_data_processed)
    X_scale = scaler.transform(df_data_processed)
    df_scale = pd.DataFrame(X_scale, columns=df_data_processed.columns)
    df_data_processed = pd.concat([df_scale, df_clusters],axis=1)
    # df_data_processed = pd.concat([df_data_processed, df_ssdeep_clusters])

    return df_data_grouped ,df_data_processed

def semi_supervised_classifier(df_data):
    ## import section
    from numpy import concatenate
    from sklearn.semi_supervised import LabelPropagation
    ##

    df_data_grouped, df_data_processed = prepare_and_scale_data(df_data)
    df_data_processed['is_top_site'] = df_data_grouped['is_top_site']
    X_train, X_test, y_train, y_test = train_test_split(df_data_processed.drop('is_top_site', axis=1), 
                                        df_data_processed['is_top_site'], test_size=0.25, stratify=df_data_processed['is_top_site'], random_state=123456)
    X_train_lab, X_test_unlab, y_train_lab, y_test_unlab = train_test_split(X_train, y_train, test_size=0.50, random_state=1, stratify=y_train)
    
    # summarize training set size

    print('======================Semi-Supervised Classifier========================')
    print('Labeled Train Set:', X_train_lab.shape, y_train_lab.shape)
    print('Unlabeled Train Set:', X_test_unlab.shape, y_test_unlab.shape)
    # summarize test set size
    print('Test Set:', X_test.shape, y_test.shape)
    

    X_train_mixed = concatenate((X_train_lab, X_test_unlab))
    nolabel = [-1 for _ in range(len(y_test_unlab))]
    # recombine training dataset labels
    y_train_mixed = concatenate((y_train_lab, nolabel))
    # define model
    model = LabelPropagation()
    # fit model on training dataset
    model.fit(X_train_mixed, y_train_mixed)
    # make predictions on hold out test set
    yhat = model.predict(X_test)
    # calculate score for test set
    score = accuracy_score(y_test, yhat)
    # summarize score
    print('Accuracy: %.3f' % (score*100))
    print('=========================================================================')

def XGB_Classifier(df_data):

    import xgboost as xgb

    df_data_grouped , df_data_processed = prepare_and_scale_data(df_data)
    df_data_processed['is_top_site'] = df_data_grouped['is_top_site']

    X_train, X_test, y_train, y_test = train_test_split(df_data_processed.drop('is_top_site', axis=1), 
                                        df_data_processed['is_top_site'], test_size=0.5, stratify=df_data_processed['is_top_site'], random_state=123456)

    param = {
        'max_depth': 10,  # the maximum depth of each tree
        'eta': 0.7,  # the training step for each iteration
        'silent': 1,  # logging mode - quiet
        'objective': 'multi:softprob',  # error evaluation for multiclass training
        'num_class': 2}  # the number of classes that exist in this datset
    num_round = 20  # the number of training iterations

    print('======================XGB Classifier========================')

    # use DMatrix for xgbosot
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)

    #------------- numpy array ------------------
    # training and testing - numpy matrices
    bst = xgb.train(param, dtrain, num_round)
    preds = bst.predict(dtest)

    # extracting most confident predictions
    best_preds = np.asarray([np.argmax(line) for line in preds])
    print( "Numpy array precision:", precision_score(y_test, best_preds, average='macro'))

    # dump the models
    bst.dump_model('dump.raw.txt')
    print('=========================================================================')

def RF_classifier(df_data):
    
    from sklearn.ensemble import RandomForestClassifier

    df_data_grouped , df_data_processed = prepare_and_scale_data(df_data)
    df_data_processed['is_top_site'] = df_data_grouped['is_top_site']

    # sns.pairplot(df_data_processed,hue ='is_top_site')
    # plt.show() 

    X_train, X_test, y_train, y_test = train_test_split(df_data_processed.drop('is_top_site', axis=1), 
                                        df_data_processed['is_top_site'], test_size=0.5, stratify=df_data_processed['is_top_site'], random_state=123456)

    print('======================Random Forest Classifier========================')
    rf = RandomForestClassifier(n_estimators=100, oob_score=True, random_state=123456)
    rf.fit(X_train, y_train)
    predicted = rf.predict(X_test)
    accuracy = accuracy_score(y_test, predicted)
    print(f'Mean accuracy score: {accuracy:.3}')
    # print(f'Out-of-bag score estimate: {rf.oob_score_:.3}')
    print('=========================================================================')

    def plot_feature_importance():
        
        importances = rf.feature_importances_
        std = np.std([
            tree.feature_importances_ for tree in rf.estimators_], axis=0)
        # print(importances)
        forest_importances = pd.Series(importances, index=X_train.columns)
        # print(forest_importances)
        # forest_importances = forest_importances.drop([x for x in X_train.columns if 'cluster'  in x or 'SDC'  in x])
        # print(forest_importances)
        fig, ax = plt.subplots()
        forest_importances.plot.bar(yerr=std, ax=ax)
        ax.set_title("Feature importances using MDI")
        ax.set_ylabel("Mean decrease in impurity")
        fig.tight_layout()
        plt.show()

    plot_feature_importance()
    # cm = pd.DataFrame(confusion_matrix(y_test, predicted), columns=[0,1] ,
    #                                  index=[0,1] )
    # sns.heatmap(cm, annot=True, fmt='d')
    # plt.show()

def classify_sites():

    ## read data from file 
    df_data = pd.read_csv('../data/domain_resources_cluster.csv', header=0)
    RF_classifier(df_data)
    # XGB_Classifier(df_data)
    semi_supervised_classifier(df_data)



if __name__ =='__main__':
    classify_sites()