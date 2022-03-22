import sys
sys.path.append('/home/sk-lab/Desktop/PhishProDetector/PhishMeshCrawler/')
import pandas as pd
import numpy as np
import json
import os
# from database import phish_db_layer
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from datetime import datetime
import ruptures as rpt


class GraphPlots:
    def __init__(self,):
        self.show_plots = False
        self.legend_size = 14
        self.label_size = 16
    
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


class PaperGraphs:

    def __init__(self,):
        self.results_dir = '../data/'        
        self.graph = GraphPlots()

    def plot_fields_count(self, fields_file_path):

        df_data = pd.read_csv(fields_file_path,header=0)
        df_data['norm_count'] = np.log2(df_data['count'])        
        df_data.rename(columns={"norm_count": "values", "field": "labels", "group": "group"}, inplace=True)

        self.graph.plot_circular_bar(df_data,self.results_dir+'field_groups2.pdf')

    def plot_submit_methods(self, submit_methods):

        dict_data = {k:[v] for k,v in submit_methods.items() if len(k)>2}
        df_data = pd.DataFrame.from_dict(dict_data, orient = 'index')
        self.graph.plot_donut(df_data,self.results_dir+'submit_methods.pdf')

    def plot_parsed_methods(self, parsed_methods):
       
        dict_data = {k:[v] for k,v in parsed_methods.items() if len(k)>2}
        df_data = pd.DataFrame.from_dict(dict_data, orient = 'index')
        self.graph.plot_donut(df_data, self.results_dir+'parsed_methods.pdf')



class DataAnalyzer:
    def __init__(self):
        self.submit_methods = {}
        self.parsed_methods = {}
        self.graphs = PaperGraphs()
    
    def parse_logs(self):

        containers_dir_path = '../PhishMeshController/phish_containers_data/20220228/phish_containers_data/'

        for d in os.listdir(containers_dir_path):
            logs_dir = os.path.join(containers_dir_path,d,'data/logs/')
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
                                    parsed_method = 'Element Data'
                                elif 'OCR' in parsed_method:
                                    parsed_method = 'OCR'
                                elif 'InnerText' in parsed_method:
                                    parsed_method = 'Sibling Element Data'
                                self.parsed_methods[parsed_method] = self.parsed_methods.get(parsed_method,0) + 1


    def plot_graphs():
        fields_file_path = '../data/fields_groups_count.csv'
        self.graphs.plot_fields_count(fields_file_path)
        self.graphs.plot_submit_methods(self.submit_methods)
        self.graphs.plot_parsed_methods(self.parsed_methods)


if __name__ == '__main__':

    paper_graph = PaperGraphs()

    paper_graph.parse_logs()
    paper_graph.plot_submit_methods()
    paper_graph.plot_parsed_methods()





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