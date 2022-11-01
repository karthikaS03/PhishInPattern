import tarfile
import os
import shutil
import json
from bs4 import BeautifulSoup
from matplotlib.pyplot import text
from numpy.lib.twodim_base import mask_indices
import sys
sys.path.append('/home/sk-lab/Desktop/PhishProDetector/PhishMeshCrawler/')
from database import phish_db_layer, phish_db_schema

containers_path = '../PhishMeshController/phish_containers_data/20220209/'
# '../PhishMeshController/phish_containers_data/' #'/Data/PhishMesh_Data/'


def get_captcha_slices(container_id = None, img_file = None, img_path = '../data/openphish_images/'):
    captcha_hashes = {}
    for d in os.listdir(containers_path):
        if 'palo'  in d:			
            if container_id != None and d != container_id:
                continue
            try:
                t = tarfile.open(containers_path+d+'/data.tar')                
                t.extractall()
                file_dir_path = './data/images/' + d.replace('container_','') +'/slices'
                for f in os.listdir(file_dir_path):
                    if img_file!=None and f!=img_file:
                        continue
                    if 'captcha'  in f:
                        c_hash = calculate_sha_hash(file_dir_path+'/'+f)
                        captcha_hashes[c_hash] = captcha_hashes.get(c_hash,[]) +[f]
                        shutil.move( file_dir_path + '/' + f, img_path+c_hash+'.png' )
                shutil.rmtree('./data')
                t.close()
            except Exception as te:
                print(te)
    with open('captcha_hashes_files.json','w') as f:
        json.dump(captcha_hashes,f,indent=4)

def get_screenshots(container_id = None, img_file = None, img_path = '../data/palo_new_images/'):
    for d in os.listdir(containers_path):
        if 'palo'  in d:			
            if container_id != None and d != container_id:
                continue
            try:
                t = tarfile.open(containers_path+d+'/data.tar')                
                t.extractall()
                file_dir_path = './data/images/' + d.replace('container_','')
                for f in os.listdir(file_dir_path):
                    if img_file!=None and f!=img_file:
                        continue
                    if 'slice' not in f and '_0_screenshot' in f:
                        f_hash = calculate_sha_hash(file_dir_path + '/' +f)
                        shutil.move( file_dir_path + '/' + f, img_path+f+'.png' )
                shutil.rmtree('./data')
                t.close()
            except Exception as te:
                print(te)

def get_files_with_canvas():

    def check_if_canvas_found(page_content):
        try:
            soup = BeautifulSoup(page_content, 'html.parser')
            canvases = soup.find_all('canvas')
            # print(canvases)
            return True if len(canvases)>0 else False
        except Exception as ex:
            print(ex)
            return False

    for d in os.listdir(containers_path):
        if True:			
            
            try:
                t = tarfile.open(containers_path+d+'/data.tar')                
                t.extractall()                
                fnames = [x.name for x in  t.getmembers() if '/resources/' in x.name]
                
                for f  in fnames:
                    
                    if os.path.isdir('./'+f):
                        continue
                    
                    with open('./'+f, 'r') as fread:
                        try:                            
                            content = fread.read()                            
                            if check_if_canvas_found(content):
                                print('Canvas Found @ '+ d+ ' in File ::'+ f)
                        except Exception as e:
                            # shutil.rmtree('./data')
                            continue                
                shutil.rmtree('./data')
                t.close()
            except Exception as te:
                # print(te)
                continue
            

def calculate_sha_hash(file_path):
    import hashlib

    hasher = hashlib.sha1()
    with open(file_path, 'rb') as afile:
        buf = afile.read()    
        hasher.update(buf)
    digest = hasher.hexdigest()	
    return digest
     

def get_files_with_captcha():       

    for d in os.listdir(containers_path):
        if 'openphish'  in d:		
            print(d)
            try:
                t = tarfile.open(containers_path+d+'/data.tar')                
                t.extractall()                
                fnames = [x.name for x in  t.getmembers() if '/resources/' in x.name]
                for f  in fnames:                    
                    if 'captcha' in f :

                        shutil.move( f, '../data/openphish_captcha_scripts/'+ calculate_sha_hash(f)+ '_'+ f.split('/')[-1])
                        shutil.rmtree('./data')
                        get_screenshots(d, None, '../data/openphish_captcha_images/')                        
                        print('Captcha Found @ '+ d+ ' in File ::'+ f)
                
                t.close()
            except Exception as te:
               
                continue


def get_pages_with_unknown_data():

    ## get resource data from a dataframe
    image_ids = phish_db_layer.fetch_unknown_pages()

    for img_file in image_ids :
        img_file = img_file[0]
        print(img_file)
        container_id = '_'.join(['container'] + img_file.split('_')[:-2])
        get_screenshots(container_id, img_file, '../data/unknown_images/')


def record_checked_urls():
    checked_dirpath = '../data/phishing_dumps/csv/'
    count = 0
    for f in os.listdir(checked_dirpath):
        urls = []
        if 'checked' in f:
            print(f)
            with open(checked_dirpath+f,'r') as fout:
                l = fout.readline()
                while l:
                    try:                         
                        u = json.loads(l)                                     
                        status_obj = phish_db_schema.PaloUrl_Status(url= u['url'].replace("'",""), category = u['category'])
                        phish_db_layer.add_palourl_status(status_obj)
                        count = count+1
                        l = fout.readline()
                    except:
                        l = fout.readline()
                        continue
    print(count)

def get_listeners(container_id = None):
    events_count = {}
    node_events_count = {}

    for d in os.listdir(containers_path):
        if 'top' in d:			
            if container_id != None and d != container_id:
                continue
            try:
                t = tarfile.open(containers_path+d+'/data.tar')                
                t.extractall()
                file_dir_path = './data'
                for f in os.listdir(file_dir_path):
                    print(f)
                    if '.json' in f and '_0' in f:
                        with open(file_dir_path+'/'+f, 'r') as fj:
                            # print(fj.read())
                            listeners = json.loads(fj.read())
                        
                        for obj in listeners:
                            node_name = obj['node']['localName']
                            for l in obj['listeners']:
                                typ = l['type']
                                events_count[typ] = events_count.get(typ,0) + 1
                                node_events_count[node_name+'_'+typ] = node_events_count.get(node_name+'_'+typ,0) + 1
                shutil.rmtree('./data')
                t.close()
            except Exception as te:
                print(te)
    
    events_count = dict(sorted(events_count.items(), key = lambda x: x[1], reverse= True))
    node_events_count = dict(sorted(node_events_count.items(), key = lambda x: x[1], reverse= True))
    with open('../data/json_results/listeners_count.json', 'w') as f:
        json.dump(events_count,f,indent = 2)
    with open('../data/json_results/node_listeners_count.json', 'w') as f:
        json.dump(node_events_count,f,indent = 2)


if __name__ =='__main__':     

    # get_listeners()
    # record_checked_urls()
    # get_files_with_canvas()
    get_screenshots()
    # get_files_with_captcha()
    # get_pages_with_unknown_data()

    # get_captcha_slices(img_path='../data/captcha_slices/')
