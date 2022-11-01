import warnings
warnings.filterwarnings('ignore')

from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import pandas as pd
import numpy as np
import enchant 
from textblob import TextBlob
from nltk import everygrams

def token_cleaning(sentences):
    res_sentences=[]
    for sentence in sentences:
        
        sentence = sentence.lower()
        s=sentence   
        max=0

        d = enchant.request_pwl_dict("../PhishMeshCrawler/mywords.txt")  
        words = [''.join(_ngram) for _ngram in everygrams(sentence) if d.check(''.join(_ngram)) ]
        sentence = ' '.join(words)
        
        input_sent=TextBlob(sentence)

        sent=''    
        for w,pos in input_sent.tags:
            if  (pos=="NN" or pos =="JJ") :
                sent= sent +" " + w
        
        # print ('final sent: ' +sentence + ' '+sent)
        res_sentences.append(s.lower())
    return res_sentences

def plot_field_cloud():
    df_fields = pd.read_csv('../data/field_test_results_unknown.csv', encoding = 'utf-8') 
    df_fields = df_fields[df_fields['Predicted']=='unknown']
    df_fields = df_fields.dropna()
    df_fields_groups = df_fields.groupby(['field_category']).apply(lambda x: ' '.join(x['field_text'])
                        ).reset_index(name='field_text_samples')

    print(df_fields_groups.head())

    # fig, axes = plt.subplots( (df_fields_groups.shape[0]+1)//4, 4, figsize=(150,35), sharex=True, sharey=True)

    for i,ax in df_fields_groups.iterrows():
        try:
            # fig.add_subplot(ax)
            text_sample = df_fields_groups['field_text_samples'][i]            
            wordcloud_fields = WordCloud(background_color="white", max_words = 50, collocations = False, colormap = 'Dark2', max_font_size=200).generate(text_sample)

            plt.figure(figsize = (8,6))
            plt.imshow(wordcloud_fields, interpolation='bilinear')            
            # plt.title('Topic ::' +  df_fields_groups['field_category'][i], fontdict=dict(size=16))
            plt.axis("off")
            plt.margins(x=0,y=0)
            plt.tight_layout()
            plt.savefig('../data/paper_graphs/unknown_cloud.pdf')
            plt.show()
        except Exception as e:
            print(e)
            continue

    # plt.subplots_adjust(wspace=0, hspace=0)
    # plt.axis('off')
    # plt.margins(x=0,y=0)
    # plt.tight_layout()
    # plt.show()


plot_field_cloud()