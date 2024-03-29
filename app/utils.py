
from torch.nn.utils.rnn import pad_sequence

import torch
import torch.nn.init as init
import torch.nn as nn

from datasets import load_dataset
from torch.utils.data import TensorDataset, DataLoader

import numpy as np

import csv
import os
import errno


# Obtain the dataset from huggingface
def get_datasets():
	return {
	 	'imdb': load_dataset('imdb'), 
		'sst2': load_dataset('sst2'),
		'y_p': load_dataset('yelp_polarity')
	}
 

# Get the accuracy score from the logits
def accuracy_score(output, label):
	output_class = torch.argmax(torch.softmax(output, dim=1), dim=1)
	return (output_class == label).sum().item()/len(output)


# Collate ducntion to build the dataset dictionary
def collate_fn(batch):
	input_ids = pad_sequence([item[0]['input_ids'] for item in batch], batch_first=True, padding_value=0)
	attention_mask = pad_sequence([item[0]['attention_mask'] for item in batch], batch_first=True, padding_value=0)
	labels = torch.tensor([item[1] for item in batch])

	return {'input_ids': input_ids, 'attention_mask': attention_mask}, labels


# Function to write the results into a csv file
def write_csv(ts_dir, head, values, categoty_type):
	if (not os.path.exists(f'app/results/{ts_dir}/{categoty_type}_results.csv')):
		
		with open(f'app/results/{ts_dir}/{categoty_type}_results.csv', 'w', encoding='UTF8') as f:
			writer = csv.writer(f)
			writer.writerow(head)
			f.close()
	
	with open(f'app/results/{ts_dir}/{categoty_type}_results.csv', 'a', encoding='UTF8') as f:
		writer = csv.writer(f)
		writer.writerow(values)
		f.close()
		
		
# Function to create the csv results directory
def create_ts_dir_res(timestamp):
	
	mydir = os.path.join('app/results', timestamp) #results
	try:
		os.makedirs(mydir)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise  # This was not a "directory exist" error..
		

# Function to initialize the models parameters
def init_params(m):
	if isinstance(m, nn.Linear):
		init.normal_(m.weight, std=1e-3)
		if m.bias is not None: init.constant_(m.bias, 0)        


# Function to read the embeddinggiven the bese model embedding and the dataset name
def read_embbedings(dataset_name, base_embeds_model, bool_validation = False):

	path = f'app/embeddings/{base_embeds_model}/{dataset_name}'
	
	if not bool_validation:
		x_train = np.concatenate([np.load(f'{path}/train_embeddings.npy'), np.load(f'{path}/val_embeddings.npy')], axis=0, dtype=np.float32)
		x_test = np.load(f'{path}/test_embeddings.npy').astype(np.float32)
			
		y_train = np.concatenate([np.load(f'{path}/labels/train_labels.npy'), np.load(f'{path}/labels/val_labels.npy')], axis=0, dtype=np.int8)
		y_test = np.load(f'{path}/labels/test_labels.npy').astype(np.int8)
    
		return x_train, x_test, y_train, y_test

	else:
		x_train = torch.tensor(np.load(f'{path}/train_embeddings.npy'), dtype=torch.float32)
		x_val = torch.tensor(np.load(f'{path}/val_embeddings.npy'), dtype=torch.float32)
		x_test = torch.tensor(np.load(f'{path}/test_embeddings.npy'), dtype=torch.float32)
    
		y_train = np.load(f'{path}/labels/train_labels.npy')
		y_val = np.load(f'{path}/labels/val_labels.npy')
		y_test = np.load(f'{path}/labels/test_labels.npy')
  
		y_train[y_train == -1] = 0
		y_val[y_val == -1] = 0
		y_test[y_test == -1] = 0
    
		return x_train, x_val, x_test, torch.tensor(y_train, dtype=torch.long), torch.tensor(y_val, dtype=torch.long), torch.tensor(y_test, dtype=torch.long)


# Fucntion to create the dataloaders from the numeric embedding
def get_text_dataloaders(x_train, x_val, x_test, y_train, y_val, y_test, batch_size):
	train_dl = DataLoader(TensorDataset(x_train, y_train), batch_size=batch_size, shuffle=True)
	val_dl = DataLoader(TensorDataset(x_val, y_val), batch_size=batch_size, shuffle=False)
	test_dl = DataLoader(TensorDataset(x_test, y_test), batch_size=batch_size, shuffle=False)
	return train_dl, val_dl, test_dl


# Function to create the competitors embeddigns
def get_competitors_embeddings_dls(ds_name, base_embeds_model, batch_size):
	x_train, x_val, x_test, y_train, y_val, y_test = read_embbedings(ds_name, base_embeds_model, bool_validation=True)

	# we use embedding approach of the main strategy
	x_train = torch.unsqueeze(torch.clone(x_train[:,-1,:]), dim=1)
	x_val = torch.unsqueeze(torch.clone(x_val[:,-1,:]), dim=1)
	x_test = torch.unsqueeze(torch.clone(x_test[:,-1,:]), dim=1)
    
	return get_text_dataloaders(x_train, x_val, x_test, y_train, y_val, y_test, batch_size)
 