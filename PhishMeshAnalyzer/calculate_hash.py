import ssdeep
import tarfile
import json
from shutil import rmtree
from collections import defaultdict
from pprint import pprint
import hashlib
import os
import sys
sys.path.append('/home/sk-lab/Desktop/PhishProDetector/PhishMeshCrawler/')
from database import phish_db_layer

containers_path = '../PhishMeshController/phish_containers_data/'
sha_file_hashes = defaultdict(list)
ssdeeep_file_hashes = defaultdict(list)

def calculate_ssdeep_hash(file_path, file_name):
	global ssdeeep_file_hashes
	file_hash = ssdeep.hash_from_file(file_path)
	ssdeep_file_hashes[file_hash].append(file_name)

def calculate_sha_hash(file_path, file_name):
	global sha_file_hashes

	hasher = hashlib.sha1()
	with open(file_path, 'rb') as afile:
		buf = afile.read()    
		hasher.update(buf)
	digest = hasher.hexdigest()	
	sha_file_hashes[digest].append(file_name)


def calculate_hashes():
	global ssdeep_file_hashes, sha_file_hashes

	for d in os.listdir(containers_path):
		try:
			t = tarfile.open(containers_path+d+'/data.tar')
			# print(t)
			t.extractall()
			file_dir_path = './data/resources/'+d.replace('container_','')
			for f in os.listdir(file_dir_path):
				calculate_sha_hash(file_dir_path+'/'+f,d+'_'+f )
				calculate_ssdeep_hash
			rmtree('./data')
			t.close()
		except Exception as te:
			print(te)

	print('SSDeep Hashes Count ::', len(ssdeeep_file_hashes))
	print('SHA Hashes Count ::', len(sha_file_hashes))

	with open('../data/ssdeep_hashes.json','w') as f:
		json.dump(ssdeep_file_hashes, f, indent=4)

	with open('../data/sha_hashes.json','w') as f:
		json.dump(sha_file_hashes, f, indent=4)

		

def cluster_files():
	file_hashes = {}
	cluster_id = 0
	with open('../data/ssdeep_hashes.json', 'r') as f:
		file_hashes = json.load(f)
	for k,v in file_hashes.items():
		for fname in v:
			container_name = '_'.join(fname.split('_')[:5])
			res_name = '_'.join(fname.split('_')[5:]) 
			t = tarfile.open(containers_path+container_name+'/data.tar')
			# pprint(t.getmembers())
			with open('../data/res_clusters/'+str(cluster_id)+'_'+res_name, 'wb') as fd:
				fbuf = t.extractfile('data/resources/'+container_name.replace('container_','')+'/'+res_name )
				fd.write(fbuf.read())
			t.close()
		cluster_id = cluster_id+1


if __name__ == '__main__':
	calculate_hashes()
	# cluster_files()