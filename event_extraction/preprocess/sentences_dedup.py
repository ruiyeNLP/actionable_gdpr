'''
deduplication with simhash
'''
import csv
import re

sentences = []
with open('./input/user_rights_sentences.tsv','r') as fin:
    reader = csv.reader(fin,delimiter='\t')
    for row in reader:
        sentence = row[1]
        sentences.append(str(row[0])+' '+sentence)

from simhash import Simhash, SimhashIndex

def get_features(s):
    width = 3
    s = s.lower()
    s = re.sub(r'[^\w]+', '', s)
    return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]

objs = [(str(idx), Simhash(get_features(sentence))) for idx,sentence in enumerate(sentences)]
index = SimhashIndex(objs, k=8)

index_duplicated = [] # save all duplicated indexs 
counter_skipped = 0
for idx, sentence in enumerate(sentences):
    s1 = Simhash(get_features(sentence))
    near_indexs = index.get_near_dups(s1)
    if len(near_indexs)==1 and near_indexs[0]==str(idx):
        counter_skipped += 1
        continue
    
    index_length_dict = {}
    for near_index in near_indexs:
        index_length_dict[near_index] = len(sentences[int(near_index)])
    max_length_index=max(index_length_dict, key=index_length_dict.get)
    dict(sorted(index_length_dict.items()))

    to_delete_index = []
    for near_index in near_indexs:
        if near_index != max_length_index:
            index_duplicated.append(int(near_index))
            to_delete_index.append(near_index)
    #print('index: ', idx, '\tindex_length_dict: ', index_length_dict, '\tto_delet_index: ', to_delete_index)

print(len(index_duplicated))
print(len(set(index_duplicated)))
print(sorted(set(index_duplicated), reverse=True))
# remove sentences by index
for idx in sorted(set(index_duplicated), reverse=True):
    del sentences[idx]

with open('./input/user_rights_sentences_dedup_test_output.tsv','w') as fout:
    writer = csv.writer(fout,delimiter='\t')
    for sentence in sentences:
        row[0] = sentence.split(' ')[0]
        writensentence = " ".join(sentence.split(' ')[1:])
        writer.writerow([row[0]]+[writensentence])
