# goal: feature engineering to find "keywords" for accessNoun, rightNoun, accessVerb, rightVerb
import spacy
import csv
from sklearn.feature_extraction.text import CountVectorizer 
from sklearn.feature_extraction.text import TfidfVectorizer 
from spacy.lang.en.stop_words import STOP_WORDS
import string 
from sklearn.decomposition import LatentDirichletAllocation, NMF, TruncatedSVD
import pandas as pd
import os

nlp = spacy.load("en_core_web_lg")

def analyse(file):
    # load tsv file as corpus
    corpus = []
    with open(file) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:        
            row2string = ''.join(str(e) for e in row)
            rowSplited = row2string.split('\t')
            parapraph = rowSplited[1]
            corpus.append(parapraph)

    # preprocess, tokenize, stem, remove stopwords, remove punc, remove digits token(pos)
    punctuations = string.punctuation
    stopwords = list(STOP_WORDS)
    def process_sentences(sentences, corpus, type=None):
        def process_words (doc, type=None):
            sentence = doc
            if type ==  'NOUN':
                sentence = [ word for word in sentence if word.pos_ == 'NOUN' ]
            elif type == 'VERB':
                sentence = [ word for word in sentence if word.pos_ == 'VERB' ]
            else:
                sentence = [ word for word in sentence if not word.is_digit ]
            sentence = [ word.lemma_.lower().strip() if word.lemma_ != "-PRON-" else word.lower_ for word in sentence ]
            sentence = [ word for word in sentence if word not in stopwords and word not in punctuations ]
            sentence = " ".join([i for i in sentence])
            return sentence 
        for doc in nlp.pipe(corpus):                       
            sentence = process_words(doc, type)
            sentences.append(sentence)
        return sentences

    # word count
    def word_count( corpus,type=None,top_n=20,ngram=1):
        sentences = []
        sentences = process_sentences(sentences, corpus, type)
        ngram_vectorizer = CountVectorizer(ngram_range=(ngram,ngram))
        ngram_matrix = ngram_vectorizer.fit_transform(sentences)
        print(str(type)+': '+str(ngram) + '-gram')
        words = sorted(list(zip(ngram_vectorizer.get_feature_names_out(), 
                                                ngram_matrix.sum(0).getA1())),
                                    key=lambda x: x[1], reverse=True)[:top_n]
        key =  'word_count'
        if key not in word_dict:
            word_dict[key] = []
        for word in words:
            word_dict[key].append(word[0])      
    word_dict = {}
    word_count(corpus)
    word_count(corpus, type='NOUN')
    word_count(corpus, type='VERB')

    # tf-idf for weights to find similar words; 
    def tfidf(corpus,type=None,top_n=20):
        sentences = []
        sentences = process_sentences(sentences, corpus, type)
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(sentences)
        print('tf-idf')
        words = sorted(list(zip(tfidf_vectorizer.get_feature_names_out(), 
                                                    tfidf_matrix.sum(0).getA1())), 
                                        key=lambda x: x[1], reverse=True)[:top_n]
        key =  'tfidf'
        if key not in word_dict:
            word_dict[key] = []
        for word in words:
            word_dict[key].append(word[0])        
    tfidf(corpus)
    tfidf(corpus, type='NOUN')
    tfidf(corpus, type='VERB')

    # topic modeling -- get top words in each topic 
    def topic_modeling(corpus,colname,type=None,top_n=20):
        sentences = []
        sentences = process_sentences(sentences, corpus, type)    
        def selected_topics(model, vectorizer):
            for idx, topic in enumerate(model.components_):
                words = [(vectorizer.get_feature_names_out()[i], topic[i])
                                for i in topic.argsort()[:-top_n - 1:-1]]
                key =  colname+'Topic' + str(idx+1)
                if key not in word_dict:
                    word_dict[key] = []
                for i in words:
                    word_dict[key].append(i[0])
        NUM_TOPICS = 10
        vectorizer = CountVectorizer(ngram_range=(1,1))
        data_vectorized = vectorizer.fit_transform(sentences)
        # Latent Dirichlet Allocation Model
        lda = LatentDirichletAllocation(n_components=NUM_TOPICS, max_iter=10, learning_method='online',verbose=True)
        data_lda = lda.fit_transform(data_vectorized)
        print("LDA Model")
        selected_topics(lda, vectorizer)

    topic_modeling(corpus, colname='lda_')
    topic_modeling(corpus, colname='lda_', type='NOUN')
    topic_modeling(corpus, colname='lda_', type='VERB')

    df = pd.DataFrame(word_dict)
    filename = './output/'+str(file).split('/')[-1].split('.')[0]+'_keywords'+'.csv'
    df.to_csv(filename, sep='\t', encoding='utf-8') 

file = "./input/contact_details.tsv"
analyse(file)
file = './input/user_rights_sentences.tsv'
analyse(file)
