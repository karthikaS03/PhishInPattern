import site
import sys
sys.path.append('/home/sk-lab/Desktop/PhishProDetector/PhishMeshCrawler/')
import pandas as pd
import numpy as np
import json
import os
from database import phish_db_layer
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from datetime import datetime
from collections import defaultdict, Counter
import ruptures as rpt
import seaborn as sn
import tldextract

class GraphPlots:
    def __init__(self,):
        self.show_plots = False
        self.legend_size = 12
        self.label_size = 14
    
    def _get_label_rotation(self, angle, offset):

        # Rotation must be specified in degrees 
        rotation = np.rad2deg(angle + offset)
        if angle <= np.pi:
            alignment = "right"
            rotation = rotation + 180
        else: 
            alignment = "left"
        return rotation, alignment

    def _add_labels(self, angles, values, labels, offset, ax):
    
        # This is the space between the end of the bar and the label
        padding = 1
        
        # Iterate over angles, values, and labels, to add all of them.
        for angle, value, label, in zip(angles, values, labels):
            angle = angle
            
            # Obtain text rotation and alignment
            rotation, alignment = self._get_label_rotation(angle, offset)

            # And finally add the text
            ax.text(
                x=angle, 
                y=value + padding, 
                s=label, 
                ha=alignment, 
                va="center", 
                fontsize = self.label_size,
                rotation=rotation, 
                rotation_mode="anchor"
            ) 

    def plot_circular_bar(self, df_data, file_name):
        
        plt.clf()
        VALUES = df_data["values"].values
        LABELS = df_data["labels"].values
        GROUP = df_data["group"].values
        
        df_groups = df_data.groupby("group", sort = False)["values"].count().reset_index()
        GROUP_LABELS = df_groups["group"].values
        GROUPS_SIZE = df_groups["values"].values
        
        PAD = 3
        ANGLES_N = len(VALUES) + PAD * len(np.unique(GROUP))

        ANGLES = np.linspace(0, 2 * np.pi, num=ANGLES_N, endpoint=False)
        WIDTH = (2 * np.pi) / len(ANGLES)

        offset = 0
        IDXS = []
        for size in GROUPS_SIZE:
            IDXS += list(range(offset + PAD, offset + size + PAD))
            offset += size + PAD

        fig, ax = plt.subplots(figsize=(8, 7), subplot_kw={"projection": "polar"})

        ax.set_theta_offset(offset)
        # ax.set_ylim(-100, 100)
        ax.set_frame_on(False)
        ax.xaxis.grid(False)
        ax.yaxis.grid(False)
        ax.set_xticks([])
        ax.set_yticks([])

        
        COLORS = [f"C{i}" for i, size in enumerate(GROUPS_SIZE) for _ in range(size)]

        ### Add bars for each value
        ax.bar(
            ANGLES[IDXS], VALUES, width=WIDTH, color=COLORS, 
            edgecolor="white", linewidth=2
        )

        ### Add labels to the bars
        self._add_labels(ANGLES[IDXS], VALUES, LABELS, offset, ax)

        offset = 0 
        legend_bars = []
        i = 0
        for group, size in zip(GROUP_LABELS, GROUPS_SIZE):
            # Add line below bars
            x1 = np.linspace(ANGLES[offset + PAD], ANGLES[offset + size + PAD - 1], num=5)
            ax.plot(x1, [-0.5]*5, color="#333333")
            
            # Add text to indicate group
            # ax.text(
            #     np.mean(x1)+0.04, 10, group, color="#333333", fontsize=14, 
            #     fontweight="bold", ha="right", va="top"
            # )

            legend_bars.append(Line2D([0], [0], color=COLORS[i], lw=3)) 
            i += size

            # # Add reference lines at 20, 40, 60, and 80
            x2 = np.linspace(ANGLES[offset], ANGLES[offset + PAD - 1], num=5)
            ax.plot(x2, [2] * 5, color="#bebebe", lw=0.8)
            ax.plot(x2, [6] * 5, color="#bebebe", lw=0.8)
            ax.plot(x2, [8] * 5, color="#bebebe", lw=0.8)
            ax.plot(x2, [10] * 5, color="#bebebe", lw=0.8)
            
            offset += size + PAD

        ax.legend(legend_bars, GROUP_LABELS, loc="lower left", ncol = 4, fontsize = self.legend_size)
        plt.rc('font', size=34)  
        plt.rc('axes', labelsize=34) 
        plt.rc('legend',fontsize=20) 
        plt.tight_layout()
        plt.savefig(file_name)

    def plot_donut(self, df_data,fig_name):

        plt.clf()

        # explosion
        explode = [0.03] * df_data.shape[0]
        df_data.plot.pie(y=0,legend=None, autopct='%1.1f%%', pctdistance=0.85, explode= explode, colormap = 'Dark2', fontsize=self.label_size) 
        
        # draw circle
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        fig = plt.gcf()
        # Adding Title of chart
        plt.title('')
        
        # Adding Circle in Pie chart
        fig.gca().add_artist(centre_circle)
        
        plt.tight_layout()
        plt.savefig(fig_name)

    def plot_correlation(self, df_data, fig_name):

        plt.clf()
        corr = df_data.corr()
        sn.heatmap(corr, annot= True)
        # plt.show()
        plt.tight_layout()        
        plt.savefig(fig_name)

    def plot_heatmap(self, df_data, fig_name):
        # print(df_data.index)
        plt.clf()
        plt.imshow(df_data, cmap='viridis')
        plt.colorbar()
        plt.xticks(range(len(df_data.columns)), df_data.columns, rotation =90)
        plt.yticks(range(len(df_data.index)), df_data.index)
        plt.tight_layout()        
        plt.savefig(fig_name)

       

    def plot_bar_subplots(self, df_data, fig_name ):
        
        plt.clf()
        axes = df_data.plot.bar(subplots=True,colormap = 'Blues', sharey=True, sharex=True)
        # print(ax)
        cols = df_data.columns

        plt.yscale('log')
        for c in range(len(cols)):
            axes[c].set_ylabel('Count')
            axes[c].set_yticks([10, 100, 1000])
            axes[c].set_title('')
            axes[c].legend(fontsize=6)
            axes[c].tick_params(axis = 'both', labelsize = 8)

        # for ax in axes:
        #     ax.tick_params(axis = 'both', labelsize = 8)
        plt.xlabel('Field Categories')
        # plt.rc('font', size=14)  
        # plt.rc('axes', labelsize=14) 
        # plt.xticks(fontsize=10, rotation=90)
        # plt.yticks(fontsize=8, rotation=0)
        # plt.rc('legend',fontsize=6) 
        # plt.rcParams['xtick.labelsize'] = 6
        # plt.rcParams['ytick.labelsize'] = 6
        plt.tight_layout()        
        plt.savefig(fig_name)


