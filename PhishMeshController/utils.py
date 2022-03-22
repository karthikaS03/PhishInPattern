import requests 
import shutil 

def download_file(file_url, dest_file_path):
    
    # Open the url, set stream to True, this will return the stream content.
    r = requests.get(file_url, stream = True)

    # Check if the file was retrieved successfully
    if r.status_code == 200:
        # Set decode_content value to True, otherwise the downloaded file's size will be zero.
        r.raw.decode_content = True
        
        # Open a local file with wb ( write binary ) permission.
        with open(dest_file_path,'wb') as f:
            shutil.copyfileobj(r.raw, f)
            
        print('Image sucessfully Downloaded: ',dest_file_path)
    else:
        print('Image Couldn\'t be retreived')


    