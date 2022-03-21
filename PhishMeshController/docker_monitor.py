import docker
import os
import time
import datetime
import tarfile
from docker_config import *
import sys
from datetime import date
from utils import download_file

# sys.path.append("../SWSec_Analysis/database")

# import db_operations

# dbo = db_operations.DBOperator()

if CRAWL_SW ==True:
    client = docker.from_env(timeout=(CRAWL_TIMEOUT))
else:
    client = docker.from_env(timeout=(ANALYSIS_TIMEOUT))

export_path = CONFIG_EXPORT_PATH

    # logging.basicConfig(name = name , filename=name +'.log', filemode='w', ,level=logging.INFO)


def get_time():
	currentDT = datetime.datetime.now()
	return '['+currentDT.strftime("%Y-%m-%d %H:%M:%S") +'] '

def initiate_container(url, id, script_name, iteration_count,  container_timeout, url_det):	
    try:
        ## create and setup container ##
        get_logger('container_'+id, 1).info(get_time() + 'container_'+id+' creating!!')
        container_id  = client.containers.create(image=docker_image,name='container_'+id,volumes = vols,
                                                shm_size='1G', user=docker_user, #network='phishpro-network',
                                                publish_all_ports=True, detach=False)
        container = client.containers.get('container_'+str(id))
        container.start()
        get_logger('container_'+id).info(get_time() + 'container_'+id+' created successfully!!')    
        
        ## wait for display to be activated ##
        time.sleep(10)
        ## Exeecute the browser automation script
        execute_script(url, id, script_name,  iteration_count, container_timeout-100, url_det)
    except Exception as e:
        print(e)
        get_logger('container_'+id).info(e) 

def execute_script(url, id, script_name,  iteration_count, container_timeout, url_det):
    try:	
        ## Execute javascript file
        get_logger('container_'+id).info(get_time() +'container_'+id+': Executing crawler script')
        container = client.containers.get('container_'+str(id))               
        #logs = container.attach(stream=True,stdout=True,stderr=True)
        _,logs = container.exec_run(cmd=['python3',script_name, url,'--phish_id', id.replace('container_Phish_','')], user=docker_user, detach=False, stream=True)
               
        for log in logs:
            # print('Container_'+id+' :: LOG :: '+log.decode('UTF-8'))
            get_logger('container_'+id).info('Container_'+id+' :: LOG :: '+log.decode('UTF-8'))
            
        # print('timeout started')
        # time.sleep(container_timeout) 
        get_logger('container_'+id).info(get_time() +'container_'+id+': Execution complete!!')	
        export_container_logs(id,iteration_count, url_det)
    except Exception as e:
        get_logger('container_'+id).info('Exception ')
        get_logger('container_'+id).info(e)
        export_container_logs(id,iteration_count, url_det)

def stop_container(id):
    try:
        container = client.containers.get('container_'+str(id))
        if container:
            get_logger('container_'+id).info(get_time() + 'container_'+id+' stopping!!')
            container.pause()
            time.sleep(2)
            container.stop()
            time.sleep(1)
            container.remove()
    except Exception as e:
        get_logger('container_'+id).info(e)

def remove_containers():
    # while client.containers.list():		
        try:
            for c in client.containers.list():
                # print(c.name)
                if 'Phish' not in c.name:
                    # print('Removing')
                    c.stop()
                    c.remove()
        except Exception as e:
            print(e)
        
def resume_container(url, id, script_name, iteration_count, container_timeout):
    container = client.containers.get('container_'+str(id))
    if container:
        get_logger('container_'+id).info(get_time() + 'container_'+id+'_'+str(iteration_count)+' resuming!!')
        container.start()
        ## wait for display to be activated ##
        time.sleep(10)
        ##   Open a blank page on the browser and wait for notifications 
        execute_script(url,id, script_name, iteration_count, container_timeout-100)


def export_container_logs(id,count, url_det):
    try:
        # print(export_path)
        print('Exporting Container :: '+id)
        container = client.containers.get('container_'+str(id))
        get_logger('container_'+id).info(get_time() + 'container_'+id+'exporting files!!')
        # dir_path = export_path+'container_'+id+'/'
        dir_path = os.path.join(export_path,date.today().strftime("%Y%m%d"))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        dir_path = dir_path +'/container_'+id+'/'
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        with open(dir_path+'data.tar', 'wb') as f:
            bits, stat = container.get_archive('/home/pptruser/data/')
            for chunk in bits:
                f.write(chunk)
        t = tarfile.open(dir_path+'data.tar')                
        t.extractall(path= dir_path)
        t.close()
        os.remove(dir_path+'data.tar') 
        
        ### download the site's screenshot provided by openphish
        file_url = url_det['screenshot']
        if file_url !=None and 'http' in file_url:
            download_file(file_url, dir_path + '/data/openphish_screenshot.png' )

        ### download the phishkit if provided by openphish
        file_url = url_det['phishkit']
        if file_url !=None and 'http' in file_url:            
            download_file(file_url, dir_path + '/data/openphish_phishkit.zip' )
        
    except Exception as e:
        get_logger('container_'+id).info(e)         
    
    

def docker_prune():
    ## Remove containers that are unused  ##
    try:
        client.containers.prune()		
    except Exception as e:
        get_logger('container_'+id).info(e)


def test():
    remove_containers()
    #docker_prune()
    initiate_container('http://446884cox.weebly.com/','phishmesh_teste3202', 'crawl_page.py','0', 1200 )   
   
   
    
if __name__== "__main__":
    test()