class PaperGraphs:

    def __init__(self,):
        self.results_dir = '../data/paper_graphs/'        
        self.graph = GraphPlots()

    def plot_fields_count(self, fields_file_path):
        try:
            df_data = pd.read_csv(fields_file_path,header=0)
            df_data['norm_count'] = np.log2(df_data['count'])        
            df_data.rename(columns={"norm_count": "values", "field": "labels", "group": "group"}, inplace=True)

            self.graph.plot_circular_bar(df_data,self.results_dir+'field_groups2.pdf')
        except Exception as e:
            print('Fields Count ::', e)

    def plot_submit_methods(self, submit_methods):
        try:
            dict_data = {k:[v] for k,v in submit_methods.items() if len(k)>2}
            df_data = pd.DataFrame.from_dict(dict_data, orient = 'index')
            self.graph.plot_donut(df_data,self.results_dir+'submit_methods.pdf')
        except Exception as e:
            print('Submit Methods :: ',e)

    def plot_parsed_methods(self, parsed_methods):
        try:
            dict_data = {k:[v] for k,v in parsed_methods.items() if len(k)>2}
            df_data = pd.DataFrame.from_dict(dict_data, orient = 'index')
            self.graph.plot_donut(df_data, self.results_dir+'parsed_methods.pdf')
        except Exception as e:
            print('Parsed Methods ::',e)

    def plot_multi_phishing_data(self, field_counts):
        try:
            df_fields = pd.DataFrame.from_dict(field_counts)

            max_pages = len(field_counts.keys())
            cols = []
            for i in range(max_pages,0,-1):
                cols.append('Page_'+str(i))
                if 'Page_'+str(i) not in df_fields.columns:
                    df_fields['Page_'+str(i)] =[np.nan] * df_fields.shape[0]
            df_fields = df_fields[cols]
            df_fields = df_fields.sort_values(by=['Page_1'], ascending=False)
            df_fields = df_fields.fillna(0)
            df_fields = df_fields.drop(df_fields.columns[df_fields.apply(lambda col: max(col)<=10)],axis=1)
            print(df_fields.head())
            self.graph.plot_heatmap(df_fields, self.results_dir+'multi_phishing_fields_count_heatmap.pdf')
            self.graph.plot_bar_subplots(df_fields, self.results_dir+'multi_phishing_fields_count.pdf')
            
        except Exception as e:
            print(e)

    def plot_nonmulti_phishing_data(self, field_counts):
        try:
            df_fields = pd.DataFrame.from_dict(field_counts)

            max_pages = len(field_counts.keys())
            cols = []
            for i in range(max_pages,0,-1):
                cols.append('Page_'+str(i))
                if 'Page_'+str(i) not in df_fields.columns:
                    df_fields['Page_'+str(i)] =[np.nan] * df_fields.shape[0]
            df_fields = df_fields[cols]
            df_fields = df_fields.sort_values(by=['Page_1'], ascending=False)
            df_fields = df_fields.fillna(0)
            df_fields = df_fields.drop(df_fields.columns[df_fields.apply(lambda col: max(col)<10)],axis=1)
            # print(df_fields.head())
            self.graph.plot_heatmap(df_fields, self.results_dir+'nonmulti_phishing_fields_count_heatmap.pdf')
            self.graph.plot_bar_subplots(df_fields, self.results_dir+'nonmulti_phishing_fields_count.pdf')
            
        except Exception as e:
            print(e)


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
    
    def parse_logs(self):
        try:
            containers_dir_path = '../PhishMeshController/phish_containers_data/'
            for record_date in os.listdir(containers_dir_path):
                if 'container' in record_date:
                    continue
                containers_dir_path2 = containers_dir_path+ record_date + '/'
                print(containers_dir_path2)
                for d in os.listdir(containers_dir_path2):
                    # print(d)
                    logs_dir = os.path.join(containers_dir_path2,d,'data/logs/')
                    for f in os.listdir(logs_dir):
                        if 'event' in f:
                            with open(logs_dir+f,'r') as logf:
                                for line in logf:

                                    ### find if the line contains the method used to submit the data successfully
                                    ind = line.find('Successfully submitted via ')
                                    if ind > 0:                                
                                        method = line.split(' ')[-2]
                                        self.submit_methods[method] = self.submit_methods.get(method,0) + 1

                                    ### find if the line contains the method used to identify HTML element
                                    ind2 = line.find('Valid Category')
                                    if ind2 > 0:                                
                                        parsed_method = line[line.find('Parsed Method'):].split(':')[-1]
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
        except Exception as e:
            print(e)

    def _record_field_count(self, row):
        # print(row)
        site_fields = row['site_elements'].split(' && ')
        page_counts = row['page_no'].split(' && ')
        dom_hashes = row['dom_hashes'].split(' && ')
        dom_hash_count = Counter(dom_hashes)
        seen_dom_hashes = set()
        repeated_pages_count = 0

        for page_no, page_fields,dom_hash in zip(page_counts,site_fields,dom_hashes):
            ### If a page is repeated more than twice, then it is not a double login, so ingore the repeated pages
            if dom_hash_count[dom_hash]>2 and dom_hash in seen_dom_hashes:                    
                    repeated_pages_count += 1                    
                    continue
            page_no = int(page_no) - repeated_pages_count
            

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

    def parse_multi_phishing_data(self):

        multi_results = phish_db_layer.fetch_multi_phishing_data()
        df_multi_data = pd.DataFrame(multi_results , columns = ['site_id','page_count','title_count','dom_hash_count','elements_count','url_count','site_elements','titles','elem_names','images','page_no', 'page_domains','dom_hashes'])
        self.fields_count_page = defaultdict(dict)
        df_multi_data['sld_domains'] = df_multi_data['page_domains'].apply(lambda x: self._get_SLDs(x))
        df_multi_data[['site_elements','page_no','dom_hashes']].apply(lambda x: self._record_field_count(x), axis =1)
        df_multi_data['has_double_login'] = df_multi_data[['titles','elem_names','dom_hashes']].apply(lambda x: self._has_double_login(x), axis = 1)
        df_multi_data['has_click_through'] = df_multi_data[['site_elements','page_no','dom_hashes']].apply(lambda x: self._has_click_through(x), axis = 1)
        df_multi_data['has_termination_message'] = df_multi_data[['site_elements','page_no','dom_hashes','sld_domains']].apply(lambda x: self._has_termination_message(x), axis = 1)
        df_multi_data['has_end_domain_changed'] = df_multi_data['sld_domains'].apply(lambda x: x.split(' && ')[0] != x.split(' && ')[-1])

        df_multi_data.to_csv('../data/multi_phishing_data.csv', index = False)

        print(df_multi_data.describe() )

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

        print(df_multi_data.describe())

    def plot_graphs(self):

        fields_file_path = '../data/fields_groups_count.csv'
        self.graphs.plot_fields_count(fields_file_path)
    
        self.parse_logs()
        self.graphs.plot_submit_methods(self.submit_methods)
        self.graphs.plot_parsed_methods(self.parsed_methods)
        # print(self.captchas)
        print({k:len(v) for k,v in self.captchas.items()})
        self.parse_multi_phishing_data()
        self.graphs.plot_multi_phishing_data(self.fields_count_page)

        self.parse_nonmulti_phishing_data()
        self.graphs.plot_nonmulti_phishing_data(self.fields_count_page)
        print(self.fields_count_all)



