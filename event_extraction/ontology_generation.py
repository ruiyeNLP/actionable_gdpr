# goal: automatically generate ontology words and patterns
# input: initial seed word lists, heuristic linguistic patterns
# output: expanded ontology word lists(???and patterns to activate trigger words)
# from asyncio.windows_events import NULL
# from curses.panel import top_panel
# from json.tool import main
import spacy
from spacy.tokens import Span
from spacy.language import Language
# import pandas as pd
import csv
import pandas as pd
import itertools
from somajo import SoMaJo
import re

class DotDict(dict):
	__getattr__ = dict.get
    # __setattr__ = dict.__setitem__
    # __delattr__ = dict.__delitem__

'''complex event pattern'''
class EventsExtraction:
	def __init__(self):
		self.ontoDict = {
			'rightVerbs': ['exercise', 'lodge', 'delete', 'access', 'correct', 'object','ask','correct','limit'],
			'rightNouns': ['right','copy'],
			'accessVerbs': ['contact'],
			'accessNouns': ['email'],
			'rightNounsFilter':['setting', 'profile'],
			'accessNounsFilter':['data','information','format','download','request','complaint','use','access','delay','portability','circumstance','accordance','time','controller'],
			'rightVerbsFilter': ['like', 'make', 'be', 'have'],
			'accessVerbsFilter': ['do', 'make'],
			'preps': ['via','by','through','within','at','to','in','with']
		}
		# self.ontoDict = {
		# 	'rightNouns': ['right','complaint','access'],
		# 	'rightVerbs': ['lodge','complain','access','contact'],
		# 	'accessNouns': ['email'],
		# 	'accessVerbs': ['contact'],
		# 	'rightNounsFilter':['setting', 'profile'],
		# 	'accessNounsFilter':['data','information','format','download','request','complaint','use','access','delay','portability','circumstance','accordance','time','controller'],
		# 	'accessVerbsFilter': ['do'],
		# 	'rightVerbsFilter': ['like', 'make', 'be', 'have'],
		# 	'preps': ['via','by','through','within','at','to','in','with']
		# }
		self.ontoDict = DotDict(self.ontoDict)
		self.patternFreq = {}
		self.candidateInSentence = {
			'rightVerbs': [],
			'rightNouns': [],
			'accessVerbs': [],
			'accessNouns': []
		}
		self.candidateInSentence = DotDict(self.candidateInSentence)
		self.resultInSentence = {
			'rightVerbs': [],
			'rightNouns': [],
			'accessVerbs': [],
			'accessNouns': []
		}
		self.resultInSentence = DotDict(self.resultInSentence)
		self.toPrintInSentence = []
		# self.recordFile = open('./output/training_sentences.csv','w')
		# self.recordWriter = csv.writer(self.recordFile)
		self.word_dict = {}
		self.word_dict['sentence'] = []
		self.word_dict['rightVerbs'] = []
		self.word_dict['rightNouns'] = []
		self.word_dict['accessVerbs'] = []
		self.word_dict['accessNouns'] = []

	'''generate ontology with liguistic pattern'''
	def generateOntology(self, doc):
		# main function 
		def analysizeSentence(sent):
			def addToOntoDict():
				self.toPrintInSentence.append('rightVerbs: '+str(self.candidateInSentence.rightVerbs))
				self.toPrintInSentence.append('rightNouns: '+str(self.candidateInSentence.rightNouns))
				self.toPrintInSentence.append('accessVerbs: '+str(self.candidateInSentence.accessVerbs))
				self.toPrintInSentence.append('accessNouns: '+str(self.candidateInSentence.accessNouns))
				self.toPrintInSentence.append('accessNouns: '+str(self.resultInSentence.accessNouns))
				# self.recordWriter.writerow(self.toPrintInSentence[2])
				for rightVerb in self.candidateInSentence.rightVerbs:
					if rightVerb.lower() not in self.ontoDict.rightVerbs:  # change to add lemma 
						self.ontoDict.rightVerbs.append(rightVerb.lower())
				for rightNoun in self.candidateInSentence.rightNouns:
					if rightNoun.lower() not in self.ontoDict.rightNouns: 
						self.ontoDict.rightNouns.append(rightNoun.lower())
				for accessNoun in self.resultInSentence.accessNouns:
					if accessNoun.lower() not in self.ontoDict.accessNouns: 
						self.ontoDict.accessNouns.append(accessNoun.lower())
				for accessVerb in self.candidateInSentence.accessVerbs:
					if accessVerb.lower() not in self.ontoDict.accessVerbs: 
						self.ontoDict.accessVerbs.append(accessVerb.lower())

			def check_rightNoun_pp(token):
				for child in token.children: # ??? to all prep or only the first and reture 
					if child.dep_ == 'prep' and child.text in self.ontoDict.preps:
						self.toPrintInSentence.append('prep: '+child.text+' | '+child.dep_+' | '+child.pos_)
						curtoken = child
						for child in curtoken.children:
							if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ == 'PROPN') and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
								if child.text.lower() not in self.candidateInSentence.accessNouns:
									self.candidateInSentence.accessNouns.append(child.text.lower()) 
								self.toPrintInSentence.append('prep+pobj: '+child.text+' | '+child.dep_+' | '+child.pos_)
								return True
				return False

			def check_rightVerb(rightToken):
				check_access_pp(rightToken)
				for child in rightToken.children:
					if child.dep_ == 'dobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'): # to add or not 
						self.toPrintInSentence.append('rightsVerb+rightsNoun: '+child.text+' | '+child.pos_+' | '+child.dep_)
						# if child.text.lower() not in self.ontoDict.rightNouns and child.text.lower() not in self.candidateInSentence.rightNouns: # enlarge accessverb list of verb + dobj
						if child.text.lower() not in self.candidateInSentence.rightNouns and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.rightNounsFilter):
							self.candidateInSentence.rightNouns.append(child.text.lower()) 
						self.toPrintInSentence.append('rightVerb+perp+pobj check start')
						if check_rightNoun_pp(child):
							# addToOntoDict()
							pass
					if child.dep_ == 'conj' and child.pos_ == 'VERB':
						# if child.lemma_ not in self.ontoDict.rightVerbs and child.lemma_ not in self.candidateInSentence.rightVerbs: 
						if child.lemma_ not in self.candidateInSentence.rightVerbs: 
							self.candidateInSentence.rightVerbs.append(child.lemma_)
						curchild = child
						self.toPrintInSentence.append('conjVerb: '+curchild.lemma_)
						# return pattern_rightVerb_pp(curchild) # to add ''You can control and limit our use of your advertising ID in your device settings .''
						check_access_pp(curchild) 

			def check_have_right(token):
				for child in token.children: 
					if child.dep_ == 'acl' and child.pos_ == 'VERB': # have the right + to + Verb
						curchild = child
						if not curchild.lemma_:
							return
						self.toPrintInSentence.append('have the right+aclVerb: '+child.text+' | '+child.dep_+' | '+child.pos_)
						# if curchild.lemma_ not in self.ontoDict.rightVerbsFilter and curchild.lemma_ not in self.candidateInSentence.rightVerbs:
						if curchild.lemma_ not in self.candidateInSentence.rightVerbs:  
							self.candidateInSentence.rightVerbs.append(curchild.lemma_)
						check_rightVerb(curchild)
				return

			def check_rightVerb_rootVerb_accessVerb(rightToken):
				if root == rightToken:
					# check_access_pp(rightToken)
					self.toPrintInSentence.append('this target sentence is analysed ')
					return
				# if  rightToken.dep_ == 'advcl' and (rightToken.head == root or (rightToken.head != root and rightToken.head.head == root)):
				if  rightToken.head == root: 
					if any(accessVerb in root.lemma_ for accessVerb in self.ontoDict.accessVerbs): # what if root verb is unfound access verb
						self.toPrintInSentence.append('rootverb '+root.text+' | '+root.dep_+' | '+root.pos_)
						check_access_pp(root)
						self.toPrintInSentence.append('this target sentence is analysed ')
						return

					for child in root.children:
						if child.pos_ == 'VERB' and any(accessVerb in child.lemma_ for accessVerb in self.ontoDict.accessVerbs):
							check_access_pp(child)
							self.toPrintInSentence.append('this target sentence is analysed ')
							return

			def check_rightNoun_Verb(token):
				# self.toPrintInSentence.append('Verb+rightNoun: '+token.head.text+' | '+token.head.dep_+' | '+token.head.pos_)
				# return token.head
				if token.head.lemma_ not in self.ontoDict.rightVerbsFilter and token.head.lemma_ not in self.candidateInSentence.rightVerbs: 
					self.candidateInSentence.rightVerbs.append(token.head.lemma_)
					self.toPrintInSentence.append('rightVerb+rightNoun: '+token.head.text+' | '+token.head.dep_+' | '+token.head.pos_)
				return token.head

			def check_access_pp(accessVerbToken):
				accessNoun_accessVerb_dobj = []
				accessNoun_accessVerb_prep_pojb = []
				accessNoun_accessVerb_prep_prep_pobj = []
				for child in accessVerbToken.children:
					self.toPrintInSentence.append('accessVerb: '+accessVerbToken.text+' | '+accessVerbToken.dep_+' | '+accessVerbToken.pos_)
					# if child.dep_ == 'dobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN') and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
					# 	self.toPrintInSentence.append('accessverb+dobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
					# 	accessNoun_accessVerb_dobj.append(child.text)
					# 	curchild = child
					# 	for child in curchild.children:
					# 		if child.dep_ == 'conj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN') and not all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
					# 			self.toPrintInSentence.append('accessverb+dobj+conj: '+child.text+' | '+child.pos_+' | '+child.dep_)
					# 			accessNoun_accessVerb_dobj.append(child.text)
					if child.dep_ == 'prep' and child.text in self.ontoDict.preps:# and child.text != 'to': # go down through the tree and find 'via' + pobj
						self.toPrintInSentence.append('accessverb+prep: '+child.text+' | '+child.pos_+' | '+child.dep_)
						curchild = child
						for child in curchild.children:
							if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN' or child.pos_ =='PUNCT') and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
								self.toPrintInSentence.append('accessverb+prep+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
								accessNoun_accessVerb_prep_pojb.append(child.text)
							if child.dep_ == 'pcomp' and child.pos_ == 'VERB':
								# if child.lemma_ not in self.ontoDict.accessVerbs and child.lemma_ not in self.candidateInSentence.accessVerbs:
								if child.lemma_ not in self.candidateInSentence.accessVerbs:
									self.candidateInSentence.accessVerbs.append(child.lemma_)
								self.toPrintInSentence.append('accessverb+prep+pcomp'+child.text+' | '+child.pos_+' | '+child.dep_)
								curchild = child
								for child in curchild.children:
									if child.dep_ == 'dobj' and child.pos_ == 'NOUN' and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
										self.toPrintInSentence.append('accessverb+prep+pcomp+dobj'+child.text+' | '+child.pos_+' | '+child.dep_)
										accessNoun_accessVerb_prep_pojb.append(child.text)
					if child.dep_ == 'prep' and child.text not in self.ontoDict.preps: # go down through the tree and find 'via' + pobj
						self.toPrintInSentence.append('accessverb+prep(not via): '+child.text+' | '+child.pos_+' | '+child.dep_)
						curchild = child
						for child in curchild.children:
							self.toPrintInSentence.append('accessverb+prep(not via)+prep: '+child.text+' | '+child.pos_+' | '+child.dep_)
							if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN' or child.ent_type_ == 'EMAIL' or child.ent_type_ == 'URL'):
								self.toPrintInSentence.append('accessverb+prep(not via)+prep+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
								ppchild = child 								
								childCounter = 0
								for child in ppchild.children:
									childCounter += 1
									self.toPrintInSentence.append(child.text)
									if child.dep_ == 'prep' and child.text in self.ontoDict.preps:
										self.toPrintInSentence.append('accessverb+prep(not via)+prep+pobj+via: '+child.text+' | '+child.pos_+' | '+child.dep_)
										curchild = child
										for child in curchild.children:
											if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN' or child.ent_type_ == 'EMAIL' or child.ent_type_ == 'URL') and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
												self.toPrintInSentence.append('accessverb+prep(not via)+prep+pobj+via+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
												accessNoun_accessVerb_prep_prep_pobj.append(child.text)
								if childCounter == 0:
									accessNoun_accessVerb_prep_prep_pobj.append(ppchild.text)

				self.toPrintInSentence.append('accessNoun_accessVerb_dobj: '+' | '.join(accessNoun_accessVerb_dobj))
				self.toPrintInSentence.append('accessNoun_accessVerb_prep_pojb: '+' | '.join(accessNoun_accessVerb_prep_pojb))
				self.toPrintInSentence.append('accessNoun_accessVerb_prep_pojb: '+' | '.join(accessNoun_accessVerb_prep_prep_pobj))
				if not accessNoun_accessVerb_dobj and not accessNoun_accessVerb_prep_pojb and not accessNoun_accessVerb_prep_prep_pobj:
					return
				for noun in accessNoun_accessVerb_prep_pojb:
					if noun.lower() not in self.candidateInSentence.accessNouns:
						self.candidateInSentence.accessNouns.append(noun.lower())
				for noun in accessNoun_accessVerb_dobj:
					if noun.lower() not in self.candidateInSentence.accessNouns:
						self.candidateInSentence.accessNouns.append(noun.lower())
				for noun in accessNoun_accessVerb_prep_prep_pobj:
					if noun.lower() not in self.candidateInSentence.accessNouns:
						self.candidateInSentence.accessNouns.append(noun.lower())
				
				self.toPrintInSentence.append('this target sentence is analysed ')
				# addToOntoDict()
				


			# for ent in doc.ents:
			# 	if ent.label_ == 'EMAIL' or ent.label_ == 'URL':
			# 		self.candidateInSentence.accessNouns.append(ent.text)
 			
			def is_right_related_sentence(sent):
				tokens = []
				for token in sent:
					if token.pos_ == 'VERB'and any(rightVerb in token.lemma_ for rightVerb in self.ontoDict.rightVerbs):
						if token not in tokens:
							tokens.append(token)
				for token in sent:
					if token.pos_ == 'NOUN' and any(rightNoun in token.lemma_ for rightNoun in self.ontoDict.rightNouns):
						if token not in tokens:
							tokens.append(token) 
				return tokens

			# entry point for the function 
			rightTokens = is_right_related_sentence(sent)
			self.toPrintInSentence.append('rightTokens: '+str(rightTokens))
			if not rightTokens:
				self.toPrintInSentence.append('it is not a right-related sentence')
				self.word_dict['accessNouns'].append('NaN')
				self.word_dict['rightNouns'].append('NaN')
				self.word_dict['rightVerbs'].append('NaN')
				self.word_dict['accessVerbs'].append('NaN')
				return 			

			for rightToken in rightTokens:
				if rightToken.pos_ == 'VERB':
					self.toPrintInSentence.append('trigger rightVerb: '+rightToken.text)
					if rightToken.lemma_ not in self.candidateInSentence.rightVerbs: 
							self.candidateInSentence.rightVerbs.append(rightToken.lemma_)
					check_rightVerb(rightToken) 

				elif rightToken.pos_ == 'NOUN':
					self.toPrintInSentence.append('trigger rightNoun: '+rightToken.text)
					# if rightToken.text.lower() not in self.ontoDict.rightNouns and rightToken.text.lower() not in self.candidateInSentence.rightNouns: # enlarge accessverb list of verb + dobj
					if rightToken.text.lower() not in self.candidateInSentence.rightNouns and all(filterWord not in rightToken.lemma_ for filterWord in self.ontoDict.rightNounsFilter):
							self.candidateInSentence.rightNouns.append(rightToken.text.lower()) 
					check_rightNoun_pp(rightToken)

				else:
					self.toPrintInSentence.append('it is not a right-related sentence')
					self.word_dict['accessNouns'].append('NaN')
					self.word_dict['rightNouns'].append('NaN')
					self.word_dict['rightVerbs'].append('NaN')
					self.word_dict['accessVerbs'].append('NaN')
					return 

				root = [token for token in sent if token.head == token][0]
				if root.pos_ != 'VERB':
					self.toPrintInSentence.append('trigger rightNoun: '+rightToken.text)
					self.word_dict['accessNouns'].append('NaN')
					self.word_dict['rightNouns'].append('NaN')
					self.word_dict['rightVerbs'].append('NaN')
					self.word_dict['accessVerbs'].append('NaN')
					return
				if rightToken.pos_ == 'VERB':
					check_rightVerb_rootVerb_accessVerb(rightToken)

				elif rightToken.pos_ == 'NOUN': 
					if rightToken.lemma_ == 'right' and rightToken.dep_ == 'dobj' and rightToken.head.text == 'have': # have the right + ... 
						check_have_right(rightToken)
						self.toPrintInSentence.append('this target sentence is analysed ')
					if rightToken.dep_ == 'dobj' and rightToken.head.pos_ == 'VERB' and rightToken.head.text != 'have':
						root = [token for token in sent if token.head == token][0]
						rightToken = check_rightNoun_Verb(rightToken)
						check_rightVerb_rootVerb_accessVerb(rightToken)
					if not (rightToken.dep_ == 'dobj' and token.head.pos_ == 'VERB'): 
						mainVerbToken = root
						check_rightNoun_Verb(mainVerbToken)
			# addToOntoDict()
			 
			


			if self.candidateInSentence.accessNouns:	
				self.resultInSentence.accessNouns = []	
				for noun in self.candidateInSentence.accessNouns:
					if not any(filter in noun for filter in self.ontoDict.accessNounsFilter):
						self.resultInSentence.accessNouns.append(noun)
				if self.resultInSentence.accessNouns: 
					self.word_dict['accessNouns'].append(self.resultInSentence.accessNouns)
					addToOntoDict()
				else:
					self.word_dict['accessNouns'].append('NaN')
					self.word_dict['rightNouns'].append('NaN')
					self.word_dict['rightVerbs'].append('NaN')
					self.word_dict['accessVerbs'].append('NaN')
					return
			else:
				self.word_dict['accessNouns'].append('NaN')
				self.word_dict['rightNouns'].append('NaN')
				self.word_dict['rightVerbs'].append('NaN')
				self.word_dict['accessVerbs'].append('NaN')
				return 

			if self.candidateInSentence.rightVerbs:		
				self.word_dict['rightVerbs'].append(self.candidateInSentence.rightVerbs)
			else:
				self.word_dict['rightVerbs'].append('NaN')

			if self.candidateInSentence.rightNouns:		
				self.word_dict['rightNouns'].append(self.candidateInSentence.rightNouns)
			else:
				self.word_dict['rightNouns'].append('NaN')

			if self.candidateInSentence.accessVerbs:		
				self.word_dict['accessVerbs'].append(self.candidateInSentence.accessVerbs)	
			else:
				self.word_dict['accessVerbs'].append('NaN')

		# entry point 
		self.candidateInSentence.rightVerbs, self.candidateInSentence.rightNouns, self.candidateInSentence.accessVerbs, self.candidateInSentence.accessNouns, self.toPrintInSentence = ([] for i in range(5))		
		with doc.retokenize() as retokenizer:
			for chunk in doc.noun_chunks:
				retokenizer.merge(chunk, attrs={'LEMMA': chunk.root.lemma_, 'TAG':chunk.root.tag_, 'TEXT': chunk.root.text})
		self.toPrintInSentence.append('**************************************')
		self.toPrintInSentence.append('*********** analyse start ************')
		self.toPrintInSentence.append(doc)

		for token in doc:
			self.toPrintInSentence.append(token.text+'\t'+token.lemma_+'\t'+token.pos_+'\t'+token.dep_+'\t'+token.head.text)
		analysizeSentence(doc)
		# for string in self.toPrintInSentence:
		# 	print(string)

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

if __name__ == '__main__':

	nlp = spacy.load('en_core_web_lg')

	# add pipeline 'access' to spacy pipeline 
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
	
	somajo_tokenizer = SoMaJo("en_PTB", split_sentences=False)
	nlp.add_pipe('access')
	print(nlp.pipe_names)

	extractor = EventsExtraction()
	# # preprpcess sentences 
	# sentences = []
	# ema = r"[a-zA-Z0-9_.+-]+ @ [ a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
	# inputFilename = './input/user_rights_data_10.tsv'
	# outputFilename = './output/'+str(inputFilename).split('/')[-1].split('.')[0]+'_result'+'.tsv'
	# with open(inputFilename) as csvfile:
	# 	reader = csv.reader(csvfile,delimiter='\t')
	# 	for row in reader:
	# 		email_without_whitespace = "".join(re.findall(ema,row[1])).replace(" ","") 
	# 		sentence = re.sub(ema, email_without_whitespace, row[1]) # delete whitespace for email address 
	# 		sentences.append(sentence)	

	# # sentences = [
	# # 	"? Access : You may access the Personal Data we hold about you at any time via your Account or by contacting us directly .",
	# # ]

	# counter = 0
	# for doc in nlp.pipe(sentences):
	# 	extractor.word_dict['sentence'].append(sentences[counter])
	# 	extractor.generateOntology(doc)
	# 	# print([(ent.text, ent.label_) for ent in doc.ents])
	# 	counter += 1

	# print('rightNouns: ', len(extractor.ontoDict.rightNouns))
	# print(extractor.ontoDict.rightNouns)
	# print('rightVerbs: ', len(extractor.ontoDict.rightVerbs))
	# print(extractor.ontoDict.rightVerbs)
	# print('accessNouns: ', len(extractor.ontoDict.accessNouns))
	# print(extractor.ontoDict.accessNouns)
	# print('accessVerbs: ', len(extractor.ontoDict.accessVerbs))
	# print(extractor.ontoDict.accessVerbs)



	# preprpcess sentences 
	sentences = []
	ema = r"[a-zA-Z0-9_.+-]+ @ [ a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
	inputFilename = './input/user_rights_data_10.tsv'
	outputFilename = './output/'+str(inputFilename).split('/')[-1].split('.')[0]+'_result'+'.tsv'
	with open(inputFilename) as csvfile:
		reader = csv.reader(csvfile,delimiter='\t')
		for row in reader:
			email_without_whitespace = "".join(re.findall(ema,row[1])).replace(" ","") 
			sentence = re.sub(ema, email_without_whitespace, row[1]) # delete whitespace for email address 
			sentences.append(sentence)
	# iterations 
	iterNum = 10
	lenRightNounLastRound,lenRightVerbLastRound,lenAccessNounLastRound,lenAccessVerbLastRound =  (0 for i in range(4))
	for i in range(iterNum):
		counter = 0
		extractor.word_dict.clear()
		extractor.word_dict = {}
		extractor.word_dict['sentence'] = []
		extractor.word_dict['rightVerbs'] = []
		extractor.word_dict['rightNouns'] = []
		extractor.word_dict['accessVerbs'] = []
		extractor.word_dict['accessNouns'] = []
		for doc in nlp.pipe(sentences):
			extractor.word_dict['sentence'].append(sentences[counter])
			extractor.generateOntology(doc)
			# print([(ent.text, ent.label_) for ent in doc.ents])
			counter += 1
		
		print('iteration: ', i)
		print('rightNouns: ', len(extractor.ontoDict.rightNouns))
		print(extractor.ontoDict.rightNouns)
		print('rightVerbs: ', len(extractor.ontoDict.rightVerbs))
		print(extractor.ontoDict.rightVerbs)
		print('accessNouns: ', len(extractor.ontoDict.accessNouns))
		print(extractor.ontoDict.accessNouns)
		print('accessVerbs: ', len(extractor.ontoDict.accessVerbs))
		print(extractor.ontoDict.accessVerbs)

		lenRightNounThisRound = len(extractor.ontoDict.rightNouns)
		lenRightVerbThisRound = len(extractor.ontoDict.rightVerbs)
		lenAccessNounThisRound = len(extractor.ontoDict.accessNouns)
		lenAccessVerbThisRound = len(extractor.ontoDict.accessVerbs)
		if lenRightNounThisRound == lenRightNounLastRound and lenRightVerbThisRound == lenRightVerbLastRound and lenAccessNounThisRound == lenAccessNounLastRound and lenAccessVerbThisRound == lenAccessVerbLastRound:
			break
		lenRightNounLastRound = lenRightNounThisRound
		lenRightVerbLastRound = lenRightVerbThisRound
		lenAccessNounLastRound = lenAccessNounThisRound
		lenAccessVerbLastRound = lenAccessVerbThisRound
	print(len(extractor.word_dict['sentence'] ),len(extractor.word_dict['rightVerbs']),len(extractor.word_dict['accessVerbs']),len(extractor.word_dict['accessNouns']))
	# print(extractor.word_dict)
	df = pd.DataFrame(extractor.word_dict)
	df.to_csv(outputFilename, sep='\t', encoding='utf-8',index=False) 
