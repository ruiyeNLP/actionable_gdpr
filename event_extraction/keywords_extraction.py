import spacy
import csv
import string
import pandas as pd
import re
import sys
import os
import string
import traceback
import datetime
from collections import Counter
import yake
import spacy
import pke
import nltk
from tqdm import tqdm
import textacy
from textacy.extract import keyterms
from textacy import preprocessing as textacy_preprocessing
from keybert import KeyBERT
import pandas as pd
from pandas.core.common import flatten
import spacy
from somajo import SoMaJo
from joblib import Parallel, delayed


spacy_languages = {"en": "en_core_web_trf"}
somajo_tokenizer = SoMaJo("en_PTB", split_sentences=False)


def analyse(filepath):

    print("Start time: ", str(datetime.datetime.now()))

    def somajo_remove_url(text):
        """
        A customized function to remove e-mails which have whitespaces
        and URLs which were apparently not cleaned from the corpus.
        """
        out = []
        text_as_list = list()
        text_as_list.append(text)
        tokenized_text = somajo_tokenizer.tokenize_text(text_as_list)
        for dummy_tokenized_text in tokenized_text:
            for token in dummy_tokenized_text:
                if token.token_class == "URL":
                    out.append("-URL-")
                elif token.original_spelling is not None:
                    out.append(token.original_spelling)
                else:
                    out.append(token.text)
                if token.space_after:
                    out.append(" ")
        return "".join(out)


    def text_preprocessing(text):
        text = textacy_preprocessing.normalize.hyphenated_words(text)
        text = textacy_preprocessing.normalize.whitespace(text)
        text = textacy_preprocessing.replace.emails(text, "-Email-")
        text = re.sub(r"[a-zA-Z0-9_.+-]+ @ [ a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", " -Email- ", text)
        text = textacy_preprocessing.replace.urls(text, "-URL-")
        text = somajo_remove_url(text)
        text = re.sub(" +", " ", "".join(x if x.isprintable() or x in string.whitespace else " " for x in text))
        return text


    def spacy_lemmatizer_with_whitespace(docs, language):
        lemmatized_docs = []
        nlp = spacy.load(spacy_languages[language])
        for doc in nlp.pipe(tqdm(docs, total=len(docs), unit="doc", desc="Spacy lemmatizer"), n_process=1):
            lemmatized_docs.append("".join([token.lemma_ + token.whitespace_ for token in doc]))
        return lemmatized_docs


    def pke_multipartiterank(text, language, pos):
        extractor = pke.unsupervised.MultipartiteRank()
        try:
            extractor.load_document(input=text, language=language)
            extractor.candidate_selection(pos={pos})
            extractor.candidate_weighting()
            keyphrases = extractor.get_n_best(n=20)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            sys.exit()
        return list_of_keyphrases


    def textacy_textrank(text, language, pos):
        try:
            doc = textacy.make_spacy_doc(text, lang=spacy_languages[language])
            keyphrases = keyterms.textrank(doc, normalize="lemma", topn=20, include_pos=pos, window_size=2, edge_weighting="binary", position_bias=False)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            sys.exit()
        return list_of_keyphrases


    def textacy_singlerank(text, language, pos):
        try:
            doc = textacy.make_spacy_doc(text, lang=spacy_languages[language])
            keyphrases = keyterms.textrank(doc, normalize="lemma", topn=20, include_pos=pos, window_size=10, edge_weighting="count", position_bias=False)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            sys.exit()
        return list_of_keyphrases


    def textacy_positionrank(text, language, pos):
        try:
            doc = textacy.make_spacy_doc(text, lang=spacy_languages[language])
            keyphrases = keyterms.textrank(doc, normalize="lemma", topn=20, include_pos=pos, window_size=10, edge_weighting="count", position_bias=True)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            sys.exit()
        return list_of_keyphrases


    def textacy_yake(text, language, pos):
        try:
            doc = textacy.make_spacy_doc(text, lang=spacy_languages[language])
            keyphrases = keyterms.yake(doc, ngrams=1, normalize="lemma", topn=20, include_pos=pos)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            print(text)
            list_of_keyphrases = []
        return list_of_keyphrases


    def textacy_scake(text, language, pos):
        try:
            doc = textacy.make_spacy_doc(text, lang=spacy_languages[language])
            keyphrases = keyterms.scake(doc, normalize="lemma", topn=20, include_pos=pos)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            sys.exit()
        return list_of_keyphrases


    def textacy_sgrank(text, language, pos):
        try:
            doc = textacy.make_spacy_doc(text, lang=spacy_languages[language])
            keyphrases = keyterms.sgrank(doc, ngrams=1, normalize="lemma", topn=20, include_pos=pos)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            list_of_keyphrases = []
        return list_of_keyphrases


    def keybert(text, language):
        try:
            if language == "en":
                kw_model = KeyBERT(model="all-mpnet-base-v2")
            else:
                kw_model = KeyBERT(model="paraphrase-multilingual-mpnet-base-v2")
            keyphrases = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 1), top_n=20)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            sys.exit()
        return list_of_keyphrases


    def postprocessing(list_of_lists_of_keywords, number_of_documents, pos=None, name=None):
        """
        The keywords are weighted over the number of extractors and number of documents
        For KeyBert, only weighting over the number of documents is performed.
        """
        list_of_lists_of_keywords = [keyword.lower() for list_of_keywords in list_of_lists_of_keywords for keyword in list_of_keywords]
        keyword_freq_dict = dict(nltk.FreqDist(flatten(list_of_lists_of_keywords)))
        if pos:
            keyword_freq_dict = {keyword:(freq/(number_of_documents*7)) for (keyword, freq) in keyword_freq_dict.items()}
            df_keywords = pd.DataFrame(keyword_freq_dict.items(), columns=[pos, pos + "_" + "weight"])
            df_keywords.sort_values(by=pos + "_" + "weight", ascending=False, inplace=True)
        elif name=="KeyBert":
            keyword_freq_dict = {keyword:(freq/number_of_documents) for (keyword, freq) in keyword_freq_dict.items()}
            df_keywords = pd.DataFrame(keyword_freq_dict.items(), columns=[name, name + "_" + "weight"])
            df_keywords.sort_values(by=name + "_" + "weight", ascending=False, inplace=True)
        print(df_keywords.head())
        return df_keywords


    def load_texts(filepath):
        list_of_texts = []
        with open(filepath) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                row2string = ''.join(str(e) for e in row)
                rowSplited = row2string.split('\t')
                parapraph = rowSplited[1]
                list_of_texts.append(parapraph)
        return list_of_texts


    ### Entry point ###
    language = "en"
    include_pos = ['NOUN', "PROPN", "VERB"]
    keyphrase_extractors = {
        "KeyBert": keybert,
        "TextRank": textacy_textrank,
        "SingleRank": textacy_singlerank,
        "PositionRank": textacy_positionrank,
        "MultipartiteRank": pke_multipartiterank,
        "Yake": textacy_yake,
        "sCAKE": textacy_scake,
        "SGRank": textacy_sgrank
    }

    # Depending on whether the library can extract keyterms based on pos or not, the appropriate list is passed to the function
    groups_of_algorithms = {"bert":["KeyBert"],
            "notBert":["TextRank", "SingleRank", "PositionRank", "MultipartiteRank", "Yake", "sCAKE", "SGRank"]}

    # load tsv file as corpus
    list_of_texts = load_texts(filepath)
    list_of_texts = [text_preprocessing(text) for text in list_of_texts]
    list_of_lemmatized_texts = spacy_lemmatizer_with_whitespace(list_of_texts, language)

    # list_of_df_keywords = []
    for pos in include_pos:
        list_of_lists_of_keywords = []
        for name, extractor in keyphrase_extractors.items():
            if name in groups_of_algorithms["notBert"]:
                print("Extracting keyphrases using " + name + " for " + pos)
                # list of lists per extractor
                if name == "MultipartiteRank":
                    list_of_lists_of_keywords.append(flatten(Parallel(n_jobs=1)(
                        delayed(extractor)(text, language, pos) for text in tqdm(list_of_lemmatized_texts, position=1))))
                else:
                    list_of_lists_of_keywords.append(flatten(Parallel(n_jobs=1)(
                        delayed(extractor)(text, language, pos) for text in tqdm(list_of_texts, position=1))))
        df_keywords = postprocessing(list_of_lists_of_keywords, len(list_of_texts), pos, None)
        output_filename = './output/' + str(filepath).split('/')[-1].split('.')[0]+'_keywords.xlsx'
        if os.path.exists(output_filename):
            with pd.ExcelWriter(output_filename, mode='a') as writer:
                df_keywords.to_excel(writer, sheet_name=pos, encoding='utf-8', index=False)
        else:
            with pd.ExcelWriter(output_filename, mode='w') as writer:
                df_keywords.to_excel(writer, sheet_name=pos, encoding='utf-8', index=False)

    # keyphrase extraction for keybert is commented out as the part-of-speech tags cannot be specificied during the extraction process
    # print("Extracting keyphrases using KeyBert")
    # list_of_lists_of_keywords = Parallel(n_jobs=1)(
    # delayed(keybert)(text, language) for text in tqdm(list_of_lemmatized_texts, position=1))
    # df_keywords = postprocessing(list_of_lists_of_keywords, len(list_of_lemmatized_texts), None,  "KeyBert")
    # list_of_df_keywords.append(df_keywords)


if __name__ == '__main__':
    for i in range(5, 11):
        filepath = './input/user_rights_data_' + str(i) + '_sentences_deduplicated.tsv'
        analyse(filepath)
