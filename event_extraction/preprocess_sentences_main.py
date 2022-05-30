'''
preprocess with deduplication
'''
import csv
import re

min_length = 1000
sentences = []
with open('./input/user_rights_sentences.tsv','r') as fin:
    reader = csv.reader(fin,delimiter='\t')
    for row in reader:
        sentence = row[1]
        sentence = " ".join(sentence.split()) # remove duplicated spaces
        # record minimun length of sentences
        length = len(re.sub(r'[^\w]+', '', sentence))
        if length < min_length:
            min_length = length

        sentences.append(str(row[0])+' '+sentence)



from simhash import Simhash, SimhashIndex

def get_features(s):
    width = min_length # not sure how to decide the width 
    s = s.lower()
    s = re.sub(r'[^\w]+', '', s)
    return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]

objs = [(str(idx), Simhash(get_features(sentence))) for idx,sentence in enumerate(sentences[:20])]
index = SimhashIndex(objs, k=len(sentences[:20]))

index_duplicated = [] # save all dup indexs 
for idx, sentence in enumerate(sentences[:20]):
    s1 = Simhash(get_features(sentence))
    near_indexs = index.get_near_dups(s1)
    if str(idx) in near_indexs:
        near_indexs.remove(str(idx)) # to do: compare and save the longest sentences
    if near_indexs:
        for near_indexs in near_indexs:
            index_duplicated.append(int(near_indexs))

# remove sentences by index
for idx in set(index_duplicated):
    del sentences[idx]

with open('./input/user_rights_sentences_dedup_test_output.tsv','w') as fout:
    writer = csv.writer(fout,delimiter=',')
    for sentence in sentences:
        row[0] = sentence.split(' ')[0]
        writensentence = " ".join(sentence.split(' ')[1:])
        writer.writerow([row[0]]+[writensentence])


'''
add 'access_info' pipeline to spacy models 
to lable email,url,address
'''
import json
import spacy
import re
from spacy.tokens import Span
from spacy.language import Language
import csv
from textacy import preprocessing as textacy_preprocessing
from somajo import SoMaJo
import string
import pyap

nlp = spacy.load('en_core_web_lg',disable=["ner"]) 
somajo_tokenizer = SoMaJo("en_PTB", split_sentences=False)
sentences = []
with open('./input/user_rights_sentences.tsv') as csvfile:
		reader = csv.reader(csvfile,delimiter='\t')
		for row in reader:
			sentences.append(row[1])	

# def somajo_remove_url(text): # label_email
#     """
#     A customized function to remove e-mails which have whitespaces
#     and URLs which were apparently not cleaned from the corpus.
#     """
#     out = []
#     text_as_list = list()
#     text_as_list.append(text)
#     tokenized_text = somajo_tokenizer.tokenize_text(text_as_list)
#     for dummy_tokenized_text in tokenized_text:
#         for token in dummy_tokenized_text:
#             if token.token_class == "URL":
#                 out.append("-URL-")
#             elif token.original_spelling is not None:
#                 out.append(token.original_spelling)
#             else:
#                 out.append(token.text)
#             if token.space_after:
#                 out.append(" ")
#     return "".join(out)


# def text_preprocessing(text): # label_email
#     text = textacy_preprocessing.normalize.hyphenated_words(text)
#     text = textacy_preprocessing.normalize.whitespace(text)
#     text = textacy_preprocessing.replace.emails(text, "-Email-")
#     text = re.sub(r"[a-zA-Z0-9_.+-]+ @ [ a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", " -Email- ", text)
#     text = textacy_preprocessing.replace.urls(text, "-URL-")
#     text = somajo_remove_url(text)
#     text = re.sub(" +", " ", "".join(x if x.isprintable() or x in string.whitespace else " " for x in text))
#     return text

def label_address(text):
    addresses = pyap.parse(text, country='US')
    for address in addresses:
        address = address.__repr__()
        match = re.search(address, text)
        start, end =match.span()
    return start, end, 'ADDRESS'

# def label(text): 
    # lable_email() # input doc text, and return info for lable, (start, end, label='EMAIL')
    # label_url() # input doc text, and return info for lable, (start, end, label='URL')
    # label_address()

@Language.component('access_info')
def access_info(doc):
    # Create an entity Span with label 'EMAIL','URL','ADDRESS'
    doc.ents = [Span(doc, 0, 1, label='EMAIL')] # replace with the label function,
    doc.ents = [Span(doc, 1, 2, label='URL')] 
    print(doc.text)
    return doc

# Add the component to the pipeline
nlp.add_pipe('access_info')

counter = 0
for doc in nlp.pipe(sentences[:10]):
    counter += 1
    print([(ent.text, ent.label_) for ent in doc.ents])
    print(nlp.pipe_names)
