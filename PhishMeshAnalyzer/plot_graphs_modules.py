import site
import sys
sys.path.append('/data/Karthika/PhishMesh-karthika-dev/PhishMeshCrawler/')
import pandas as pd
import numpy as np
import json
import os
from database import phish_db_layer
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.cm import get_cmap
from datetime import datetime
from collections import defaultdict, Counter
import ruptures as rpt
import seaborn as sn
import tldextract

class GraphPlots:
    def __init__(self,):
        self.show_plots = False
        self.legend_size = 14
        self.label_size = 18
    
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
        padding = 0.1
        
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
            
            
    def _add_count_labels(self, angles, values, labels, offset, ax):
    
        # This is the space between the end of the bar and the label
        padding = -0.8
        
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
                fontsize = self.label_size-5,
                color = 'white',
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
        
        PAD = 2
        ANGLES_N = len(VALUES) + PAD * len(np.unique(GROUP))

        ANGLES = np.linspace(0, 2 * np.pi, num=ANGLES_N, endpoint=False)
        WIDTH = (2 * np.pi) / len(ANGLES)

        offset = 0
        IDXS = []
        for size in GROUPS_SIZE:
            IDXS += list(range(offset + PAD, offset + size + PAD))
            offset += size + PAD

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})

        ax.set_theta_offset(offset)
        # ax.set_ylim(-100, 100)
        ax.set_frame_on(False)
        ax.xaxis.grid(False)
        ax.yaxis.grid(False)
        ax.set_xticks([])
        ax.set_yticks([])

        
        COLORS = [f"C{i}" for i, size in enumerate(GROUPS_SIZE) for _ in range(size)]
        print(COLORS)
        ### Add bars for each value
        ax.bar(
            ANGLES[IDXS], VALUES, width=WIDTH, color=COLORS, 
            edgecolor="white", linewidth=2
        )

        ### Add labels to the bars
        self._add_labels(ANGLES[IDXS], VALUES, LABELS, offset, ax)
        self._add_count_labels(ANGLES[IDXS], VALUES , df_data['count'], offset, ax)
        
        offset = 0 
        legend_bars = []
        i = 0
        for group, size in zip(GROUP_LABELS, GROUPS_SIZE):
            # Add line below bars
            x1 = np.linspace(ANGLES[offset + PAD], ANGLES[offset + size + PAD - 1], num=5)
            ax.plot(x1, [-0.1]*5, color="#333333")
            
            # Add text to indicate group
            #ax.text(
            #     np.mean(x1)+0.04, 10, group, color="#333333", fontsize=14, 
            #     fontweight="bold", ha="right", va="top"
            # )

            legend_bars.append(Line2D([0], [0], color=COLORS[i], lw=3)) 
            i += size

            # # Add reference lines at 20, 40, 60, and 80
            x2 = np.linspace(ANGLES[offset], ANGLES[offset + PAD - 1], num=5)
            ax.plot(x2, [1] * 5, color="#bebebe", lw=0.8)
            ax.plot(x2, [2] * 5, color="#bebebe", lw=0.8)
            ax.plot(x2, [3] * 5, color="#bebebe", lw=0.8)
            ax.plot(x2, [4] * 5, color="#bebebe", lw=0.8)
            
            offset += size + PAD

        ax.legend(legend_bars, GROUP_LABELS, loc="upper right", ncol = 1, fontsize = self.legend_size)
        plt.rc('font', size=34)  
        plt.rc('axes', labelsize=34) 
        plt.rc('legend',fontsize=20) 
        plt.tight_layout()
        plt.savefig(file_name,bbox_inches='tight')
 
    def plot_bar(self, df_data, file_name, options = {}):
    	
    	plt.clf()
    
    	df_data.plot.bar(x="labels",y="values", fontsize=12, legend=False)
    	plt.xticks(range(len(df_data["labels"] )), df_data["labels"])
    	#plt.yscale('log')
    	plt.yticks([x for x in range(0, int(df_data['values'].max())+5,10)])
    	if 'xlabel' in options:
    	    plt.xlabel(options['xlabel'], fontsize=16)
    	if 'ylabel' in options:
    	    plt.ylabel(options['ylabel'], fontsize=16)
    	plt.tight_layout()
    	plt.savefig(file_name)
    	
    def plot_bar_grouped(self, df_data, file_name):
    	
    	plt.clf()
    	
    	cmap = get_cmap('Dark2')
    	print(cmap.colors)
    	colors = cmap.colors
    	df_data = df_data.fillna('')
    	group_colors = {g:colors[i+2] for i,g in enumerate(df_data['group'].unique() ) }
    	field_color = df_data['group'].apply(lambda x : group_colors[x])
    	df_data.plot.bar(x="labels",y="values2", rot=0, color = field_color , fontsize=self.label_size)
    	plt.xticks(range(len(df_data["labels"] )), df_data["labels"], rotation =90)
    	plt.yscale('log')
    	plt.tight_layout()
    	plt.savefig(file_name)
    	
    def plot_bar_horizontal(self, df_data, file_name):
    	
    	plt.clf() 
    	df_data = df_data.fillna(0)
    	df_data2 = df_data.transpose()  	
    	ax = df_data2.plot.barh(rot=0, fontsize=self.label_size, stacked = True, legend = False, colormap='Dark2', figsize = (10,3))
    	x_pos = 0
    	y_pos = 0.5
    	for ind,row in df_data.iterrows():
    	    print('index',ind)
    	    if row['percentage'] < 10:
    	        y_pos += 0.4
    	    else:
    	        y_pos = 0.5
    	    ax.text(x_pos, y_pos, ind, fontsize=12, ha="left", va="bottom", rotation=0)
    	    x_pos = x_pos + row['percentage']
    	
    	plt.ylim((0,3))
    	#plt.yticks([])
    	#plt.xticks([])
    	plt.box(False)
    	plt.xlabel('')
    	plt.tight_layout()
    	plt.savefig(file_name)

    def plot_bar_group(self, df_data, file_name):
        plt.clf()
        grouped = df_data.groupby('group')
        print(grouped.head())
        rowlength = grouped.ngroups//2                      
        fig, axs = plt.subplots(figsize=(9,4), 
		nrows=2, ncols=rowlength) 

        targets = zip(grouped.groups.keys(), axs.flatten())
        for i, (key, ax) in enumerate(targets):
            print(key)
            df_g = grouped.get_group(key)[['labels','values2']]
            df_g.plot.bar(x="labels",y="values2", rot=0, fontsize=self.label_size, ax = ax)
            ax.set_title(key)
        ax.legend()

        plt.tight_layout()
        plt.savefig(file_name)

    def plot_donut(self, df_data,fig_name):

        plt.clf()
        # explosion
        explode = [0.03] * df_data.shape[0]
        df_data.plot.pie(y=0,legend=None, autopct='%1.1f%%', pctdistance=0.85, explode= explode, colormap = 'viridis', fontsize=self.label_size)         
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
        GROUP = df_data['group']
        df_data = df_data.drop(['group'], axis=1)
        COLORS = ['C0', 'C0', 'C0', 'C1', 'C1', 'C1', 'C1', 'C1', 'C1', 'C1', 'C1', 'C1', 'C2', 'C2', 'C3', 'C3', 'C3', 'C3']
        axes = df_data.plot.bar(subplots=True , sharey=True, sharex=True, figsize=(6,5), legend = False, width=0.3)
        # print(ax)
        cols = df_data.columns

        plt.yscale('log')
        for c in range(len(cols)):
            axes[c].set_ylabel('Count', fontsize=8)
            axes[c].set_xlabel('Fields', fontsize=10)            
            axes[c].set_title('Page_'+str(len(cols)-c),fontsize=8,y=1.0, pad=-14 )
            #axes[c].set_yscale('log', base=2)
            axes[c].set_yticks([10,100,1000])
            #axes[c].legend(False)
            #axes[c].legend(fontsize=6,loc="upper right" )
            axes[c].tick_params(axis = 'both', labelsize = 10)
            for axbar,color in zip(axes[c].get_children(), COLORS):
                axbar.set_color(color)
        
        #plt.xlabel('Field Categories')
        # plt.rc('font', size=14)  
        # plt.rc('axes', labelsize=14) 
        #plt.xticks(fontsize=10, rotation=45)
        #plt.yticks(fontsize=8, rotation=0)
        # plt.rc('legend',fontsize=6) 
        # plt.rcParams['xtick.labelsize'] = 6
        # plt.rcParams['ytick.labelsize'] = 6
        plt.subplots_adjust(hspace=0)
        plt.tight_layout()        
        plt.savefig(fig_name,bbox_inches='tight')


