'''
deduplication with simhash
'''
import csv
import re
from simhash import Simhash, SimhashIndex


def read_sentences(number):
    filepath = './input/user_rights_data_' + str(number) + "_sentences.tsv"
    sentences = []
    with open(filepath,'r') as fin:
        reader = csv.reader(fin, delimiter='\t')
        for row in reader:
            sentence = row[1]
            sentences.append(str(row[0]) + ' ' + sentence)
    return sentences

def write_sentences(sentences, number):
    filepath = './input/user_rights_data_' + str(number) + '_sentences_deduplicated.tsv'
    with open(filepath, 'w') as fout:
        writer = csv.writer(fout, delimiter='\t')
        for sentence in sentences:
            row = []
            row.append(sentence.split(' ')[0])
            row.append(" ".join(sentence.split(' ')[1:]))
            writer.writerow(row)

def get_features(s):
    width = 3
    s = s.lower()
    s = re.sub(r'[^\w]+', '', s)
    return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]


for i in range(5, 11):
    sentences = read_sentences(i)

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
    write_sentences(sentences, i)
