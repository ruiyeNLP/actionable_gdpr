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
# output 
# ['right', 'copy', 'your right', 'the right', 'the personal information', 'your information', 'your personal data', 'the use', 'the sharing', 'position', 'a complaint']
# ['exercise', 'access', 'edit', 'control', 'limit', 'disable', 'object', 'request', 'make']
# ['email', 'the contact data', 'address', 'your game account', 'your account', 'the apps profile page', 'your device setting', '-Email-', 'your browser setting', 'this use', 'our newsletter', '-email-', 'our Personal Data Request Portal', 'the Information Commissioners Office']
# ['contact', 'submit']
	
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
# output
# ['right', 'copy', 'your right', 'the sharing', 'your personal data', 'the processing', 'the right', 'inaccuracy', 'portability', 'our use', 'a complaint', 'certain data', 'data collection', 'all personal data', 'a company', 'certain type', 'your consent', 'your data', 'the accuracy', 'the erasure', 'their Data', 'a claim', 'an external data protection officer', 'a copy', 'your information', 'the information', 'his entire profile', 'the deletion', 'his entrie', 'all recipient', 'transferability', 'personal data', 'information', 'the personal data', 'change', 'update', 'access', 'datum', 'the contact information', 'other option', 'the way', 'your account', 'consent', 'our processing', 'place', 'commercially reasonable effort', 'a respective objection', 'your my account information', 'your personal information', 'our u.s.-based third party dispute resolution provider', 'our customer support team', 'such direct marketing', 'personal information', 'that information', 'the metro department', 'higher charge', 'further information', 'our office', 'these principle', 'the restriction', 'control', 'their contact detail', 'this right', 'any employee', 'email', 'the other way', 'good faith effort', 'the method', 'a request', 'the use', 'these right', 'what data', 'processing', 'complaint', 'contact detail', 'this information', 'the appropriate technologie', 'our customer service', 'an additional request', 'privacy', 'what information', 'their personal data', 'your complaint', 'confirmation', 'the purpose', 'a small charge', 'your marketing preference', 'our customer services department', 'your 2k account information', 'any personal information', 'our data protection officer', 'rectification', 'the personal information', 'certain tracking', 'their accuracy', 'their processing', 'such promotional communication', 'a written request', 'most information', 'your profile information', 'your device privacy setting', 'question', 'valid complaint', 'contextlogic b.v.s data protection officer', 'my account', 'your local data protection authority', 'application', 'an e-mail', 'our game', 'zuuks games data protection officer', 'e-mail', 'an access request', 'the access', 'restriction', 'the ability', 'any statutory right', 'your inquirie', 'all information', 'any assistance', 'rectification / correction', 'our service', 'erasure', 'your email', 'Remove data', 'example', 'removal', 'their child', 'a restriction', 'other modification', 'an email', 'the same request', 'your request', 'the account information', 'certain information', 'a data protection officer', 'any personal data', 'such an objection', 'that data', 'deletion', 'your concern', 'more information', 'the current contact detail', 'the consent', 'the rectification', 'the privacy policy', 'thing', 'dispute', 'this request', 'icbc business service', 'the customer service channel', 'support', 'your imo chat history', 'your chat history', 'your entire account', 'a download', 'your account information', 'your personally identifiable information', 'a deletion', 'an official request', 'timely acknowledgment', 'interest', 'an error', 'an application', 'part', 'such an email', 'your medium account', 'issue', 'your mind', 'review', 'all data', 'assistance', 'any information', 'limitation', 'european user', 'correction', 'this page', 'request', 'any privacy or security question', 'menu', 'und informationsfreiheit  email', 'the name', 'our legal department', 'certain record', 'us mail', 'your Personal Data', 'any inaccurate or incomplete personal data', 'your telegram account', 'your question', 'the authorized person', 'our support team', 'our support', 'transparency', 'the content', 'tool', 'an account', 'certain account information', 'your privacy setting', 'a means', 'the data controller', 'supervisory authority', 'one copy', 'topic', 'personal data breach', 'your setting', 'such a request', 'the processing activitie', 'our processing activitie', 'file', 'these action', 'this privacy policy', "neptune 's studio", 'the amount', 'our contact information', 'the app', 'object', 'any complaint', 'the answer', 'such information', 'setting', 'your account setting', 'that consent', 'a gdpr complaint', 'resident', 'timely acknowledgement', 'your query', 'his login setting', 'cookie', 'an objection', 'an authority', 'its registered address', 'an electronic copy', 'a message', 'incorrect personal data', 'our sharing', 'request deletion', 'a personalized advertising experience', 'the minimum amount', 'appropriate consent', 'headspace customer support', 'headspace', 'the data', 'the lawfulness', 'the relevant supervisory authority', 'the ico', 'more detail', 'instruction', 'your usual residence', 'the event', 'your privacy', 'a machine readable copy', 'a query', 'the correction', 'that personal information', 'your information information', 'your e-mail preference', 'any request', 'the portability', 'your other right', 'marketing communication', 'a form', 'detail', 'a valid notice', 'measure', 'our driver', 'the latest postcode', 'a moment', 'our privacy and security guideline', 'my personal data', 'our customer care department', 'a link', 'the necessary personal data', 'the security', 'exercise', 'choice and control section', 'customer service', 'our online help', "the `` account '' section", "the `` account '' portion"]
# ['exercise', 'access', 'edit', 'control', 'limit', 'disable', 'object', 'delete', 'receive', 'entitle', 'process', 'data', 'in', 'lodge', 'govern', 'update', 'prevent', 'withdraw', 'oppose', 'therefore  the right', 'enforce', 'verify', 'correct', 'restrict', 'remove', 'detail', 'make', 'request access', 'request erasure', 'require', 'suspend', '18.3 right', 'request', 'have', 'terminate', 'irrespective', '18.7 right', 'transmit', 'a complaint', 'export', 'b ) right', 'c ) right', 'd ) right', 'e ) right', 'the right', 'provide', 'request correction', 'use', 'take', 'asus', 'ask', 'rely', 'decline', 'contact', 'modify', 'right', 'violate', 'store', 'opt', 'of', 'other data protection regulation', 'complete', '18  request', 'the personal information', 'revise', 'our right', 'erase', 'assert', 'revoke', 'file', 'seek', 'give', 'be', 'change', 'the existence', 'f ) right', 'g ) right', 'destroy', 'for', 'need', 'any request', 'rectify', 'send', 'refer', ': -email-', '-Email-', 'feel', 'appear', 'respond', 'email', 'hold', 'any other querie', 'resolve', 'right to data portability', 'e-mail address', 'collect', 'share', 'disclose', 'realize', 'want', 'restriction', 'contest', 'unsubscribe', 'include', 'amend', 'demand', 'wish', 'to', 'portability', 'manage', 'CA', 'any question', 'regard', 'through', 'review', 'raise', '-email-', 'apply', 'claim', 'support service', 'mention', 'by', 'mail', 's', 'keep', 'concern', 'enter', 'feature', 'follow', 'pende', 'base', 'carry', 'desire', 'like', '( ii ) acquisition processing restriction', 'opposition', 'download', 'write', 'hesitate', 'a right', '( ii ) a right', '( v ) a right', '( vii ) a right', 'rectification', 'what', 'email address', 'inform', 'issue', 'consider', 'question', 'Right', 'affect', 'complaint', 'update information', 'recover', '[ email ] netmarble', 'about', 'the origin', 'the purpose', 'data processing', '11.4 ) right', 'any inquirie', 'comment', 'retrieve', 'as well as the right', 'confirm', 'read', 'address', 'visit', 'supplement', 'consult', 'cancel', '3.request a copy', 'reach', 'stop', '( 1 ) right', '( 2 ) right', '( 3 ) right', '( 6 ) right', '( 7 ) right', 'obtain', 'part', '( information', 'Privacy Policy', 'Lodge', 'your right', 'direct', 'live', 'reque', 'preserve', 'vary', 'disclaim', 'note', 'stay', 'Feedback', 'deletion', 'remain', 'add', 'welcome', 'Inc', 'our contact email', 'let', 'lead', 'as', 'TEKHNOLODZHI', 'ooo support service', 'access / update tool', '/ right', 'fill', 'mean', 'identify', 'information', 'concerned', 'certain right', 'reject', 'move', 'any additional question', 'support', '# restriction', 'European Union', 'e-mail', 'please direct information request', 'or a right', 'notify', '15 right', 'enable', 'exist', '5 ) right', 'a concern', 'heres', 'all matter', 'imagitech.co.uk Notification', 'withdrawal', 'info', 'display', 'see', 'data controller', 'act', 'events privacy policy term', 'privacy policy', 'endeavour', 'Access', 'consent', 'transfer', 'any other question', 'at', 'learn', 'contact detail', '1.information', 's information', '7.your question', 'help', 'invite', 'how to access', '9.2 rectification', '9.6 objection', 'lodging complaint', 'the following right', 'find', 'reset', 'permit', 'buy', 'acquire', 'any issue', 'the event', 'satisfied', 'view', 'jeopardize', 'GDPR', 'questions  concern', 'allow', 'necessary', 'this Privacy Statement', 'your information']
# ['email', 'any time', 'this use', 'the processing', 'the right', 'our privacy email', 'processing', 'that processing', 'our use', 'limitation', 'another person', '-email-', 'certain feature', 'your device', 'correction', 'deletion', 'our processing', 'an email', '-Email-', 'your account', 'service', 'the scope', 'the e-mail address', 'the unsubscribe link', 'my.malwarebytes.com', 'the support widget', 'Personal Information', 'the metro customer service number', 'your account settings section', 'the google analytics opt-out browser add-on', 'the personal information', 'mopubs personalized advertising experience', 'such processing', 'rectification', 'erasure', 'the respective use', 'demand', 'our contact information', 'the data manager contact information section', '-PRON-', 'the game', 'the application', 'this online request form', 'your information', 'your device setting', 'the supervisory authority', 'the method', 'the following link', 'team', 'dpo', 'the email', 'your concern', 'our legitimate purpose', 'the address', 'the responsible supervisory authority', 'your game account', 'cookie', 'your first name', 'your personal information', 'support', 'a data protection authority', 'the bottom', 'additional processing', 'the following address', 'the European Economic Area', 'a request', 'the provided e-mail', 'the substance', 'restriction', 'the use', 'our online support form', 'the data', 'service support', 'betterme.tip', 'your personal data', 'the service', 'the end', 'your supervisory authority', 'any processing', 'support page', 'e-mail', 'your Personal Data', 'feature', 'your national data protection regulator', 'direct marketing', 'any profiling', 'all personal data', 'any time review', 'another data controller', 'your profile setting', 'get-headway.com', 'i', 'the meaning', 'our web form', 'help', 'the Facebook Settings', 'its website', 'netmarbles', 'the way', 'privacy', 'e-mail privacy', 'the app', 'the function', 'the customer service', 'the  delete chat history', 'the  delete imo account', 'our Customer Support', 'the personal data processing', 'your satisfaction', 'dataprotection', 'the approach', 'the customer service channel', 'your request', 'another party', 'the change', 'your profile', 'data portability', 'our email', 'our collection', 'the email address', 'contact', 'the privacy settings menu', "uber 's processing", 'Personal data', 'their website', 'your account setting', 'info', 'our website', 'your doubleugames account', 'the deactivation page', 'TESTFONI', 'the site', 'the specific content', 'mail', 'your setting', 'the instruction', 'the e-mail', 'either consent', 'the corresponding functionality', 'the contact detail', 'the my account', 'my profile', 'profiling', 'a ticket', 'its use', 'information', 'the relevant Supervisory Authority', 'no cost', 'datenschutz', 'the setting', 'the data controller', 'Brunnsgatan', 'our system', 'data processing', 'any processing operation', 'our support form', 'such a request', 'your mobile device setting', 'the contact', 'a data protection', 'the primary account holder', 'certain processing activitie', 'such posted content', 'headspace', 'www.itv.com/contactus', 'your browser setting', 'page', 'recent order', 'your enquirie', 'other it system', 'the support service', 'the contact information', 'the contact form', 'the opt-out instruction', 'the postal address', 'a notice', 'phone', 'the relevant third party', 'our privacy', 'other', 'the company', 'the Contact']
# ['contact', 'demand', 'ask', 'email', 'access', 'provide', 'update', 'call', 'inform', 'grant', 'destroy', 'withdraw', 'let', 'cancel', 'follow', 'send', 'retain', 'confirm', 'explain', 'write', 'redirect', 'carry', 'work', 'submit', 'lodge', 'inquire', 'use', 'delete', 'know', 'log', 'apply', 'visit', 'receive', 'disclose', 'notify', 'feel', 'express', 'exercise', 'collect', 'process', 'supply', 'switch', 'choose', 'advise', 'please', 'rectify']