class PaperGraphs:

    def __init__(self,):
        self.results_dir = '../data/paper_graphs/'        
        self.graph = GraphPlots()



    def plot_fields_count(self, fields_file_path):
        try:
            df_data = pd.read_csv(fields_file_path,header=0)
            df_data['norm_count'] = np.log10(df_data['count'])      
            df_data['percentage'] = (df_data['count'] / df_data['count'].sum()) * 100
            df_data = df_data.round(2)
            #df_data['percentage'] = df_data['percentage'].apply(lambda x: int(x) )
            #df_data['labels'] = df_data[['field','count']].apply(lambda x: "{}({})".format(x['field'],x['count']), axis = 1)
            df_data.rename(columns={"norm_count": "values","field":"labels", "group": "group"}, inplace=True)

            self.graph.plot_circular_bar(df_data,self.results_dir+'field_groups2.pdf')

            #df_data.rename(columns={"count": "values2", "field": "labels", "group": "group"}, inplace=True)
            #self.graph.plot_bar(df_data,self.results_dir+'field_groups_bar.pdf')
            
        except Exception as e:
            print('Fields Count ::', e)
            
            

    def plot_submit_methods(self, submit_methods):
        try:
            dict_data = {k:[v] for k,v in submit_methods.items() if len(k)>2}
            df_data = pd.DataFrame.from_dict(dict_data, orient = 'index')
            df_data = df_data.reset_index()
            print(df_data.head())
            submit_order = ['button','submit_button','visual_button','link_button','form_name', 'form_id', 'input_image', 'path_click','canvas_click','enter_submit']
                       
            df_data['percentage'] = (df_data[0] / df_data[0].sum()) * 100
            df_data['labels'] = df_data['index'].apply(lambda x: x)
            df_data['values'] = df_data['percentage'].apply(lambda x: x)
            df_data = df_data.set_index('labels')
            df_data = df_data.reindex(submit_order) 
            df_data = df_data.reset_index()
            print(df_data.head())
            #df_data['percentage'] = df_data['percentage'].apply(lambda x: int(x) )
            df_data = df_data.round(2)
            df_data = df_data.drop([0,'index'], axis = 1)
            self.graph.plot_bar(df_data,self.results_dir+'submit_methods_bar.pdf', {'xlabel':'Submit Methods', 'ylabel': 'Percentage'})
        except Exception as e:
            print('Submit Methods :: ',e)

    def plot_parsed_methods(self, parsed_methods):
        try:
            dict_data = {k:[v] for k,v in parsed_methods.items() if len(k)>2}
            df_data = pd.DataFrame.from_dict(dict_data, orient = 'index')
            df_data = df_data.reset_index()
            df_data['percentage'] = (df_data[0] / df_data[0].sum()) * 100
            df_data['labels'] = df_data['index'].apply(lambda x: x)
            df_data['values'] = df_data['percentage'].apply(lambda x: x)
            
            self.graph.plot_bar(df_data, self.results_dir+'parsed_methods_bar.pdf', {'xlabel':'Parsed Methods', 'ylabel': 'Percentage'})
        except Exception as e:
            print('Parsed Methods ::',e)

    def plot_multi_phishing_data(self, field_counts):
        def include_col(col):
            print(col.max(), col.max()<=10)
            return col.max()<=10
        try:
            df_fields = pd.DataFrame.from_dict(field_counts)
            
            FIELDS_TO_PLOT = {'Identification':'Login','Password':'Login','Email':'Login','Name':'Personal', 'Address':'Personal', 'Phone':'Personal', 'City':'Personal', 'State':'Personal', 'Date':'Personal', 'Question':'Personal', 'Answer':'Personal','Zip':'Personal', 'License':'Social', 'SSN':'Social', 'Card':'Financial', 'CVV':'Financial', 'ExpDate':'Financial', 'Year':'Financial'}
            
            df_fields = df_fields.reindex(FIELDS_TO_PLOT.keys())
            max_pages = len(field_counts.keys())
            cols = []
            for i in range(max_pages,0,-1):
                cols.append('Page_'+str(i))
                if 'Page_'+str(i) not in df_fields.columns:
                    df_fields['Page_'+str(i)] =[np.nan] * df_fields.shape[0]
            df_fields = df_fields[cols]
            df_fields = df_fields.drop(df_fields.columns[df_fields.apply(lambda col: col.max()<=10)],axis=1)
            
            df_fields['group'] = [FIELDS_TO_PLOT.get(x) for x in df_fields.index]
            #df_fields = df_fields.sort_values(by=['Page_1'], ascending=False)
            df_fields = df_fields.fillna(0)            
            print(df_fields.head(20))
            #self.graph.plot_heatmap(df_fields, self.results_dir+'multi_phishing_fields_count_heatmap.pdf')
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