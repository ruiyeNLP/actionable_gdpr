#goal: automatically generate ontology words and patterns
#input: initial seed word lists, heuristic linguistic patterns
#output: expanded ontology word lists(???and patterns to activate trigger words)
#from asyncio.windows_events import NULL
from curses.panel import top_panel
from json.tool import main
import spacy
import csv

'''ontology dictionary'''
class OntologyDict:
	def __init__(self):
		# init seed words
		self.rightVerbs = [u'exercise', u'lodge', u'delete', u'access', u'correct', u'object',u'ask',u'correct']
		self.rightVerbsFilter = [u'like', u'make']
		self.accessVerbs = [u'contact']
		self.rightNouns = [u'right']
		self.accessNouns = [u'email']
		self.accessVerbsFilter = [u'do']
		self.preps = [u'via',u'by',u'through',u'within',u'at']

'''complex event pattern '''
class EventsExtraction:
	def __init__(self, nlpModel):
		self.parser = nlpModel
		self.ontodict = OntologyDict()

	'''generate ontology with liguistic method'''
	def generate_ontology(self, paragraph):
		doc = self.parser(paragraph)
		with doc.retokenize() as retokenizer:
			for chunk in doc.noun_chunks:
				retokenizer.merge(chunk, attrs={'LEMMA': chunk.root.lemma_, 'TAG':chunk.root.tag_, 'TEXT': chunk.root.text })

		def analysize_sentence(sent,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint):
			def lingui_rightNoun_prep_n(token, toPrint):
				for child in token.children:
							#print('grandchild', grandchild.text, grandchild.pos_, grandchild.dep_)
							if child.dep_ == 'prep' and child.text in self.ontodict.preps:
								print('rightNoun+prep: ', child.text, child.pos_, child.dep_)
								curtoken = child
								for child in curtoken.children:
									if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ == 'PROPN'):
										#print('verb+prep+pobj', gradgrandchild.text)
										if child.lemma_ not in self.ontodict.accessNouns: # enlarge accessverb list of verb + 
											self.ontodict.accessNouns.append(child.lemma_) 
											#print('gradgrandchild.lemma_', gradgrandchild.lemma_)
											break
			def lingui_prep_n(token,accessNouns,toPrint):
				for child in token.children:
					if child.dep_ == 'prep' and child.text in self.ontodict.preps:
						toPrint.append('prep: '+child.text+' | '+child.dep_+' | '+child.pos_)
						curtoken = child
						for child in curtoken.children:
							if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ == 'PROPN'):
								accessNouns.append(child.lemma_) 
								toPrint.append('prep+pobj: '+child.text+' | '+child.dep_+' | '+child.pos_)
								return True
				return False
			
			def activate_ontodic_enlarge(rightVerbs,rightNouns,accessNouns,accessVerbs):
				for rightVerb in rightVerbs:
					if rightVerb.lower() not in self.ontodict.rightVerbs: 
						self.ontodict.rightVerbs.append(rightVerb.lower())
				for rightNoun in rightNouns:
					if rightNoun.lower() not in self.ontodict.rightNouns: 
						self.ontodict.rightNouns.append(rightNoun.lower())
				for accessNoun in accessNouns:
					if accessNoun.lower() not in self.ontodict.accessNouns: 
						self.ontodict.accessNouns.append(accessNoun.lower())
				for accessVerb in accessVerbs:
					if accessVerb.lower() not in self.ontodict.accessVerbs: 
						self.ontodict.accessVerbs.append(accessVerb.lower())

			def lingui_aclVerb_dobj_prep_n(token,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint):
				for child in token.children: 
					if child.dep_ == 'acl' and child.pos_ == 'VERB': # have the right + to + Verb
						curchild = child
						toPrint.append('have the right+aclVerb: '+child.text+' | '+child.dep_+' | '+child.pos_)
						if curchild.lemma_ not in self.ontodict.rightVerbsFilter: 
							rightVerbs.append(curchild.lemma_)
						for child in curchild.children:
							if child.dep_ == 'dobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
								rightNouns.append(child.lemma_)	
								toPrint.append('have the right+aclVerb+n: '+child.text+' | '+child.dep_ +' | '+child.pos_)
								toPrint.append('have the right+prep+pobj check start')
								if lingui_prep_n(child,accessNouns,toPrint):	
									activate_ontodic_enlarge(rightVerbs,rightNouns,accessNouns,accessVerbs)					
				return

			def lingui_rightVerb_rightNoun(token, rightVerbs,toPrint):
				if token.head.lemma_ not in self.ontodict.rightVerbsFilter: 
					rightVerbs.append(token.head.lemma_)
					toPrint.append('rightVerb+rightNoun: '+token.head.text+' | '+token.head.dep_+' | '+token.head.pos_)
					return token.head

			def lingui_findMainVerb_from_rightVerb(token,toPrint):
				# toPrint.append('rightVerb: '+token.text)
				if not token:
					toPrint.append('skip for no access')
					return 
				if token.dep_ == 'ROOT':
					toPrint.append('rightVerb is Root: '+token.text)
					return token
				if token.dep_ == 'xcomp' and token.head.pos_ == 'VERB' and token.head.dep_ == 'advcl':
					toPrint.append('rightVerb+xcomp+advcl: '+token.head.text)
					return token.head
				
			def lingui_findMainVerb(token, toPrint): # another method is to use token.head.dep_ == 'xcomp':
						curtoken = token.head
						toPrint.append('curtoken: '+curtoken.text+' | '+curtoken.dep_+' | '+curtoken.pos_)
						if not (curtoken.dep_ == 'advcl' and curtoken.pos_ == 'VERB'):
							curtoken = curtoken.head
							toPrint.append('curtoken+rightNoun: '+curtoken.text+' | '+curtoken.dep_+' | '+curtoken.pos_)
							if not (curtoken.dep_ == 'advcl' and curtoken.pos_ == 'VERB'):
								curtoken = curtoken.head
								toPrint.append('curtoken+rightNoun: '+curtoken.text+' | '+curtoken.dep_+' | '+curtoken.pos_)
								if not (curtoken.dep_ == 'advcl' and curtoken.pos_ == 'VERB'):
									curtoken = curtoken.head
									toPrint.append('curtoken+rightNoun: '+curtoken.text+' | '+curtoken.dep_+' | '+curtoken.pos_)
						if not(curtoken.dep_ == 'advcl' and curtoken.pos_ == 'VERB'):
							toPrint.append('no main verb')
							return 
						else:
							return curtoken

			def lingui_accessVerb_patterns(accessVerbToken,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint):
				accessNoun_accessVerb_dobj = []
				accessNoun_accessVerb_prep_pojb = []
				accessNoun_accessVerb_prep_prep_pobj = []
				for child in accessVerbToken.children:
					toPrint.append('accessVerb: '+child.text+' | '+child.dep_+' | '+child.pos_)
					if child.dep_ == 'dobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
						toPrint.append('accessverb+dobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
						accessNoun_accessVerb_dobj.append(child.text)
						

					if child.dep_ == 'prep' and child.text in self.ontodict.preps: # go down through the tree and find 'via' + pobj
						toPrint.append('accessverb+prep: '+child.text+' | '+child.pos_+' | '+child.dep_)
						curchild = child
						for child in curchild.children:
							if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
								toPrint.append('accessverb+prep+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
								accessNoun_accessVerb_prep_pojb.append(child.text)
							if child.dep_ == 'pcomp' and child.pos_ == 'VERB':
								toPrint.append('accessverb+prep+pcomp'+child.text+' | '+child.pos_+' | '+child.dep_)
								curchild = child
								for child in curchild.children:
									if child.dep_ == 'dobj' and child.pos_ == 'NOUN':
										toPrint.append('accessverb+prep+pcomp+dobj'+child.text+' | '+child.pos_+' | '+child.dep_)
										accessNoun_accessVerb_prep_pojb.append(child.text)

					if child.dep_ == 'prep' and child.text not in self.ontodict.preps: # go down through the tree and find 'via' + pobj
						toPrint.append('accessverb+prep(not via): '+child.text+' | '+child.pos_+' | '+child.dep_)
						curchild = child
						for child in curchild.children:
							toPrint.append('accessverb+prep(not via)+prep: '+child.text+' | '+child.pos_+' | '+child.dep_)
							if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
								toPrint.append('accessverb+prep(not via)+prep+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
								curchild = child 
								for child in curchild.children:
									if child.dep_ == 'prep' and child.text in self.ontodict.preps:
										toPrint.append('accessverb+prep(not via)+prep+pobj+via: '+child.text+' | '+child.pos_+' | '+child.dep_)
										curchild = child
										for child in curchild.children:
											if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
												toPrint.append('accessverb+prep(not via)+prep+pobj+via+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
												accessNoun_accessVerb_prep_prep_pobj.append(child.text)
				print('accessNoun_accessVerb_dobj: ', accessNoun_accessVerb_dobj)
				print('accessNoun_accessVerb_prep_pojb: ', accessNoun_accessVerb_prep_pojb)
				print('accessNoun_accessVerb_prep_pojb: ', accessNoun_accessVerb_prep_prep_pobj)
				if not accessNoun_accessVerb_dobj and not accessNoun_accessVerb_prep_pojb and not accessNoun_accessVerb_prep_prep_pobj:
					return
				elif accessNoun_accessVerb_prep_pojb:
					for noun in accessNoun_accessVerb_prep_pojb:
						accessNouns.append(noun)
				elif accessNoun_accessVerb_dobj:
					for noun in accessNoun_accessVerb_dobj:
						accessNouns.append(noun)
				else: 
					for noun in accessNoun_accessVerb_prep_prep_pobj:
						accessNouns.append(noun)
				activate_ontodic_enlarge(rightVerbs,rightNouns,accessNouns,accessVerbs)

			def lingui_mainVerb_check(mainVerbToken,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint):

				print(mainVerbToken.head.text)
				if mainVerbToken.head.pos_ != 'VERB':
					return 

				toPrint.append('mainVerb+accessVerb: '+mainVerbToken.head.text)						
				curtoken = mainVerbToken.head
				lingui_accessVerb_patterns(curtoken,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint)
			
			for token in sent:
				if token.pos_ == 'NOUN'and any(rightNoun in token.lemma_ for rightNoun in self.ontodict.rightNouns):	
					toPrint.append('trigger rightNoun: '+token.text)
					if token.dep_ == 'dobj' and token.head.text == 'have': # have the right + ... 
						lingui_aclVerb_dobj_prep_n(token,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint)
						for string in toPrint:
							print(string)						
						return 
					if token.dep_ == 'dobj' and token.head.pos_ == 'VERB' and token.head.text != 'have':
						VerbToken = lingui_rightVerb_rightNoun(token, rightVerbs,toPrint) 
						mainVerbToken = lingui_findMainVerb_from_rightVerb(VerbToken, toPrint)
													
					if not (token.dep_ == 'dobj' and token.head.pos_ == 'VERB'): 
						mainVerbToken = lingui_findMainVerb(token, toPrint)

					# 	if not mainVerbToken: # no main verb ????						
					
					if mainVerbToken: 
						toPrint.append('the mainVerbToken is: '+mainVerbToken.text)	

						lingui_mainVerb_check(mainVerbToken,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint )	
						return						

				if token.pos_ == 'VERB'and any(rightVerb in token.lemma_ for rightVerb in self.ontodict.rightVerbs):
					toPrint.append("rightsVerb: "+token.text)

					def lingui_rightVerb_rightNoun_pp(token,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint):
						for child in token.children:
							if child.dep_ == 'dobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
								toPrint.append('rightsVerb+rightsNoun: '+child.text+' | '+child.pos_+' | '+child.dep_)
								if child.lemma_ not in self.ontodict.rightNouns: # enlarge accessverb list of verb + dobj
									rightNouns.append(child.lemma_) 
								toPrint.append('rightVerb+perp+pobj check start')
								if lingui_prep_n(child,accessNouns,toPrint):
									activate_ontodic_enlarge(rightVerbs,rightNouns,accessNouns,accessVerbs)
									return True
						return False

					if lingui_rightVerb_rightNoun_pp(token,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint):
						for string in toPrint:
							print(string)
						
						return

					def lingui_rightVerb_pp(token,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint):
						for child in token.children:
							if child.dep_ == 'prep' and child.text in self.ontodict.preps: 
								toPrint.append('accessverb+prep: '+child.text+' | '+child.pos_+' | '+child.dep_)
								curchild = child
								for child in curchild.children:
									if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
										toPrint.append('accessverb+prep+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
										if child.lemma_ not in self.ontodict.accessNouns: 
											accessNouns.append(child.lemma_)
										return True # ??? or continure & compare all accessNoun candidates
									if child.dep_ == 'pcomp':
										toPrint.append('accessverb+prep+pcomp: '+child.text+' | '+child.pos_+' | '+child.dep_)
										curchild = child
										for child in curchild.children:		
											if child.dep_ == 'prep':
												toPrint.append('accessverb+prep+pcomp+prep: '+child.text+' | '+child.pos_+' | '+child.dep_)
												curchild = child
												for child in curchild.children:
													if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
														toPrint.append('accessverb+prep+pcomp+prep+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
														if child.lemma_ not in self.ontodict.accessNouns:  
															accessNouns.append(child.lemma_)
														return True # ??? or continure & compare all accessNoun candidates
												if child.dep_ == 'dobj':
													toPrint.append('accessverb+prep+pcomp+dobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
													formerchild = child 
													curchild = child
													child_has_acl =False
													for child in curchild.children:
														if child.dep_ == 'acl':
															child_has_acl = True
															toPrint.append('accessverb+prep+pcomp+dobj+acl: '+child.text+' | '+child.pos_+' | '+child.dep_)
															curchild = child
															for child in curchild.children:
																if child.dep_ == 'prep':
																	toPrint.append('accessverb+prep+pcomp+dobj+acl+prep: '+child.text+' | '+child.pos_+' | '+child.dep_)
																	curchild = child
																	for child in curchild.children:
																		if child.dep_ == 'pobj':
																			toPrint.append('accessverb+prep+pcomp+dobj+acl+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
																			if child.lemma_ not in self.ontodict.accessNouns: # enlarge accessverb list of verb + 
																				accessNouns.append(child.lemma_)
																			return True # ??? or continure & compare all accessNoun candidates
													if not child_has_acl:
														if formerchild.lemma_ not in self.ontodict.accessNouns: # enlarge accessverb list of verb + 
															accessNouns.append(formerchild.lemma_)
						return False

					if lingui_rightVerb_pp(token,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint):
						for string in toPrint:
							print(string)
						activate_ontodic_enlarge(rightVerbs,rightNouns,accessNouns,accessVerbs)
						return

					def lingui_rightVerb_conjVerb_pp(token,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint):
						for child in token.children:
							if child.dep_ == 'conj' and child.pos_ == 'VERB':
								if child.lemma_ not in self.ontodict.rightVerbs: 
									rightVerbs.append(child.lemma_)
								curchild = child
								toPrint.append('conjVerb: '+curchild.lemma_)
								return lingui_rightVerb_pp(curchild,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint) # to add ''You can control and limit our use of your advertising ID in your device settings .''
								# for child in curchild.children:
								# 	if child.dep_ == 'dobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
								# 		toPrint.append('conjVerb+dobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
								# 		curchild = child
								# 		for child in curchild.children:
								# 			if child.dep_ == 'prep':
								# 				toPrint.append('conjVerb+dobj+prep: '+child.text+' | '+child.pos_+' | '+child.dep_)
								# 				curchild = child
								# 				for child in curchild.children:
								# 					if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ =='PROPN'):
								# 						toPrint.append('conjVerb+dobj+prep+pobj: '+child.text+' | '+child.pos_+' | '+child.dep_)
								# 						if child.lemma_ not in self.ontodict.accessNouns: # enlarge accessverb list of verb + 
								# 							accessNouns.append(child.lemma_) 
								# 							#print('gradgrandchild.lemma_', gradgrandchild.lemma_)
								# 					return True
						return False

					if lingui_rightVerb_conjVerb_pp(token,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint):
						for string in toPrint:
							print(string)
						activate_ontodic_enlarge(rightVerbs,rightNouns,accessNouns,accessVerbs)
						return						
								
				# 		if child.dep_ == 'dobj' and child.pos_ != 'NOUN':
				# 			#print('child: ', child.text, child.pos_, child.dep_)
				# 			for grandchild in child.children:
				# 				#print('grandchild', grandchild.text, grandchild.pos_, grandchild.dep_)
				# 				if grandchild.dep_ == 'prep':
				# 					for gradgrandchild in grandchild.children:
				# 						if gradgrandchild.dep_ == 'pobj' and gradgrandchild.pos_ == 'NOUN':
				# 							#print('verb+prep+pobj', gradgrandchild.text)
				# 							if gradgrandchild.lemma_ not in self.ontodict.rightNouns: # enlarge accessverb list of verb + 
				# 								self.ontodict.rightNouns.append(gradgrandchild.lemma_) 
				# 								#print('gradgrandchild.lemma_', gradgrandchild.lemma_)
				# 								break
						

					#if not (token.dep_ == 'dobj' and token.head.pos_ == 'VERB'): 
					mainVerbToken = lingui_findMainVerb_from_rightVerb(token, toPrint)
					if mainVerbToken: 
						toPrint.append('the mainVerbToken is: '+mainVerbToken.text)	
						if mainVerbToken.dep_ == 'advcl' and (mainVerbToken.head.pos_ == 'VERB' or mainVerbToken.head.lemma_ == 'do'): # find rightsacess pattern
							toPrint.append('rightVerb: '+mainVerbToken.text+' accessVerb: '+mainVerbToken.head.lemma_)
							if mainVerbToken.head.lemma_ not in self.ontodict.accessVerbs and mainVerbToken.head.lemma_ != 'do': # enlarge accessverb list 
								accessVerbs.append(mainVerbToken.head.lemma_) # ??? not sure
							curtoken = mainVerbToken.head
							lingui_accessVerb_patterns(curtoken,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint)
							for string in toPrint:
								print(string) 
							return 

						if mainVerbToken.dep_ == 'ROOT':
							lingui_accessVerb_patterns(mainVerbToken,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint)
							for string in toPrint:
								print(string) 
							return

		for sent in doc.sents:
			rightVerbs = []
			rightNouns = []
			accessNouns = []
			accessVerbs = []
			toPrint = []
			for token in sent:
				toPrint.append(token.text+'\t'+token.pos_+'\t'+token.dep_+'\t'+token.head.text)
			analysize_sentence(sent,rightVerbs,rightNouns,accessNouns,accessVerbs,toPrint)

			



if __name__ == '__main__':
	nlp = spacy.load('en_core_web_lg') #self.defined entity 
	print(nlp.pipe_names)

	# sentences_training = [
	# 	"If you have any questions related to data protection , or if you wish to exercise your rights , please contact EMAIL or the address stated above , adding the keyword Data Protection . ",
	# 	"If you have any questions about this Privacy Policy or your rights under applicable data protection law , you can contact our customer service at address." ,
	# 	"You can access the personal information you have made available as part of your account by logging into your Game account",
	# 	"You can access much of your information by logging into your account .",
	# 	'You can access your personal data within the Apps profile page',
	# 	'You can edit some of your personal data through your account .',
	# 	'You can control and limit our use of your advertising ID in your device settings .',
	# 	'To limit the use and disclosure of your personal information , please submit a written request to -Email- .',
	# 	'You can disable the sharing of you position by adapting your browser settings accordingly .',
	# 	'If you wish to object to this use of your data , you can do so by canceling our newsletters in any of the emails we sent .',
	# 	'If you would like a copy of some or all of your Personal Information , please contact us at -Email- - ',
	# 	'You can request a copy of or deletion of your game account data through our Personal Data Request Portal .',
	# 	'You have the right to make a complaint to the Information Commissioners Office'
	# ]

	# extractor = EventsExtraction(nlpModel=nlp)
	# for sentence in sentences_training:
	# 	extractor.generate_ontology(sentence)
	# print(extractor.ontodict.rightNouns)
	# print(extractor.ontodict.rightVerbs)
	# print(extractor.ontodict.accessNouns)
	# print(extractor.ontodict.accessVerbs)


# output of training sentences

	extractor = EventsExtraction(nlpModel=nlp)
	with open('./input/user_rights_sentences.tsv') as csvfile:
		reader = csv.reader(csvfile)
		#for row in islice(reader, 10): # first 10 only
		for row in reader:
			row2string = ''.join(str(e) for e in row)
			rowSplited = row2string.split('\t')
			parapraph = rowSplited[1]
			
			extractor.generate_ontology(parapraph)
	print(extractor.ontodict.rightNouns)
	print(extractor.ontodict.rightVerbs)
	print(extractor.ontodict.accessNouns)
	print(extractor.ontodict.accessVerbs)
# output