if __name__ == '__main__':

    analyzer_obj = DataAnalyzer()
    analyzer_obj.plot_graphs()





def segment_events(event_deltas):
    if len(event_deltas)>1:
        signal = np.array([[x] for x in event_deltas])
        print(signal.shape)
        algo = rpt.Pelt(model="rbf",jump=1).fit(signal)
        result = algo.predict(pen=0.5)        
        rpt.display(signal, result, result)
        plt.savefig('pelt.pdf')
        return result[:-1]
    return [0]

def get_all_events():
    event_keywords = ['Crawling Started', 'Navigated to', 'handle_request', 'Submitting via', 'Providing input', 'Browser Closed']

    containers_dir_path = '../PhishMeshController/phish_containers_data/20220228/phish_containers_data/'
    
    for d in os.listdir(containers_dir_path):
        logs_dir = os.path.join(containers_dir_path,d,'data/logs/')
        # if '2022_215' not in d:
        #     continue
        for f in os.listdir(logs_dir):
            events = []
            id = 0
            prev_time = None
            if 'event' in f:
                with open(logs_dir+f,'r') as logf:
                    for line in logf:
                        
                        for kword in event_keywords:
                            if kword in line:
                                
                                ev_time = datetime.strptime(line.split(' -')[0],'%Y-%m-%d %H:%M:%S,%f')
                                event = { 'id': id,
                                                'event_time' : line.split(' -')[0], 
                                                'time_delta' : (ev_time - (prev_time if prev_time else ev_time) ).total_seconds(),
                                                'event' : kword, 
                                                'text' : line}
                                
                                events.append(event)
                                id += 1
                                prev_time = ev_time
                
                print(len(events))
                seg_res = segment_events([e['time_delta'] for e in events  ])
                seg_res = [0]+ seg_res + [len(events)]

                for i in range(1, len(seg_res)):
                    ev_seg = []
                    ev_seg = ' -||- '.join([ str(ev['id'])+'_'+ev['event'] for ev in events[seg_res[i-1]: seg_res[i]]])
                    if 'Providing' in ev_seg or 'Submitting' in ev_seg:
                        print(d, ev_seg)

                # print(seg_res)
                with open('../data/events/'+d+'_events.json','w') as fj:
                    json.dump(events, fj, indent = 2)

# get_all_events()

# parse_logs()
# plot_circular_bar()

# plot_pagewise_fields()



'''
def get_label_rotation(angle, offset):
    # Rotation must be specified in degrees :(
    rotation = np.rad2deg(angle + offset)
    if angle <= np.pi:
        alignment = "right"
        rotation = rotation + 180
    else: 
        alignment = "left"
    return rotation, alignment
def add_labels(angles, values, labels, offset, ax):
    
    # This is the space between the end of the bar and the label
    padding = 1
    
    # Iterate over angles, values, and labels, to add all of them.
    for angle, value, label, in zip(angles, values, labels):
        angle = angle
        
        # Obtain text rotation and alignment
        rotation, alignment = get_label_rotation(angle, offset)
        # And finally add the text
        ax.text(
            x=angle, 
            y=value + padding, 
            s=label, 
            ha=alignment, 
            va="center", 
            fontsize = 16,
            rotation=rotation, 
            rotation_mode="anchor"
        ) 
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
'''