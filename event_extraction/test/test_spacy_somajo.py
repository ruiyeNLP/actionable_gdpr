'''
add 'access' pipeline to spacy models 
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
ema = r"[a-zA-Z0-9_.+-]+ @ [ a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
with open('./input/user_rights_sentences_dedup_test_output.tsv') as csvfile:
    reader = csv.reader(csvfile,delimiter='\t')
    for row in reader:
        email_without_whitespace = "".join(re.findall(ema,row[1])).replace(" ","")
        sentence = re.sub(ema, email_without_whitespace, row[1])
        sentences.append(sentence)	

def somajo_label_url(text): # label_email
    match = re.search('-URL-', text)
    if match:
        return '-URL-'

    text_as_list = list()
    text_as_list.append(text)
    tokenized_text = somajo_tokenizer.tokenize_text(text_as_list)
    for dummy_tokenized_text in tokenized_text:
        for token in dummy_tokenized_text:
            if token.token_class == "URL":
                match = re.search(token.text, text)
                if match:
                    return token.text
                else:
                    print('error') 
    return 

def somajo_label_email(text): # label_email
    match = re.search('-Email-', text)
    if match:
        return '-Email-'
     
    text_as_list = list()
    text_as_list.append(text)
    tokenized_text = somajo_tokenizer.tokenize_text(text_as_list)
    for dummy_tokenized_text in tokenized_text:
        for token in dummy_tokenized_text:
            if token.token_class == "email_address":
                match = re.search(token.text, text)
                if match:
                    return token.text
                else:
                    print('error')        
    return 

# def label_address(text):
#     addresses = pyap.parse(text, country='US')
#     for address in addresses:
#         address = address.__repr__()
#     return addresses

@Language.component('access')
def access_info(doc):
    # Create an entity Span with label 'EMAIL','URL','ADDRESS'     
    if somajo_label_email(doc.text):
        email_token = somajo_label_email(doc.text)
        for token in doc:
            if token.text == email_token:
                doc.ents = [Span(doc, token.i, token.i+1, label='EMAIL')] # replace with the label function,
    
    if somajo_label_url(doc.text):
        url_token = somajo_label_url(doc.text)
        for token in doc:
            if token.text == url_token:
                doc.ents = [Span(doc, token.i, token.i+1, label='URL')]

    return doc

# Add the component to the pipeline
nlp.add_pipe('access')

counter_email = 0
counter_url = 0
for doc in nlp.pipe(sentences):
    print([(ent.text, ent.label_) for ent in doc.ents])
    for ent in doc.ents:
        if ent.label_ == 'EMAIL':
            counter_email += 1
        if ent.label_ == 'URL':
            counter_url += 1

print('total numbers of emails labeled by somajo: ', counter_email)
print('total numbers of urls labeled by somajo: ', counter_url)

    
