# goal: automatically generate ontology words and patterns
# input: initial seed word lists, heuristic linguistic patterns
# output: expanded ontology word lists(???and patterns to activate trigger words)
from curses.panel import top_panel
from json.tool import main
import spacy
# import pandas as pd
import csv
import pandas as pd
import itertools

class DotDict(dict):
	__getattr__ = dict.get
    # __setattr__ = dict.__setitem__
    # __delattr__ = dict.__delitem__

'''complex event pattern'''
class EventsExtraction:
	def __init__(self):
		#self.parser = nlpModel
		self.ontoDict = {
			'rightVerbs': ['exercise', 'lodge', 'delete', 'access', 'correct', 'object','ask','correct','limit'],
			'rightVerbsFilter': ['like', 'make', 'be'],
			'rightNouns': ['right','copy'],
			'accessVerbs': ['contact'],
			'accessNouns': ['email'],
			'accessNounsFilter':['right','time','complaint','use','delay','portability','circumstance','accordance'],
			'accessVerbsFilter': ['do'],
			'preps': ['via','by','through','within','at','to','in','with']
		}
		self.ontoDict = DotDict(self.ontoDict)
		self.patternFreq = {}
		self.candidateInSentence = {
			'rightVerbs': [],
			'rightNouns': [],
			'accessVerbs': [],
			'accessNouns': []
		}
		self.candidateInSentence = DotDict(self.candidateInSentence)
		self.toPrintInSentence = []
		self.recordFile = open('./output/training_sentences.csv','w')
		self.recordWriter = csv.writer(self.recordFile)
		self.word_dict = {}
		self.word_dict['sentence'] = []
		self.word_dict['accessNouns'] = []
		self.word_dict['rightNouns'] = []
		self.word_dict['rightVerbs'] = []
		self.word_dict['accessVerbs'] = []

	'''generate ontology with liguistic pattern'''
	def generateOntology(self, doc):
		def analysizeSentence(sent):
			def addToOntoDict():
				self.toPrintInSentence.append('rightVerbs: '+str(self.candidateInSentence.rightVerbs))
				self.toPrintInSentence.append('rightNouns: '+str(self.candidateInSentence.rightNouns))
				self.toPrintInSentence.append('accessVerbs: '+str(self.candidateInSentence.accessVerbs))
				self.toPrintInSentence.append('accessNouns: '+str(self.candidateInSentence.accessNouns))
				self.recordWriter.writerow(self.toPrintInSentence[2])
				for rightVerb in self.candidateInSentence.rightVerbs:
					if rightVerb.lower() not in self.ontoDict.rightVerbs: 
						self.ontoDict.rightVerbs.append(rightVerb.lower())
				for rightNoun in self.candidateInSentence.rightNouns:
					if rightNoun.lower() not in self.ontoDict.rightNouns: 
						self.ontoDict.rightNouns.append(rightNoun.lower())
				for accessNoun in self.candidateInSentence.accessNouns:
					if accessNoun.lower() not in self.ontoDict.accessNouns: 
						self.ontoDict.accessNouns.append(accessNoun.lower())
				for accessVerb in self.candidateInSentence.accessVerbs:
					if accessVerb.lower() not in self.ontoDict.accessVerbs: 
						self.ontoDict.accessVerbs.append(accessVerb.lower())		
							
			def pattern_prep_n(token):
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

			def pattern_aclVerb_dobj_prep_n(token):
				for child in token.children: 
					if child.dep_ == 'acl' and child.pos_ == 'VERB': # have the right + to + Verb
						curchild = child
						self.toPrintInSentence.append('have the right+aclVerb: '+child.text+' | '+child.dep_+' | '+child.pos_)
						if curchild.lemma_ not in self.ontoDict.rightVerbsFilter: 
							self.candidateInSentence.rightVerbs.append(curchild.lemma_)
						for child in curchild.children:
							if child.dep_ == 'dobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
								if child.text.lower() not in self.ontoDict.rightNouns: 
									self.candidateInSentence.rightNouns.append(child.text.lower())	
								self.toPrintInSentence.append('have the right+aclVerb+n: '+child.text+' | '+child.dep_ +' | '+child.pos_)
								self.toPrintInSentence.append('have the right+prep+pobj check start')
								if pattern_prep_n(child):	
									addToOntoDict()					
				return

			def pattern_rightVerb_rightNoun(token):
				if token.head.lemma_ not in self.ontoDict.rightVerbsFilter: 
					self.candidateInSentence.rightVerbs.append(token.head.lemma_)
					self.toPrintInSentence.append('rightVerb+rightNoun: '+token.head.text+' | '+token.head.dep_+' | '+token.head.pos_)
					return token.head
				else:
					return None

			def pattern_Verb_rightNoun(token):
				self.toPrintInSentence.append('Verb+rightNoun: '+token.head.text+' | '+token.head.dep_+' | '+token.head.pos_)
				return token.head

			def lingui_findMainVerb_from_rightVerb(token):
				#self.toPrintInSentence.append('Verb: '+token)
				if token.dep_ == 'ROOT':
					self.toPrintInSentence.append('rightVerb is Root: '+token.text)
					return token
				if token.dep_ == 'advcl':
					self.toPrintInSentence.append('rightVerb is curtoken: '+token.text)
					return token
				if token.dep_ == 'xcomp' and token.head.pos_ == 'VERB' and token.head.dep_ == 'advcl':
					self.toPrintInSentence.append('rightVerb+xcomp+advcl: '+token.head.text)
					return token.head
				else:
					return None
				
			def lingui_findMainVerb(token): # another method is to use token.head.dep_ == 'xcomp':
				curtoken = token.head
				self.toPrintInSentence.append('curtoken: '+curtoken.text+' | '+curtoken.dep_+' | '+curtoken.pos_)
				if not (curtoken.dep_ == 'advcl' and curtoken.pos_ == 'VERB'):
					curtoken = curtoken.head
					self.toPrintInSentence.append('curtoken+rightNoun: '+curtoken.text+' | '+curtoken.dep_+' | '+curtoken.pos_)
					if not (curtoken.dep_ == 'advcl' and curtoken.pos_ == 'VERB'):
						curtoken = curtoken.head
						self.toPrintInSentence.append('curtoken+rightNoun: '+curtoken.text+' | '+curtoken.dep_+' | '+curtoken.pos_)
						if not (curtoken.dep_ == 'advcl' and curtoken.pos_ == 'VERB'):
							curtoken = curtoken.head
							self.toPrintInSentence.append('curtoken+rightNoun: '+curtoken.text+' | '+curtoken.dep_+' | '+curtoken.pos_)
				if not(curtoken.dep_ == 'advcl' and curtoken.pos_ == 'VERB'):
					self.toPrintInSentence.append('no main  verb')
					return 
				else:
					return curtoken

			def lingui_accessVerb_patterns(accessVerbToken):
				accessNoun_accessVerb_dobj = []
				accessNoun_accessVerb_prep_pojb = []
				accessNoun_accessVerb_prep_prep_pobj = []
				for child in accessVerbToken.children:
					self.toPrintInSentence.append('accessVerb: '+child.text+' | '+child.dep_+' | '+child.pos_)
					if child.dep_ == 'dobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN') and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
						self.toPrintInSentence.append('accessverb+dobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
						accessNoun_accessVerb_dobj.append(child.text)
						curchild = child
						for child in curchild.children:
							if child.dep_ == 'conj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN') and not all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
								self.toPrintInSentence.append('accessverb+dobj+conj: '+child.text+' | '+child.pos_+' | '+child.dep_)
								accessNoun_accessVerb_dobj.append(child.text)
					if child.dep_ == 'prep' and child.text in self.ontoDict.preps:# and child.text != 'to': # go down through the tree and find 'via' + pobj
						self.toPrintInSentence.append('accessverb+prep: '+child.text+' | '+child.pos_+' | '+child.dep_)
						curchild = child
						for child in curchild.children:
							if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN' or child.pos_ =='PUNCT') and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
								self.toPrintInSentence.append('accessverb+prep+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
								accessNoun_accessVerb_prep_pojb.append(child.text)
							if child.dep_ == 'pcomp' and child.pos_ == 'VERB':
								if child.lemma_ not in self.ontoDict.accessVerbs:
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
							if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
								self.toPrintInSentence.append('accessverb+prep(not via)+prep+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
								curchild = child 
								for child in curchild.children:
									if child.dep_ == 'prep' and child.text in self.ontoDict.preps:
										self.toPrintInSentence.append('accessverb+prep(not via)+prep+pobj+via: '+child.text+' | '+child.pos_+' | '+child.dep_)
										curchild = child
										for child in curchild.children:
											if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN') and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
												self.toPrintInSentence.append('accessverb+prep(not via)+prep+pobj+via+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
												accessNoun_accessVerb_prep_prep_pobj.append(child.text)
				self.toPrintInSentence.append('accessNoun_accessVerb_dobj: '+' | '.join(accessNoun_accessVerb_dobj))
				self.toPrintInSentence.append('accessNoun_accessVerb_prep_pojb: '+' | '.join(accessNoun_accessVerb_prep_pojb))
				self.toPrintInSentence.append('accessNoun_accessVerb_prep_pojb: '+' | '.join(accessNoun_accessVerb_prep_prep_pobj))
				if not accessNoun_accessVerb_dobj and not accessNoun_accessVerb_prep_pojb and not accessNoun_accessVerb_prep_prep_pobj:
					return
				for noun in accessNoun_accessVerb_prep_pojb:
					if child.text.lower() not in self.candidateInSentence.accessNouns:
						self.candidateInSentence.accessNouns.append(noun.lower())
				for noun in accessNoun_accessVerb_dobj:
					if child.text.lower() not in self.candidateInSentence.accessNouns:
						self.candidateInSentence.accessNouns.append(noun.lower())
				for noun in accessNoun_accessVerb_prep_prep_pobj:
					if child.text.lower() not in self.candidateInSentence.accessNouns:
						self.candidateInSentence.accessNouns.append(noun.lower())
				self.toPrintInSentence.append('this target sentence is analysed ')
				addToOntoDict()

			def checkMainVerb(mainVerbToken):
				print(mainVerbToken.head.text)
				if mainVerbToken.head.pos_ != 'VERB':
					return 
				self.toPrintInSentence.append('mainVerb+accessVerb: '+mainVerbToken.head.text)						
				curtoken = mainVerbToken.head
				lingui_accessVerb_patterns(curtoken)
			
			def pattern_rightVerb_rightNoun_pp(token):
				for child in token.children:
					if child.dep_ == 'dobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
						self.toPrintInSentence.append('rightsVerb+rightsNoun: '+child.text+' | '+child.pos_+' | '+child.dep_)
						if child.text.lower() not in self.ontoDict.rightNouns: # enlarge accessverb list of verb + dobj
							self.candidateInSentence.rightNouns.append(child.text.lower()) 
						self.toPrintInSentence.append('rightVerb+perp+pobj check start')
						if pattern_prep_n(child):
							addToOntoDict()
							return True
				return False

			def pattern_rightVerb_pp(token):
				for child in token.children:
					if child.dep_ == 'prep' and child.text in self.ontoDict.preps and child.text != 'to': 
						self.toPrintInSentence.append('accessverb+prep: '+child.text+' | '+child.pos_+' | '+child.dep_)
						curchild = child
						for child in curchild.children:
							if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN') and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
								self.toPrintInSentence.append('accessverb+prep+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
								if child.lemma_ not in self.ontoDict.accessNouns: 
									self.candidateInSentence.accessNouns.append(child.text.lower())
								return True # ??? or continure & compare all accessNoun candidates
							if child.dep_ == 'pcomp':
								self.toPrintInSentence.append('accessverb+prep+pcomp: '+child.text+' | '+child.pos_+' | '+child.dep_)
								curchild = child
								for child in curchild.children:		
									if child.dep_ == 'prep':
										self.toPrintInSentence.append('accessverb+prep+pcomp+prep: '+child.text+' | '+child.pos_+' | '+child.dep_)
										curchild = child
										for child in curchild.children:
											if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN') and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
												self.toPrintInSentence.append('accessverb+prep+pcomp+prep+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
												if child.lemma_ not in self.ontoDict.accessNouns:  
													self.candidateInSentence.accessNouns.append(child.text.lower())
												return True # ??? or continure & compare all accessNoun candidates
										if child.dep_ == 'dobj':
											self.toPrintInSentence.append('accessverb+prep+pcomp+dobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
											formerchild = child 
											curchild = child
											child_has_acl =False
											for child in curchild.children:
												if child.dep_ == 'acl':
													child_has_acl = True
													self.toPrintInSentence.append('accessverb+prep+pcomp+dobj+acl: '+child.text+' | '+child.pos_+' | '+child.dep_)
													curchild = child
													for child in curchild.children:
														if child.dep_ == 'prep':
															self.toPrintInSentence.append('accessverb+prep+pcomp+dobj+acl+prep: '+child.text+' | '+child.pos_+' | '+child.dep_)
															curchild = child
															for child in curchild.children:
																if child.dep_ == 'pobj' and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter):
																	self.toPrintInSentence.append('accessverb+prep+pcomp+dobj+acl+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
																	if child.lemma_ not in self.ontoDict.accessNouns: # enlarge accessverb list of verb + 
																		self.candidateInSentence.accessNouns.append(child.text.lower())
																	return True # ??? or continure & compare all accessNoun candidates
											if not child_has_acl:
												if formerchild.lemma_ not in self.ontoDict.accessNouns and all(filterWord not in child.lemma_ for filterWord in self.ontoDict.accessNounsFilter): # enlarge accessverb list of verb + 
													self.candidateInSentence.accessNouns.append(formerchild.text.lower())
				return False
			
			def pattern_rightVerb_conjVerb_pp(token):
				for child in token.children:
					if child.dep_ == 'conj' and child.pos_ == 'VERB':
						if child.lemma_ not in self.ontoDict.rightVerbs: 
							self.candidateInSentence.rightVerbs.append(child.lemma_)
						curchild = child
						self.toPrintInSentence.append('conjVerb: '+curchild.lemma_)
						return pattern_rightVerb_pp(curchild) # to add ''You can control and limit our use of your advertising ID in your device settings .''
				return False

			for token in sent:
				if token.pos_ == 'VERB'and any(rightVerb in token.lemma_ for rightVerb in self.ontoDict.rightVerbs):
					self.toPrintInSentence.append("rightsVerb: "+token.text)
					if token.text.lower() not in self.ontoDict.rightVerbs: 
						self.ontoDict.rightVerbs.append(token.text.lower())
					if pattern_rightVerb_rightNoun_pp(token):
						self.toPrintInSentence.append('this target sentence is analysed ')
						return					
					if pattern_rightVerb_pp(token):
						self.toPrintInSentence.append('this target sentence is analysed ')
						addToOntoDict()
						return
					if pattern_rightVerb_conjVerb_pp(token):
						self.toPrintInSentence.append('this target sentence is analysed ')
						addToOntoDict()
						return						
					mainVerbToken = lingui_findMainVerb_from_rightVerb(token)
					if mainVerbToken: 
						self.toPrintInSentence.append('the mainVerbToken is: '+mainVerbToken.text)	
						if mainVerbToken.dep_ == 'advcl' and (mainVerbToken.head.pos_ == 'VERB' or mainVerbToken.head.lemma_ == 'do'): # find rightsacess pattern
							self.toPrintInSentence.append('rightVerb: '+mainVerbToken.text+' accessVerb: '+mainVerbToken.head.lemma_)
							if mainVerbToken.head.lemma_ not in self.ontoDict.accessVerbs and mainVerbToken.head.lemma_ != 'do': # enlarge accessverb list 
								self.candidateInSentence.accessVerbs.append(mainVerbToken.head.lemma_) # ??? not sure
							curtoken = mainVerbToken.head
							lingui_accessVerb_patterns(curtoken)
							self.toPrintInSentence.append('this target sentence is analysed ') 
							return 
						if mainVerbToken.dep_ == 'ROOT':
							lingui_accessVerb_patterns(mainVerbToken)
							self.toPrintInSentence.append('this target sentence is analysed ')
							return	

				if token.pos_ == 'NOUN' and any(rightNoun in token.lemma_ for rightNoun in self.ontoDict.rightNouns):	
					self.toPrintInSentence.append('trigger rightNoun: '+token.text)
					if token.text.lower() not in self.ontoDict.rightNouns: 
						self.ontoDict.rightNouns.append(token.text.lower())
					if pattern_prep_n(token):	
						addToOntoDict()
						return	
					mainVerbToken = None
					if token.dep_ == 'dobj' and token.head.text == 'have': # have the right + ... 
						pattern_aclVerb_dobj_prep_n(token)
						self.toPrintInSentence.append('this target sentence is analysed ')
					if token.dep_ == 'dobj' and token.head.pos_ == 'VERB' and token.head.text != 'have':

						if pattern_rightVerb_rightNoun(token):
							VerbToken = pattern_rightVerb_rightNoun(token) 
						else:
							VerbToken = pattern_Verb_rightNoun(token)
						#print('verbToken'+VerbToken)
						if VerbToken:
							mainVerbToken = lingui_findMainVerb_from_rightVerb(VerbToken)	
						else:
							self.toPrintInSentence.append('skip for no access')
							return None							
					if not (token.dep_ == 'dobj' and token.head.pos_ == 'VERB'): 
						mainVerbToken = lingui_findMainVerb(token)
					# 	if not mainVerbToken: # no main verb ????						
					if mainVerbToken: 
						self.toPrintInSentence.append('the mainVerbToken is: '+mainVerbToken.text)	
						checkMainVerb(mainVerbToken)	
						return 		
					else:
						self.toPrintInSentence.append('skip this sentence')
		

		self.candidateInSentence.rightVerbs, self.candidateInSentence.rightNouns, self.candidateInSentence.accessVerbs, self.candidateInSentence.accessNouns, self.toPrintInSentence = ([] for i in range(5))		
		with doc.retokenize() as retokenizer:
			for chunk in doc.noun_chunks:
				retokenizer.merge(chunk, attrs={'LEMMA': chunk.root.lemma_, 'TAG':chunk.root.tag_, 'TEXT': chunk.root.text })
		self.toPrintInSentence.append('**************************************')
		self.toPrintInSentence.append('*********** analyse start ************')
		self.toPrintInSentence.append(doc)

		for token in doc:
			self.toPrintInSentence.append(token.text+'\t'+token.pos_+'\t'+token.dep_+'\t'+token.head.text)
		analysizeSentence(doc)
		for string in self.toPrintInSentence:
			print(string)

		if self.candidateInSentence.accessNouns:		
			self.word_dict['accessNouns'].append(self.candidateInSentence.accessNouns)
		else:
			self.word_dict['accessNouns'].append('nah')
			self.word_dict['rightNouns'].append('nah')
			self.word_dict['rightVerbs'].append('nah')
			self.word_dict['accessVerbs'].append('nah')
			return 
		if self.candidateInSentence.rightVerbs:		
			self.word_dict['rightVerbs'].append(self.candidateInSentence.rightVerbs)
		else:
			self.word_dict['rightVerbs'].append('nah')
		if self.candidateInSentence.rightNouns:		
			self.word_dict['rightNouns'].append(self.candidateInSentence.rightNouns)
		else:
			self.word_dict['rightNouns'].append('nah')
		if self.candidateInSentence.accessVerbs:		
			self.word_dict['accessVerbs'].append(self.candidateInSentence.accessVerbs)	
		else:
			self.word_dict['accessVerbs'].append('nah')

if __name__ == '__main__':
	
	nlp = spacy.load('en_core_web_lg') 
	print(nlp.pipe_names)

	extractor = EventsExtraction()
	sentences = []
	with open('./input/user_rights_sentences_dedup.tsv') as csvfile:
		reader = csv.reader(csvfile,delimiter=',')
		for row in reader:
			sentences.append(row[1])	
	
	counter = 0
	for doc in nlp.pipe(sentences[:200]):
		extractor.word_dict['sentence'].append(sentences[counter])
		extractor.generateOntology(doc)
		counter += 1

	df = pd.DataFrame(extractor.word_dict)
	filename = './output/result.csv'
	df.to_csv(filename, sep=',', encoding='utf-8',index=False) 
	extractor.recordFile.close()

	print(extractor.ontoDict.rightNouns)
	print(extractor.ontoDict.rightVerbs)
	print(extractor.ontoDict.accessNouns)
	print(extractor.ontoDict.accessVerbs)


	# evaluation
	with open('./input/data_gt_dedup_user_rights_sentences.csv', 'r') as source, open('./output/result.csv', 'r') as tested:
		source_r = csv.reader(source,delimiter=',')
		tested_r = csv.reader(tested,delimiter=',')
		TP_accessNouns = 0
		TP_FP_accessNouns = 0
		TP_FN_accessNouns = 0
		counter = 0
		for row_s, row_t in zip(source_r, tested_r):
			if counter > 200:
				break
			else:
				counter += 1
			if row_s[0] == 'sentence':
				print('skip header')
				continue

			if row_s[1] != 'nah':
				TP_FN_accessNouns += 1
			if row_t[1] != 'nah':
				TP_FP_accessNouns += 1

			if row_s[1] != 'nah' and row_t[1] == 'nah':
				print('TN missing sentence with accessNouns: ', row_s[0], row_s[1], row_t[1])
			if row_s[1] == 'nah' and row_t[1] != 'nah':
				print('FP non-targeted sentence predicted: ', row_s[0], row_s[1], row_t[1])

			if row_s[1] != 'nah' and row_t[1] != 'nah':
				print(row_s[1],row_t[1])
				if row_s[1] in row_t[1]: # to add type if sting, then in; if list then loop or any
					TP_accessNouns += 1
					print(row_s[1],row_t[1])
				else:
					print('wrong predicted sentence with accessNouns: ', row_s[0], row_s[1], row_t[1])

		print('TP_accessNouns: ', TP_accessNouns)
		print('TP_FP_accessNouns: ', TP_FP_accessNouns) # trigger word
		print('TP_FN_accessNouns: ', TP_FN_accessNouns)
		print('precision_accessNouns: ', TP_accessNouns/TP_FP_accessNouns)
		print('recall_accessNouns: ', TP_accessNouns/TP_FN_accessNouns)

# result
# TP_accessNouns:  10
# TP_FP_accessNouns:  28
# TP_FN_accessNouns:  51
# precision_accessNouns:  0.35714285714285715
# recall_accessNouns:  0.19607843137254902
