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

containers_path = '/Data/PhishMesh_Data/' #'../PhishMeshController/phish_containers_data/'
sha_file_hashes = defaultdict(list)
ssdeep_file_hashes = defaultdict(list)

def calculate_ssdeep_hash(file_path, file_name):
	try:
		global ssdeep_file_hashes
		# print(file_path)
		if file_path !='' and os.path.exists(file_path):
			if 'tar' in file_path:
				t = tarfile.open(file_path)				
				with open('./temp', 'wb') as fd:
					fbuf = t.extractfile('data'+file_name)
					fd.write(fbuf.read())
				file_hash = ssdeep.hash_from_file('./temp')
				# print(file_path, file_name, file_hash)
				return file_hash
			else:
				file_hash = ssdeep.hash_from_file(file_path)
				# print(file_path, file_hash)
				ssdeep_file_hashes[file_hash].append(file_name)
				return file_hash
		return ''
	except Exception as e:
		# print(e)
		return ''

def cluster_ssdeep_hashes(new_hash, hashes_set):
	
	similarity_scores = {}
	SSDEEP_SIMILARITY_THRESHOLD = 75

	for h in hashes_set:
		try:
			score = ssdeep.compare(h, new_hash)
			similarity_scores[h] = score
			
		except Exception as e:
			continue
			# print(new_hash, e)
	# print(new_hash, similarity_scores)

	return dict(filter(lambda x: x[1] > SSDEEP_SIMILARITY_THRESHOLD, similarity_scores.items()))

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
	file_count = 0
	for d in os.listdir(containers_path):
		if 'top' in d:
			continue
		try:
			t = tarfile.open(containers_path+d+'/data.tar')
			# print(t)
			t.extractall()
			file_dir_path = './data/resources/'+d.replace('container_','')
			for f in os.listdir(file_dir_path):
				file_count = file_count+1
				calculate_sha_hash(file_dir_path+'/'+f,d+'_'+f )
				calculate_ssdeep_hash(file_dir_path+'/'+f,d+'_'+f )
			rmtree('./data')
			t.close()
		except Exception as te:
			print(te)

	print('Total Files :: ', file_count)
	print('SSDeep Hashes Count ::', len(ssdeep_file_hashes))
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