#goal: automatically generate trigger words and patterns
#input: initial triggers word lists, heuristic linguistic patterns
#output: expanded trigger word lists, and patterns to activate trigger words
import spacy

'''tag keyphrase'''
class KeyphraseTagger:
	def __init__(self):
		self.rightVerbs = [u'exercise',u'access',u'edit',u'control',u'limit',u'disable',u'object']
		self.accessVerbs = [u'contact']
		self.rightNouns = [u'right',u'copy']
		self.accessNouns = [u'email']
		self.preps = [u'via',u'by',u'through',u'within',u'at',u'to']

'''complex event pattern '''
class EventsExtraction:
	def __init__(self, nlpModel):
		self.parser = nlpModel
		self.tagger = KeyphraseTagger()
		self.patterns = []
		self.rightspatterns = []
		self.accesspatterns = []
		self.rightaccesspatterns = []

	'''creat pattern'''
	def create_pattern(self, paragraph):
		doc = self.parser(paragraph)
		with doc.retokenize() as retokenizer:
			for chunk in doc.noun_chunks:
				retokenizer.merge(chunk, attrs={'LEMMA': chunk.root.lemma_, 'TAG':chunk.root.tag_, 'TEXT': chunk.root.text })
				#print(chunk, chunk.root.lemma_, chunk.root.tag_)
		for sent in doc.sents:
			for token in sent:
				print(token.text,token.pos_, token.dep_, token.head.text)

		for sent in doc.sents:
			for token in sent:
				#print("token",token, token.pos_, token.dep_, token.head.text)
				if token.pos_ == 'NOUN'and any(rightNoun in token.lemma_ for rightNoun in self.tagger.rightNouns):
					print("rightNouns: ", token.text)
					if token.dep_ == 'dobj' and token.head.pos_ == 'VERB' and token.head.text != 'have': 
						curtoken = token
						if token.head.lemma_ not in self.tagger.rightVerbs and token.head.text != 'like' and token.lemma_ != 'make': # enlarge rightsverb list rightsverb+rightsnoun
							self.tagger.rightVerbs.append(token.head.lemma_) 
							print('add new rightverb: ', token.head.lemma_)
					
					if token.dep_ == 'dobj' and token.head.text == 'have': 
						for child in token.children:
							print('have the right+',child.text, child.dep_, child.pos_)
							if child.dep_ == 'acl' and child.pos_ == 'VERB': # add right trigger have the right to v
								curchild = child
								print('have the right+acl',child.text, child.dep_, child.pos_)
								for child in curchild.children:
									if child.dep_ == 'dobj' and child.pos_ == 'NOUN':
										print('have the right+acl+n',child.text, child.dep_, child.pos_)
										if child.lemma_ not in self.tagger.rightNouns: # enlarge rightsverb list rightsverb+rightsnoun
											self.tagger.rightNouns.append(child.lemma_)										
										curchild = child
										for child in curchild.children:
											if child.dep_ == 'prep' and child.text in self.tagger.preps:
												print('have the right+acl+prep',child.text, child.dep_, child.pos_)
												curchild = child
												for child in curchild.children:
													if child.dep_ == 'pobj' and child.pos_ == 'PROPN':
														print('have the right+acl+prep+pobj',child.text, child.dep_, child.pos_)
														if child.lemma_ not in self.tagger.accessNouns: # enlarge accessverb list of verb + 
															self.tagger.accessNouns.append(child.lemma_)
														break								
										break
								# if child.lemma_ not in self.tagger.rightVerbs and child.lemma_ != 'make': # enlarge rightsverb list rightsverb+rightsnoun
								# 	self.tagger.rightVerbs.append(child.lemma_)
												
					if not (token.dep_ == 'dobj' and token.head.pos_ == 'VERB'):
						curtoken = token.head
						#print('curtoken: ', curtoken)
						if not (curtoken.dep_ == 'dobj' and curtoken.head.pos_ == 'VERB'):
							curtoken = curtoken.head
							#print('curtoken: ', curtoken)
							if not (curtoken.dep_ == 'dobj' and curtoken.head.pos_ == 'VERB'):
								curtoken = curtoken.head
								#print('curtoken: ', curtoken)
						if curtoken.head.lemma_ not in self.tagger.rightVerbs and curtoken.head.text != 'have': # enlarge rightsverb list rightsverb+rightsnoun
							self.tagger.rightVerbs.append(curtoken.head.lemma_) 
							#print('add new rightverb: ', curtoken.head.lemma_)
					
					for grandchild in token.children:
								#print('grandchild', grandchild.text, grandchild.pos_, grandchild.dep_)
								if grandchild.dep_ == 'prep' and grandchild.text in self.tagger.preps:
									print('rightNoun+prep: ', grandchild.text, grandchild.pos_, grandchild.dep_)
									for gradgrandchild in grandchild.children:
										if gradgrandchild.dep_ == 'pobj' and (gradgrandchild.pos_ == 'NOUN' or gradgrandchild.pos_ == 'PROPN'):
											#print('verb+prep+pobj', gradgrandchild.text)
											if gradgrandchild.lemma_ not in self.tagger.accessNouns: # enlarge accessverb list of verb + 
												self.tagger.accessNouns.append(gradgrandchild.lemma_) 
												#print('gradgrandchild.lemma_', gradgrandchild.lemma_)
												break
				
					
					if curtoken.head.dep_ == 'xcomp':
						curtoken = curtoken.head.head
					# elif curtoken.head.dep_ == 'ROOT':
					# 	curtoken = curtoken
					else: 
						curtoken = curtoken.head
					
					print(curtoken.text, curtoken.dep_)
					if curtoken.dep_ == 'ROOT':
						for child in curtoken.children:
							#print(child.text, child.pos_, child.dep_)
							if child.dep_ == 'dobj' and child.pos_ == 'NOUN':
								print('rightsverb+dobj', child.text, child.pos_, child.dep_)
							if child.dep_ == 'prep' and child.text in self.tagger.preps: # go down through the tree and find 'via' + pobj
								print('rightsverb+prep', child.text, child.pos_, child.dep_)
								curchild = child
								for child in curchild.children:
									if child.dep_ == 'pobj':
										print('rightsverb+prep+pobj', child.text, child.pos_, child.dep_)
							if child.dep_ == 'prep' and child.text not in self.tagger.preps: # go down through the tree and find 'via' + pobj
								print('rightsverb+prep(not via)', child.text, child.pos_, child.dep_)
								curchild = child
								for child in curchild.children:
									print('rightsverb+prep(not via)+prep', child.text, child.pos_, child.dep_)
									if child.dep_ == 'pobj' and child.pos_ == 'NOUN':
										print('rightsverb+prep(not via)+prep+pobj', child.text, child.pos_, child.dep_)
										curchild = child 
										for child in curchild.children:
											if child.dep_ == 'prep' and child.text in self.tagger.preps:
												print('rightsverb+prep(not via)+prep+pobj+via', child.text, child.pos_, child.dep_)
												curchild = child
												for child in curchild.children:
													if child.dep_ == 'pobj':
														print('rightsverb+prep(not via)+prep+pobj+via+pobj', child.text, child.pos_, child.dep_)

					if curtoken.dep_ == 'advcl' and curtoken.head.pos_ == 'VERB': # find rightsacess pattern 

						if curtoken.head.lemma_ not in self.tagger.accessVerbs: # enlarge accessverb list 
							self.tagger.accessVerbs.append(curtoken.head.lemma_) 
						curtoken = curtoken.head
						print("accessVERB: ", curtoken)
						# add to rightnaccess pattern 
						for child in curtoken.children:
							#print('accessVerb: ', child.text, child.pos_, child.dep_)
							if child.dep_ == 'dobj' and child.pos_ == 'NOUN':
								print('accessverb+dobj', child.text, child.pos_, child.dep_)
							if child.dep_ == 'prep' and child.text in self.tagger.preps: # go down through the tree and find 'via' + pobj
								print('accessverb+prep', child.text, child.pos_, child.dep_)
								curchild = child
								for child in curchild.children:
									if child.dep_ == 'pobj' and child.pos_ == 'NOUN':
										print('accessverb+prep+pobj', child.text, child.pos_, child.dep_)
										if child.lemma_ not in self.tagger.accessNouns: # enlarge rightsverb list rightsverb+rightsnoun
											self.tagger.accessNouns.append(child.lemma_)

							if child.dep_ == 'prep' and child.text not in [u'via','at']: # go down through the tree and find 'via' + pobj
								print('accessverb+prep(not via)', child.text, child.pos_, child.dep_)
								curchild = child
								for child in curchild.children:
									print('accessverb+prep(not via)+prep', child.text, child.pos_, child.dep_)
									if child.dep_ == 'pobj' and child.pos_ == 'NOUN':
										print('accessverb+prep(not via)+prep+pobj', child.text, child.pos_, child.dep_)
										curchild = child 
										for child in curchild.children:
											if child.dep_ == 'prep' and child.text in ['via']:
												print('accessverb+prep(not via)+prep+pobj+via', child.text, child.pos_, child.dep_)
												curchild = child
												for child in curchild.children:
													if child.dep_ == 'pobj':
														print('accessverb+prep(not via)+prep+pobj+via+pobj', child.text, child.pos_, child.dep_)
														if child.lemma_ not in self.tagger.accessNouns: # enlarge rightsverb list rightsverb+rightsnoun
															self.tagger.accessNouns.append(child.lemma_)

												break							

					print(self.tagger.rightVerbs)
					print(self.tagger.rightNouns)
					print(self.tagger.accessVerbs)
					print(self.tagger.accessNouns)
					continue
				if token.pos_ == 'VERB'and any(rightVerb in token.lemma_ for rightVerb in self.tagger.rightVerbs):
					print("rightsVerb: ", token.text)
					#print('rightsverb', token.text)
					for child in token.children:
						#print(child.text, child.pos_, child.dep_)
						if child.dep_ == 'dobj' and child.pos_ == 'NOUN':
							#print('***********', child.text, child.pos_, child.dep_, child.lemma_)
							if child.lemma_ not in self.tagger.rightNouns: # enlarge accessverb list of verb + dobj
								self.tagger.rightNouns.append(child.lemma_) 
							for grandchild in child.children:
								#print('rightNouns child', grandchild.text, grandchild.pos_, grandchild.dep_)
								if grandchild.dep_ == 'prep' and grandchild.text in [u'via',u'at',u'by',u'within']:
									print('rightNouns+prep', child.text, child.pos_, child.dep_)
									curchild = grandchild
									for child in curchild.children:
										if child.dep_ == 'pobj':
											print('rightNouns+prep+pobj', child.text, child.pos_, child.dep_)
											if child.lemma_ not in self.tagger.accessNouns: # enlarge accessverb list of verb + dobj
												self.tagger.accessNouns.append(child.lemma_)
											break
								break 
						if child.dep_ == 'conj' and child.pos_ == 'VERB':
							if child.lemma_ not in self.tagger.rightVerbs: # enlarge accessverb list with conj verb 
								self.tagger.rightVerbs.append(child.lemma_)
							curchild = child
							print('conjVerb: ', curchild)
							for child in curchild.children:
								if child.dep_ == 'dobj' and child.pos_ == 'NOUN':
									print('conjVerb+dobj: ', child.text, child.pos_, child.dep_)
									curchild = child
									for child in curchild.children:
										#print('grandchild', grandchild.text, grandchild.pos_, grandchild.dep_)
										if child.dep_ == 'prep':
											print('conjVerb+dobj+prep: ', child.text, child.pos_, child.dep_)
											curchild = child
											for child in curchild.children:
												if child.dep_ == 'pobj' and child.pos_ == 'NOUN':
													print('conjVerb+dobj+prep+pobj: ', child.text, child.pos_, child.dep_)
													if child.lemma_ not in self.tagger.accessNouns: # enlarge accessverb list of verb + 
														self.tagger.accessNouns.append(child.lemma_) 
														#print('gradgrandchild.lemma_', gradgrandchild.lemma_)
												break
										


								
						if child.dep_ == 'dobj' and child.pos_ != 'NOUN':
							#print('child: ', child.text, child.pos_, child.dep_)
							for grandchild in child.children:
								#print('grandchild', grandchild.text, grandchild.pos_, grandchild.dep_)
								if grandchild.dep_ == 'prep':
									for gradgrandchild in grandchild.children:
										if gradgrandchild.dep_ == 'pobj' and gradgrandchild.pos_ == 'NOUN':
											#print('verb+prep+pobj', gradgrandchild.text)
											if gradgrandchild.lemma_ not in self.tagger.rightNouns: # enlarge accessverb list of verb + 
												self.tagger.rightNouns.append(gradgrandchild.lemma_) 
												#print('gradgrandchild.lemma_', gradgrandchild.lemma_)
												break
						
						if child.dep_ == 'prep' and child.text in self.tagger.preps: # go down through the tree and find 'via' + pobj
								print('accessverb+prep', child.text, child.pos_, child.dep_)
								curchild = child
								for child in curchild.children:
									if child.dep_ == 'pobj' and child.pos_ == 'NOUN':
										print('accessverb+prep+pobj', child.text, child.pos_, child.dep_)
										if child.lemma_ not in self.tagger.accessNouns: # enlarge accessverb list of verb + 
											self.tagger.accessNouns.append(child.lemma_)
										break
									if child.dep_ == 'pcomp':
										print('accessverb+prep+pcomp', child.text, child.pos_, child.dep_)
										curchild = child
										for child in curchild.children:
											
											if child.dep_ == 'prep':
												print('accessverb+prep+pcomp+prep', child.text, child.pos_, child.dep_)
												curchild = child
												for child in curchild.children:
													if child.dep_ == 'pobj':
														print('accessverb+prep+pcomp+prep+pobj', child.text, child.pos_, child.dep_)
														if child.lemma_ not in self.tagger.accessNouns: # enlarge accessverb list of verb + 
															self.tagger.accessNouns.append(child.lemma_)

											if child.dep_ == 'dobj':
												print('accessverb+prep+pcomp+dobj', child.text, child.pos_, child.dep_)
												formerchild = child 
												curchild = child
												child_has_acl =False
												for child in curchild.children:
													if child.dep_ == 'acl':
														child_has_acl = True
														print('accessverb+prep+pcomp+dobj+acl', child.text, child.pos_, child.dep_)
														curchild = child
														for child in curchild.children:
															if child.dep_ == 'prep':
																print('accessverb+prep+pcomp+dobj+acl+prep', child.text, child.pos_, child.dep_)
																curchild = child
																for child in curchild.children:
																	if child.dep_ == 'pobj':
																		print('accessverb+prep+pcomp+dobj+acl+pobj', child.text, child.pos_, child.dep_)
																		if child.lemma_ not in self.tagger.accessNouns: # enlarge accessverb list of verb + 
																			self.tagger.accessNouns.append(child.lemma_)
																		break
												if not child_has_acl:
													if formerchild.lemma_ not in self.tagger.accessNouns: # enlarge accessverb list of verb + 
														self.tagger.accessNouns.append(formerchild.lemma_)

								
								break
					
					#print(token.head.dep_, )
					
					if token.dep_ == 'xcomp' and token.head.dep_ == 'advcl':
						curtoken = token.head
					# elif token.head.dep_ == 'advcl':
					# 	curtoken = token.head
					else:
						if token.dep_ == 'advcl' or token.dep_ == 'ROOT':
							curtoken = token 
						else:
							curtoken = token 
					print('curtoken: ', curtoken)
					if curtoken.dep_ == 'ROOT':
						for child in curtoken.children:
							#print(child.text, child.pos_, child.dep_)
							if child.dep_ == 'dobj' and child.pos_ == 'NOUN':
								print('accessverb(root)+dobj', child.text, child.pos_, child.dep_)
							if child.dep_ == 'prep' and child.text in [u'via',u'at',u'by',u'within',u'through']: # go down through the tree and find 'via' + pobj
								print('accessverb(root)+prep', child.text, child.pos_, child.dep_)
								curchild = child
								for child in curchild.children:
									if child.dep_ == 'pobj':
										print('accessverb(root)+prep+pobj', child.text, child.pos_, child.dep_)
							if child.dep_ == 'prep' and child.text not in [u'via',u'at',u'by',u'within',u'through']: # go down through the tree and find 'via' + pobj
								print('accessverb(root)+prep(not via)', child.text, child.pos_, child.dep_)
								curchild = child
								for child in curchild.children:
									print('accessverb(root)+prep(not via)+prep', child.text, child.pos_, child.dep_)
									if child.dep_ == 'pobj' and child.pos_ == 'NOUN':
										print('accessverb(root)+prep(not via)+prep+pobj', child.text, child.pos_, child.dep_)
										curchild = child 
										for child in curchild.children:
											if child.dep_ == 'prep' and child.text in [u'via',u'at',u'by',u'within',u'through']:
												print('accessverb(root)+prep(not via)+prep+pobj+via', child.text, child.pos_, child.dep_)
												curchild = child
												for child in curchild.children:
													if child.dep_ == 'pobj':
														print('accessverb(root)+prep(not via)+prep+pobj+via+pobj', child.text, child.pos_, child.dep_)

					if curtoken.dep_ == 'advcl' and (curtoken.head.pos_ == 'VERB' or curtoken.head.lemma_ == 'do'): # find rightsacess pattern
						print('rightVerb: ', curtoken.text, 'accessVerb: ', curtoken.head.lemma_)
						if curtoken.head.lemma_ not in self.tagger.accessVerbs and curtoken.head.lemma_ != 'do': # enlarge accessverb list 
							self.tagger.accessVerbs.append(curtoken.head.lemma_) 
						curtoken = curtoken.head
						# add to rightnaccess pattern 
						for child in curtoken.children:
							#print(child.text, child.pos_, child.dep_)
							if child.dep_ == 'dobj' and child.pos_ == 'NOUN':
								print('accessverb+dobj', child.text, child.pos_, child.dep_)
							if child.dep_ == 'prep' and child.text in self.tagger.preps: # go down through the tree and find 'via' + pobj
								print('accessverb+prep', child.text, child.pos_, child.dep_)
								curchild = child
								for child in curchild.children:
									if child.dep_ == 'pobj' and (child.pos_ == 'NOUN' or child.pos_ == 'PROPN'):
										print('accessverb+prep+pobj', child.text, child.pos_, child.dep_)
										if child.lemma_ not in self.tagger.accessNouns: # enlarge accessverb list of verb + 
											self.tagger.accessNouns.append(child.lemma_)
									if child.dep_ == 'pcomp' and child.pos_ == 'VERB':
										print('accessverb+prep+pcomp', child.text, child.pos_, child.dep_)
										curchild = child
										for child in curchild.children:
											if child.dep_ == 'dobj' and child.pos_ == 'NOUN':
												print('accessverb+prep+pcomp+dobj', child.text, child.pos_, child.dep_)
												if child.lemma_ not in self.tagger.accessNouns: # enlarge accessverb list of verb + 
													self.tagger.accessNouns.append(child.lemma_)

							if child.dep_ == 'prep' and child.text not in [u'via']: # go down through the tree and find 'via' + pobj
								print('accessverb+prep(not via)', child.text, child.pos_, child.dep_)
								curchild = child
								for child in curchild.children:
									print('accessverb+prep(not via)+prep', child.text, child.pos_, child.dep_)
									if (child.dep_ == 'pobj' or child.dep_ == 'dobj') and child.pos_ == 'NOUN':
										print('accessverb+prep(not via)+prep+pobj/dobj', child.text, child.pos_, child.dep_)
										curchild = child 
										for child in curchild.children:
											if child.dep_ == 'prep' and child.text in ['via']:
												print('accessverb+prep(not via)+prep+pobj+via', child.text, child.pos_, child.dep_)
												curchild = child
												for child in curchild.children:
													if child.dep_ == 'pobj':
														print('accessverb+prep(not via)+prep+pobj+via+pobj', child.text, child.pos_, child.dep_)
														if child.lemma_ not in self.tagger.accessNouns: # enlarge rightsverb list rightsverb+rightsnoun
															self.tagger.accessNouns.append(child.lemma_)

					print(self.tagger.rightVerbs)
					print(self.tagger.rightNouns)
					print(self.tagger.accessVerbs)
					print(self.tagger.accessNouns)
					break



