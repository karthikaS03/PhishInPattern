import site
import sys
sys.path.append('/data/Karthika/PhishMesh-karthika-dev/PhishMeshCrawler/')
import pandas as pd
import numpy as np
import json
import os
import glob

from database import phish_db_layer
from plot_graphs_modules import PaperGraphs


from datetime import datetime
from collections import defaultdict, Counter
import ruptures as rpt
import seaborn as sn
import tldextract
import nltk
nltk.download('stopwords')
nltk.download('vader_lexicon')
from nltk.sentiment import SentimentIntensityAnalyzer
from googletrans import Translator
from bs4 import BeautifulSoup


class DataAnalyzer:
    def __init__(self):
        self.submit_methods = {}
        self.parsed_methods = {}
        self.captchas = defaultdict(set)
        self.fields_count_page = defaultdict(dict)
        self.fields_count_all = {}
        self.double_login_dom_hashes = []
        self.double_login_fields = set()
        self.graphs = PaperGraphs()
        self.domain_extract = tldextract.TLDExtract(include_psl_private_domains=True)
        self.submit_methods2 = {}
        self.containers_dir_path = '/data/Karthika/phish_final_data/'
        self.STOPWORDS = nltk.corpus.stopwords.words("english")
        self.NoInpVocab = Counter()
        self.SENTI_LEXICON = {}
    
    def parse_logs(self):
        try:
            containers_dir_path = self.containers_dir_path
            
            for record_date in os.listdir(containers_dir_path):
                if 'container' in record_date:
                    continue
                containers_dir_path2 = containers_dir_path+ record_date + '/'
                print(containers_dir_path2)
                for d in os.listdir(containers_dir_path2):
                    # print(d)
                    try:
                        logs_dir = os.path.join(containers_dir_path2,d,'data/logs/')
                        for f in os.listdir(logs_dir):
                            if 'event' in f:
                                submitted_methods = []
                                page_count = 1
                                with open(logs_dir+f,'r') as logf:
                                    for line in logf:

                                        ### find if the line contains the method used to submit the data successfully
                                        ind = line.find('Successfully submitted via ')
                                        if ind > 0:                                
                                            method = line.split(' ')[-2]
                                            self.submit_methods[method] = self.submit_methods.get(method,0) + 1
                                        
                                        ind = line.find('Page Details ')
                                        if ind > 0:                                
                                            page_details = line.split('::')[2]
                                            try:
                                                curr_page_count = int(page_details.split(',')[0].split(':')[-1])
                                                if curr_page_count != page_count:
                                                    if submitted_methods:
                                                        self.submit_methods2[submitted_methods[-1]] = self.submit_methods2.get(submitted_methods[-1],0) + 1
                                                    submitted_methods = []
                                                    page_count = curr_page_count
                                                
                                            except Exception as pe:
                                                print(page_details)
                                                print('Page details exception ::',pe)
                                                                                
                                        ind = line.find('Submitting via ')
                                        if ind > 0:                        
                                            method = line.split(' ')[-2]  
                                            method = method.replace('(','').replace(')','')                                        
                                            submitted_methods.append(method)


                                        ### find if the line contains the method used to identify HTML element
                                        ind2 = line.find('Valid Category')
                                        if ind2 > 0:                                
                                            parsed_method = line[line.find('Parsed Method'):].split(':')
                                            
                                            if len(parsed_method)>0:
                                                parsed_method = parsed_method[-1]
                                                if parsed_method in ['Element Name\n', 'Element Id\n', 'placeholder\n']:
                                                    parsed_method = 'HTML Data'
                                                elif 'OCR' in parsed_method:
                                                    parsed_method = 'OCR'
                                                elif 'InnerText' in parsed_method:
                                                    parsed_method = 'Other HTML'
                                                self.parsed_methods[parsed_method] = self.parsed_methods.get(parsed_method,0) + 1
                                    
                                        captcha_ind = line.find('Known Captcha')
                                        if captcha_ind > 0:                                        
                                            self.captchas['Known Captcha'].add(d)
                                        elif line.find('Captcha') > 0 and line.find('Clicked')>0 and d not in self.captchas['Known Captcha']:
                                            captcha_type = [w for w in line.split(' ') if 'Captcha' in w][0]
                                            self.captchas[captcha_type].add(d)
                                    if submitted_methods:
                                        self.submit_methods2[submitted_methods[-1]] = self.submit_methods2.get(submitted_methods[-1],0) + 1
                    except Exception as ce:
                        print(ce)
                        break
        except Exception as e:
            print(e)

    def _record_field_count(self, row):
        # print(row)
        sld_domains = row['sld_domains'].split(' && ')
        site_fields = row['site_elements'].split(' && ')
        page_counts = row['page_no'].split(' && ')
        dom_hashes = row['dom_hashes'].split(' && ')
        dom_hash_count = Counter(dom_hashes)
        seen_dom_hashes = set()
        repeated_pages_count = 0
        prev_dom_hash = None
        
        for page_no, page_fields,dom_hash,sld in zip(page_counts,site_fields,dom_hashes,sld_domains):
            ### If a page is repeated more than twice, then it is not a double login, so ingore the repeated pages
            if  sld != sld_domains[0] or (int(page_no)>1 and dom_hash == dom_hashes[0] and dom_hash != prev_dom_hash):
                break
            prev_dom_hash = dom_hash
            if dom_hash_count[dom_hash]>2 and dom_hash in seen_dom_hashes:                    
                    repeated_pages_count += 1                    
                    continue
            page_no = int(page_no) - repeated_pages_count
            
            if int(page_no) > 5:
                print(page_no+1, site_fields, sld_domains, dom_hashes,'\n')            

            ### Record field only for unique pages including double logins
            for f in page_fields.split('--'):
                if 'Unkno' in f:
                    f = 'Other'
                f = f.replace(' ','')                
                seen_dom_hashes.add(dom_hash)                
                p_num = 'Page_'+str(page_no+1)
                self.fields_count_page[p_num][f] = self.fields_count_page[p_num].get(f,0)+1
                self.fields_count_all[f] = self.fields_count_all.get(f,0)+1
                
    def _get_SLDs(self,page_urls):
        
        page_domains = []
        for url in page_urls.split(' && '):
            ext = self.domain_extract(url)
            page_domains.append(ext.domain+'.'+ ext.suffix)
        
        return  ' && '.join(page_domains)

    def _has_double_login(self, row):
        
        page_titles = row['titles'].split(' && ')
        dom_hashes = row['dom_hashes'].split(' && ')
        dom_elems = row['elem_names'].split(' && ')
        elems_count = Counter(dom_elems)
        titles_count = Counter(page_titles)
        double_logins = []
        dom_hash_index = defaultdict(list)

        for idx, dom_hash in enumerate(dom_hashes):
            dom_hash_index[dom_hash].append(idx)
        
        ### Check if dom_hash count is 2 and the respective title count is 2 and it is not the last page
        for dom_hash,idxs in dom_hash_index.items():
            if len(idxs) == 2:
                if int(idxs[1]) - int(idxs[0]) == 1 and dom_hashes[-1] != dom_hash and elems_count[dom_elems[idxs[0]]] == 2:
                    double_logins.append(dom_hash)
        
        self.double_login_dom_hashes = self.double_login_dom_hashes + double_logins

        return len(double_logins)>0

    def _has_click_through(self, row):
        
        
        dom_hashes = row['dom_hashes'].split(' && ')        
        site_fields = row['site_elements'].split(' && ')
        click_through = False

        ### TODO: Ensure noinp appears before any information is requested not after. 
        ### First, check if there are more pages that request input other than the click-through page
        if len(set(site_fields))> 1:
            ind = 0
            for  page_fields,dom_hash in zip(site_fields, dom_hashes):
                ### Check if the page is a click-through page and that it isn't the last page and that noinp appears before any information is requested not after. 
                if page_fields.replace('NoInp','') == '' and dom_hash != dom_hashes[-1] and len(set(site_fields[ind:]))>1:
                    click_through = True
                    # print(page_no, site_fields, dom_hashes)
                    break
                ind += 1

        return click_through



    def _has_termination_message(self, row):        
        site_fields = row['site_elements'].split(' && ')        
        return site_fields[-1] == 'NoInp' and len(set(site_fields))>1
    
        
    def _get_text_sentiment(page_text):    
        
        #print(page_words)
        sia = SentimentIntensityAnalyzer()
        polarity_scores = sia.polarity_scores(" ".join(page_words))
        return 'pos' if polarity_scores['compound']>=0 else 'neg'
    
    def _get_word_sentiment(self, page_word):
        
        if not self.SENTI_LEXICON:
            with open('senti_lexicon.json','r') as f:
                self.SENTI_LEXICON = json.load(f)
        
        return self.SENTI_LEXICON.get(page_word,None) 
    
    def _parse_html_file(self, file_path):
        text_content = ''
        res_text = ''        
        try:
            with open(file_path) as fp:
                soup = BeautifulSoup(fp,"html.parser")
                text_content = soup.get_text().replace('\n',' ')                
            
                #translator = Translator()
                #res = translator.translate(text_content)
                #res_text = res.text
                res_text = text_content
        except Exception as e:
            print(e)
            res_text = text_content
        return res_text
    
        
    def _process_non_input_page(self, page_name):
        try:
            for file_path in glob.glob(self.containers_dir_path+'**/'+page_name,recursive = True):
                print(file_path)
                html_text = self._parse_html_file(file_path)
                page_words = [w.lower() for w in html_text.split(' ') if w.lower() not in self.STOPWORDS and len(w)>1]
                if not os.path.exists('../data/NonInputContents/'+page_name):
                    with open('../data/NonInputContents/'+page_name,'w') as f:
                        f.write(' '.join(page_words))
                #self.NoInpVocab.update(page_words)
        except:
            pass
    
    def _get_non_input_pages(self,row):
        try:
            site_fields = row['site_elements'].split(' && ')
            site_images = row['images'].split(' && ')  
            for pno, page_fields in enumerate(site_fields):
                if page_fields == 'NoInp':
                    image_name = site_images[pno].split('_')
                    page_name = '_'.join(image_name[:3])+'_page_'+ image_name[3]+'.html'
                    self._process_non_input_page(page_name)
        except:
            pass
        
    def parse_multi_phishing_data(self):

        multi_results = phish_db_layer.fetch_multi_phishing_data()
        df_multi_data = pd.DataFrame(multi_results , columns = ['site_id','page_count','title_count','dom_hash_count','elements_count','url_count','site_elements','titles','elem_names','images','page_no', 'page_domains','dom_hashes'])
        self.fields_count_page = defaultdict(dict)
        df_multi_data['sld_domains'] = df_multi_data['page_domains'].apply(lambda x: self._get_SLDs(x))
        #df_campaigns = df_multi_data.groupby(['site_])
        df_campaigns = df_multi_data.groupby(['site_elements','page_no','dom_hashes','sld_domains'])[['site_elements','page_no','dom_hashes']].apply(lambda x : list(np.unique(x)))       
        df_campaigns.to_csv('../data/unique_campaigns.csv')
        df_campaigns.reset_index().apply(lambda x: self._record_field_count(x), axis =1)
        #df_multi_data[['site_elements','images']].apply(lambda x: self._get_non_input_pages(x), axis =1)
        df_multi_data['has_double_login'] = df_multi_data[['titles','elem_names','dom_hashes']].apply(lambda x: self._has_double_login(x), axis = 1)
        df_multi_data['has_click_through'] = df_multi_data[['site_elements','page_no','dom_hashes']].apply(lambda x: self._has_click_through(x), axis = 1)
        df_multi_data['has_termination_message'] = df_multi_data[['site_elements','page_no','dom_hashes','sld_domains']].apply(lambda x: self._has_termination_message(x), axis = 1)
        df_multi_data['has_end_domain_changed'] = df_multi_data['sld_domains'].apply(lambda x: x.split(' && ')[0] != x.split(' && ')[-1])

        df_multi_data.to_csv('../data/multi_phishing_data.csv', index = False)

        print(df_multi_data.info() )

        print('\n\n Count of Double Login ::', df_multi_data[df_multi_data['has_double_login'] == True]['has_double_login'].count())
        print('Count of Click Through ::', df_multi_data[df_multi_data['has_click_through'] == True]['has_click_through'].count())
        print('Count of Termination Patterns ::', df_multi_data[df_multi_data['has_termination_message'] == True]['has_termination_message'].count())
        print('Count of Termination and Domain Navigations ::', df_multi_data[(df_multi_data['has_end_domain_changed'] == True) & (df_multi_data['has_termination_message'] == True) ]['has_end_domain_changed'].count())
        print('Count of Domain Navigations ::', df_multi_data[df_multi_data['has_end_domain_changed'] == True]['has_end_domain_changed'].count())
        

    def parse_nonmulti_phishing_data(self):

        nonmulti_results = phish_db_layer.fetch_nonmulti_phishing_data()
        df_multi_data = pd.DataFrame(nonmulti_results , columns = ['site_id','page_count','title_count','dom_hash_count','elements_count','url_count','site_elements','titles','elem_names','images','page_no', 'page_domains','dom_hashes'])
        self.fields_count_page = defaultdict(dict)
        df_multi_data['sld_domains'] = df_multi_data['page_domains'].apply(lambda x: self._get_SLDs(x))
        df_multi_data[['site_elements','page_no','dom_hashes']].apply(lambda x: self._record_field_count(x), axis =1)

    def plot_graphs(self):
        
        fields_file_path = '../data/fields_groups_count.csv'
        self.graphs.plot_fields_count(fields_file_path)
        
        self.parse_logs()
        
        self.graphs.plot_submit_methods(self.submit_methods2)
        self.graphs.plot_parsed_methods(self.parsed_methods)
        '''
        
        self.parse_multi_phishing_data()
        
        print(self.NoInpVocab.most_common(50))
        for word in self.NoInpVocab:
            print(word, self._get_word_sentiment(word))
            
        
        
        self.graphs.plot_multi_phishing_data(self.fields_count_page)
        
        self.parse_nonmulti_phishing_data()
        self.graphs.plot_nonmulti_phishing_data(self.fields_count_page)
        '''


if __name__ == '__main__':

    analyzer_obj = DataAnalyzer()
    analyzer_obj.plot_graphs()
