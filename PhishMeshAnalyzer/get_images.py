import tarfile
import os
import shutil
from bs4 import BeautifulSoup
from matplotlib.pyplot import text
from numpy.lib.twodim_base import mask_indices
import sys
sys.path.append('/home/sk-lab/Desktop/PhishProDetector/PhishMeshCrawler/')
# from database import phish_db_layer

containers_path = '../PhishMeshController/phish_containers_data/'
# '../PhishMeshController/phish_containers_data/' #'/Data/PhishMesh_Data/'




def get_screenshots(container_id = None, img_file = None, img_path = '../data/openphish_images/'):
    for d in os.listdir(containers_path):
        if 'openphish'  in d:			
            if container_id != None and d != container_id:
                continue
            try:
                t = tarfile.open(containers_path+d+'/data.tar')                
                t.extractall()
                file_dir_path = './data/images/' + d.replace('container_','')
                for f in os.listdir(file_dir_path):
                    if img_file!=None and f!=img_file:
                        continue
                    if 'slice' not in f:
                        shutil.move( file_dir_path + '/' + f, img_path )
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

if __name__ =='__main__':     

    # get_files_with_canvas()
    # get_screenshots()
    get_files_with_captcha()
    # get_pages_with_unknown_data()