if __name__ == '__main__':
	nlp = spacy.load('en_core_web_lg') #self.defined entity 
	print(nlp.pipe_names)

	sentences_training = [
		"If you have any questions related to data protection , or if you wish to exercise your rights , please contact EMAIL or the address stated above , adding the keyword Data Protection . ",
		"If you would like to exercise any of the rights you are entitled to , please contact us as the responsible party via the contact data given above , or use any of the other ways of contact provided to notify us .",
		"If you have any questions about this Privacy Policy or your rights under applicable data protection law , you can contact our customer service at address.",
		"You can access the personal information you have made available as part of your account by logging into your Game account",
		"You can access much of your information by logging into your account .",
		'You can edit your personal data within the Apps profile page',
		'You can edit some of your personal data through your account .',
		'You can control and limit our use of your advertising ID in your device settings .',
		'To limit the use and disclosure of your personal information , please submit a written request to -Email- .',
		'You can disable the sharing of you position by adapting your browser settings accordingly .',
		'If you wish to object to this use of your data , you can do so by canceling our newsletters in any of the emails we sent .',
		'If you would like a copy of some or all of your Personal Information , please contact us at -Email- - ',
		'You can request a copy of or deletion of your game account data through our Personal Data Request Portal .',
		'You have the right to make a complaint to the Information Commissioners Office'
	]

	extractor = EventsExtraction(nlpModel=nlp)
	for sentence in sentences_training:
		extractor.create_pattern(sentence)
	print(extractor.tagger.rightNouns)
	print(extractor.tagger.rightVerbs)
	print(extractor.tagger.accessNouns)
	print(extractor.tagger.accessVerbs)
	
	# extractor = EventsExtraction(nlpModel=nlp)
	# with open('./input/user_rights_sentences.tsv') as csvfile:
	# 	reader = csv.reader(csvfile)
	# 	#for row in islice(reader, 10): # first 10 only
	# 	for row in reader:
	# 		row2string = ''.join(str(e) for e in row)
	# 		rowSplited = row2string.split('\t')
	# 		parapraph = rowSplited[1]
			
	# 		extractor.create_pattern(parapraph)
	# print(extractor.tagger.rightNouns)
	# print(extractor.tagger.rightVerbs)
	# print(extractor.tagger.accessNouns)
	# print(extractor.tagger.accessVerbs)

