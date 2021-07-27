#!/usr/bin/python
# coding=utf8

import sys


from textblob import Word
from textblob.classifiers import NaiveBayesClassifier
from textblob import TextBlob
import difflib
import json
import nltk
nltk.download('averaged_perceptron_tagger')
nltk.download('punkt')
import collections
from nltk.classify.scikitlearn import SklearnClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from faker import Faker
import pickle
from database import phish_db_layer
from database import phish_db_schema
import os
import pandas as pd
from nltk import everygrams
import enchant
from sklearn import metrics
import numpy as np
import random
from sklearn.naive_bayes import GaussianNB
dir_path = os.path.abspath(os.path.dirname(__file__))

samples=[]



def token_cleaning(sentence):
    res_sentences=[]
    sentence = sentence.lower()
    s=sentence   
    max=0
    # print ('sent : ',sentence)
    d = enchant.request_pwl_dict(dir_path+"/mywords.txt")
    # for ng in everygrams(sentence):
    #     print(ng)
    #     print(d.check(''.join(ng)))
    words = [''.join(_ngram) for _ngram in everygrams(sentence) if d.check(''.join(_ngram)) ]
    sentence = ' '.join(words)
    # print(sentence)
    input_sent=TextBlob(sentence)
    sent=''
    # print (input_sent.tags)
    for w,pos in input_sent.tags:
        if  (pos=="NN" or pos =="JJ") :
            sent= sent +" " + w
    
    # print ('final sent: ' +sentence + ' '+sent)
    res_sentences.append(((sentence + ' '+sent).lower()+' ')*10)
    return res_sentences

def fetch_field_training_set():

    training_set = []
    with open('./database/TrainingSet.json','r') as f:
        
        train =json.load(f)
        for obj in train:            
            for text in obj['texts']:
                data={}
                data['category'] = obj['category']
                data['text'] = text
                training_set.append(data)

    return training_set 

def pickle_data():
    global samples
    t_set = fetch_field_training_set()#phish_db_layer.fetch_field_training_set()
    random.shuffle(t_set)
    samples = list(set([e['category']for e in t_set]))
    samples.sort()
    train_set = [{'cat': e['category'] , 'text': token_cleaning(e['text'])[0] }for (e) in t_set]
    train_data = pd.DataFrame(train_set, columns=['cat', 'text'])
    train_data['cat_num'] = train_data.cat.map({c: i for i,c in enumerate(samples)})
    #print train_data.head()
    X = train_data.text
    Y = train_data.cat_num
    test_set =[{'cat': e['category'] , 'text': token_cleaning(e['text'])[0] }for (e) in t_set][300:]
    test_data = pd.DataFrame(test_set, columns=['cat', 'text'])
    test_data['cat_num'] = test_data.cat.map({c: i for i,c in enumerate(samples)})
    X_test = test_data.text
    Y_test = test_data.cat_num
    '''
    vect = CountVectorizer()
    X_train_dtm = vect.fit_transform(X)
    tf_transformer = TfidfTransformer(use_idf=False)
    X_train_tf = tf_transformer.fit_transform((X_train_dtm)
    nb = MultinomialNB()
    nb.fit(X_train_tfidf,Y)
    ('clf', MultinomialNB()),
    ('vect', CountVectorizer()),
    ('clf', SGDClassifier(loss='log', penalty='l2',alpha=1e-3, random_state=42)),
    '''
    nb = Pipeline([
    
     ('vect', CountVectorizer()),
     ('clf', SGDClassifier(loss='log', penalty='l2',alpha=1e-3, random_state=42, max_iter=5, tol=None)),
    ])
    nb.fit(X, Y)
    #y_pred = nb.predict(X_test)
    #print np.mean(y_pred == Y_test)
    #print(metrics.classification_report(Y_test, y_pred,target_names=samples))
    cl_pickle = open(os.path.join(dir_path,"category.pickle"),"wb")
    pickle.dump(nb,cl_pickle)
    cl_pickle.close()
    
    
# Classify some text
def classify(text):
    # print ('_________________START____________________')
    #print text
    global samples
    if len(text)<2:
        return "", 0
    t_set = set([t['category'] for t in fetch_field_training_set()]) #phish_db_layer.get_categories()
    samples =[e for e in t_set]
    samples.sort()
    # print(samples)
    cl_pickle = open(os.path.join(dir_path,"category.pickle"),"rb")
    nb = pickle.load(cl_pickle)
    cl_pickle.close()

    # print(text)
    text=  text.encode('ascii','ignore').decode() # text.decode('unicode_escape').encode('ascii','ignore')

    X_test = token_cleaning(text)

    y_pred = nb.predict(X_test)
    # print( y_pred)
    y_pred_prob = nb.predict_proba(X_test)[:,y_pred]
    # print (samples)
    result = samples[y_pred[0]]

    if result.lower() in X_test[0].lower():

        return result, y_pred_prob[0]

    elif y_pred_prob[0]*100 <80:
        # print ("low probability")
        return "", 0
	

    #print metrics.confusion_matrix(Y, y_pred)
    return result, y_pred_prob[0]


def get_category_input_value(category):
    # print(category)
    fake = Faker()
    # Faker.seed(0)
    choice ={'address' : fake.address(),
    		'name'    : fake.name(),
    		'username': fake.simple_profile(sex=None).get("username"),
    		'password': fake.password(), #fake.word()+'@'+str(fake.random_number(digits=3)),
            'identification': fake.email(),
    		'email'   : fake.email(),
            'phone'   : str(fake.random_number(digits=10)),
            'month'   : fake.month(),
            'date'    : str(fake.simple_profile(sex=None).get("birthdate")),
            'year'    : fake.year(),
            'day'     : fake.day_of_month(),
    		'card'    : fake.credit_card_number(card_type=None),
    		'cvv'     : fake.credit_card_security_code(card_type=None),
    		'expdate' : fake.credit_card_expire(),#start="now", end="+10Y", date_format="%m%y"),
    		'ssn'     : fake.ssn(),
            'zip'     : fake.zipcode(),
            'city'    : fake.city(),
            'state'   : fake.state(),
            'license' : fake.ssn(),
            'search'  : ''
    }    
    return choice.get(category.lower(),"default");

# classify('email')
if __name__ == '__main__':
    pickle_data()