#import spacy
#nlp = spacy.load('en_core_web_lg')
#pip install spacy==2.3.7
from lib2to3.pygram import pattern_grammar
from pickletools import uint4
import spacy
from spacy.matcher import Matcher
import re
from enum import Enum
import networkx as nx
import matplotlib.pyplot as plt
from spacy.matcher import DependencyMatcher
import csv
from itertools import islice
#import pymongo
#import urllib.parse

#test goal: trigger word, pattern match
#input: one sentence for extract pattern, one test sentence for yes, another test sentence for no
#output: 

class AnnotationType(Enum): # label chunks in sentences
	NONE = 0
	RIGHT_VERB = 1
	ACCESS_VERB = 2
	RIGHT_NOUN = 3
	ACCESS_NOUN = 4
	SHARE_AND_COLLECT_VERB = 5


	@property
	def isRightOrAccess(self):
		return self in [AnnotationType.RIGHT_VERB, AnnotationType.ACCESS_VERB, AnnotationType.SHARE_AND_COLLECT_VERB]

	@property
	def isAccessVerb(self):
		return self == AnnotationType.ACCESS_VERB

	@property
	def isRightNoun(self):
		return self == AnnotationType.RIGHT_NOUN

	@property
	def isAccessNoun(self):
		return self == AnnotationType.ACCESS_NOUN

	@property
	def isNotNone(self):
		return self != AnnotationType.NONE

	@property
	def isNone(self):
		return self == AnnotationType.NONE

'''tag keyphrase'''
class KeyphraseTagger: # label chunks in sentences, can be replaced with spacy
	def __init__(self):
		self.rightNouns = ['right', 'copy', 'the right', 'a right', 'those rights', 'a complaint', 'a copy', 'your right', 'rights', 'the rights']
		self.rightVerbs = ['exercise', 'lodge', 'delete', 'access', 'correct', 'object', 'ask', 'correct', 'limit', 'corrected', 'deleted', 'exercised', 'objected', 'exercising', 'corrects', 'deletes']
		self.accessNouns = ['email', 'relevant supervisory authorities', 'access', 'that processing', 'processing', 'correction', 'limitation']
		self.accessVerbs = ['contact']

	def getTag(self, token):
		def isRightVerb(self, token):
			return token.pos == spacy.symbols.VERB and token.lemma_ in self.rightVerbs

		def isAccessVerb(self, token):
			return token.pos == spacy.symbols.VERB and token.lemma_ in self.accessVerbs

		#TODO do we really want "service|app|application" here? And not check if it is a subject or how related to the verb? 
		def isEntity(self, token):
			return True if token.text.lower() in [u'we', u'i', u'us', u'me', u'you'] or token.ent_type_ in [u'PERSON', u'ORG'] else False

		def isRightNoun(self, token):
			#return token.pos == spacy.symbols.NOUN and token.lemma_ in self.rightNouns
			return token.pos == spacy.symbols.NOUN and any(rightNoun in token.lemma_ for rightNoun in self.rightNouns)


		def isAccessNoun(self, token): # TODO do we want to allow multi-token matches or just merge?
			return token.pos == spacy.symbols.NOUN and token.lemma_ in self.accessNouns

		#############################
		if isRightVerb(self, token):
			return AnnotationType.RIGHT_VERB
		elif isAccessVerb(self, token):
			return AnnotationType.ACCESS_VERB
		elif isRightNoun(self, token):
			return AnnotationType.RIGHT_NOUN
		elif isAccessNoun(self, token):
			return AnnotationType.ACCESS_NOUN
		return AnnotationType.NONE

	def tagSentence(self, sentence): # to do: modified with spacy, input sentences, output sentences
		res = {}
		for token in sentence:
			tag = self.getTag(token)
			if tag.isNotNone:
				res[(token.i, token)] = self.getTag(token)
		return res

class DependencyGraphConstructor: # construch structure tree
	@staticmethod
	def getConjugatedVerbs(sentence, targetTok = None):
		def isComma(token):
			return token.pos_ == u'PUNCT' and token.text == u','

		def isCConj(token):
			return token.pos == spacy.symbols.CCONJ and token.lemma_ in [u'and', u'or', u'nor']

		def isNegation(token):
			return token.dep == spacy.symbols.neg

		def getConjugatedVerbsInternal(results, token):
			if token.pos == spacy.symbols.VERB:
				results.append(token)
			for tok in token.children:
				if tok.i < token.i:#Ensure we only look at children that appear AFTER the token in the sentence
					continue
				if tok.dep == spacy.symbols.conj and tok.pos == spacy.symbols.VERB:
					if not getConjugatedVerbsInternal(results, tok):
						return False
				elif not (isComma(tok) or isCConj(tok) or isNegation(tok)):
					return False
			return True

		def isTokenContainedIn(token, conjugatedVerbs):
			for vbuffer in conjugatedVerbs:
				if token in vbuffer:
					return True
			return False

		conjugatedVerbs = []
		vbuffer = []
		for token in sentence:
			if token.pos == spacy.symbols.VERB:
				# Make sure we didn't already cover the verb...
				if isTokenContainedIn(token, conjugatedVerbs):
					continue

				vbuffer = []
				getConjugatedVerbsInternal(vbuffer, token)
				if len(vbuffer) > 1:
					conjugatedVerbs.append(vbuffer)

		if targetTok != None:
			for vbuffer in conjugatedVerbs:
				if targetTok in vbuffer:
					return vbuffer
			return []
		return conjugatedVerbs

	@staticmethod
	def getRootNodes(graph):
		def hasNoInEdges(graph, node):
			return len([n for n in graph.in_edges(node)]) == 0
		root = [ n for n in graph.nodes if hasNoInEdges(graph, n) ]
		return root # Could be multiple trees...

	@staticmethod
	def getNodeAnnotationTag(node):
		return node[2]

	@staticmethod
	def isVerb(graph, node):
		return graph.nodes[node]['pos'] == u'VERB'

	@staticmethod
	def areAnnotationTagsEqual(node1, node2):
		t1 = DependencyGraphConstructor.getNodeAnnotationTag(node1)
		t2 = DependencyGraphConstructor.getNodeAnnotationTag(node2)
		return t1 == t2 or t1.isRightOrAccess and t2.isRightOrAccess


	@staticmethod
	def isVerbNegated(token, sentence):
		def isVerbNegatedInternal(token):
			return any(t.dep == spacy.symbols.neg for t in token.children)

		if isVerbNegatedInternal(token):
			return True

		# Check if verb is part of conjugated verb phrase, if so, check if any of those are negated
		conjugatedVerbs = DependencyGraphConstructor.getConjugatedVerbs(sentence, token)
		for tok in conjugatedVerbs:
			if isVerbNegatedInternal(tok):
				return True

		# Check if verb is xcomp, if so check if prior verb is negated?
		#TODO should also do advcl
		if token.dep == spacy.symbols.xcomp or token.dep == spacy.symbols.advcl:
			return DependencyGraphConstructor.isVerbNegated(token.head, sentence)
		return False

	@staticmethod
	def convertDTreeToNxGraph(sentence, tokenTags):
		def addNode(key, node, graph, sentence):
			if key not in graph:
				negation = False
				if key[2].isRightOrAccess:
					graph.add_node(key, label=u'{}({}{}) - {}'.format(key[2], node.lemma_, u' - NOT' if negation else u'', node.i), tag = key[2], lemma = node.lemma_, lemmaList=[node.lemma_ if node.lemma_ != u'-PRON-' else node.text.lower()], dep=node.dep_, pos=node.pos_, neg=negation, docStart=node.i, docEnd=node.i)
				else:
					graph.add_node(key, label=u'{}({}) - {}'.format(key[2], node.lemma_, node.i), tag = key[2], lemma = node.lemma_, lemmaList=[node.lemma_ if node.lemma_ != u'-PRON-' else node.text.lower()], dep=node.dep_, pos=node.pos_, neg=negation, docStart=node.i, docEnd=node.i)

		def convertDTreeToNxGraphInternal(root, graph, tokenTags, sentence):
			rkey = DependencyGraphConstructor.getKey(root, tokenTags)

			if rkey not in graph:
				addNode(rkey, root, graph, sentence)

			for c in root.children:
				ckey = DependencyGraphConstructor.getKey(c, tokenTags)
				if ckey not in graph:
					addNode(ckey, c, graph, sentence)

				graph.add_edge(rkey, ckey, label = c.dep_)
				convertDTreeToNxGraphInternal(c, graph, tokenTags, sentence)
				
		##############
		dgraph = nx.DiGraph()
		convertDTreeToNxGraphInternal(sentence.root, dgraph, tokenTags, sentence)
		pos = nx.spring_layout(dgraph, k = 0.5)
		plt.clf()
		nx.draw(dgraph, with_labels=True, node_color='skyblue', node_size=200, font_size= 8, edge_cmap=plt.cm.Blues,pos=pos)
		plt.show()    
		plt.savefig("./images/graph_convertDTreeToNxGraph.png")
		return dgraph

	@staticmethod
	def drawGraph(g, filename):
#		try:
#			A = nx.drawing.nx_agraph.to_agraph(g)
#			A.draw(filename, prog='dot', args='-Granksep=2.0')
#		except:# FIXME unicode error here for some reason...
#			pass
		return
	
	@staticmethod
	def getKey(root, tokenTags):

		tKey = (root.i, root)
		tag = AnnotationType.NONE if tKey not in tokenTags else tokenTags[tKey]
		return (root.i, root, tag)

	@staticmethod
	def getSimplifiedDependencyGraph(sentence, tokenTags):
		def getPathBetweenNodes(g, itok, jtok, tokenTags):
			pathNodes = nx.shortest_path(g.to_undirected(), DependencyGraphConstructor.getKey(itok, tokenTags), DependencyGraphConstructor.getKey(jtok, tokenTags))
			return g.subgraph(pathNodes).copy()

		##############################
		if len(tokenTags) <= 1: # Need two or more tokens...
			return None

		g = DependencyGraphConstructor.convertDTreeToNxGraph(sentence, tokenTags)
		graphs = []
		taggedTokens = [(token, tokenTags[(token.i, token)]) for i,token in tokenTags]
		for i,(itok,itag) in enumerate(taggedTokens):
			for j,(jtok, jtag) in enumerate(taggedTokens[i+1:]):
				graphs.append(getPathBetweenNodes(g, itok, jtok, tokenTags))

		#Do not prune subjects and objects...
		#TODO is it just share verbs or all?
		for i,(itok,itag) in enumerate(taggedTokens):
			if itag.isRightOrAccess:
				for _, dst in g.out_edges(DependencyGraphConstructor.getKey(itok, tokenTags)):
					if dst[1].dep in [spacy.symbols.dobj, spacy.symbols.nsubj, spacy.symbols.nsubjpass] and dst[2].isNone:
						graphs.append(getPathBetweenNodes(g, itok, dst[1], tokenTags))

		#################################

		g = nx.compose_all(graphs)
		#DependencyGraphConstructor.collapseConjugatedVerbs(g, sentence, tokenTags)
		# Prune non-attached nodes...
		#DependencyGraphConstructor.pruneUnattachedNodes(g)
		#DependencyGraphConstructor.collapseConjugatedEntities(g, sentence, tokenTags)
		#DependencyGraphConstructor.pruneNonSharingVerbs(g)
		#DependencyGraphConstructor.drawGraph(g, 'simplified_graph.png')
		pos = nx.spring_layout(g, k = 0.5)
		plt.clf()
		nx.draw(g, with_labels=True, node_color='skyblue', node_size=200, font_size= 8, edge_cmap=plt.cm.Blues, pos=pos)
		plt.show()    
		plt.savefig("./images/graph_getSimplifiedDependencyGraph.png")		
		return g
class GraphCompare:
	@staticmethod
	def nmatchCallback(n1, n2):
		def getVerbGroup(lemmaList):
			groups = [[u'contact'],
					[u'exercise'],
									   ]
			results = []
			for lemma in lemmaList:
				for i,g in enumerate(groups):
					if lemma in g:
						results.append(i)
			return set(results) #This should really never happen as long as the two lists in sync

		if n1['tag'].isRightOrAccess and n2['tag'].isRightOrAccess:
			vg1 = getVerbGroup(n1['lemmaList'])
			vg2 = getVerbGroup(n2['lemmaList'])
			return len(vg1.intersection(vg2)) > 0
#			return getVerbGroup(n1['lemmaList']) == getVerbGroup(n2['lemmaList'])
			#return n1['dep'] == n2['dep'] and groupsMatch #TODO should we ensure verb matches?
		if n1['tag'].isNone and n2['tag'].isNone and n1['pos'] == u'ADP' and n2['pos'] == u'ADP':
			return n1['tag'] == n2['tag'] and n1['dep'] == n2['dep'] and n1['lemma'] == n2['lemma']
		if n1['tag'].isNone and n2['tag'].isNone and n1['pos'] == u'VERB' and n2['pos'] == u'VERB':
			if n1['dep'] == u'ROOT' or n2['dep'] == u'ROOT':
				return n1['tag'] == n2['tag'] and n1['pos'] == n2['pos']
		return n1['tag'] == n2['tag'] and n1['dep'] == n2['dep']

	@staticmethod
	def ematchCallback(n1, n2):
		return n1['label'] == n2['label']

'''complex event pattern '''
class EventsExtraction:
	def __init__(self, nlpModel):
		self.parser = nlpModel
		self.tagger = KeyphraseTagger()
		self.patterns = []

	def containsRightsOrAccess(self, tags):
		return any(tags[k].isRightOrAccess for k in tags)

	'''creat pattern'''
	def create_pattern(self, paragraph):
		doc = self.parser(paragraph)
		with doc.retokenize() as retokenizer:
			for chunk in doc.noun_chunks:
				retokenizer.merge(chunk, attrs={'LEMMA': chunk.root.lemma_, 'TAG':chunk.root.tag_ })

		patterns = []
		for sent in doc.sents:
			tags = self.tagger.tagSentence(sent) #
			print('sent: ', sent)
			print('tags: ', tags)
			if len(tags) <= 0: # use the taggers to find targeted sentences that contains the ()
				continue
			if not self.containsRightsOrAccess(tags):
					continue
			
			#merge phrases
			
			#for token in sent:
			#	print(token.text, token.pos_, token.dep_, token.head.text)			
			pattern = DependencyGraphConstructor.getSimplifiedDependencyGraph(sent,tags)
			
			# Load spacy's dependency tree into a networkx graph
			#edges = []




			#graph = nx.Graph(edges)

			# https://networkx.github.io/documentation/networkx-1.10/reference/algorithms.shortest_paths.html
			#print(nx.shortest_path_length(graph, source='contact', target='EMAIL'))
			#print(nx.shortest_path(graph, source='contact', target='EMAIL'))
			#for token in doc:
			#	print(token.text, token.dep_, token.head.text, token.head.pos_,[child for child in token.children])
			#pattern = DependencyGraphConstructor.getSimplifiedDependencyGraph(sent, tags)
			self.patterns.append(pattern)
			#self.matcher.add("RIGHTS", [pattern])
		#return patterns

	'''split sentences'''
	def split_sents(self, content):
		return [sentence for sentence in re.split(r'[?!.;:\n\r]', content) if sentence]

	'''pattern match'''
	def pattern_match(self, sent):
		#datas = {}
		results = []
		doc = self.parser(sent)
		with doc.retokenize() as retokenizer:
			for chunk in doc.noun_chunks:
				retokenizer.merge(chunk, attrs={'LEMMA': chunk.root.lemma_, 'TAG':chunk.root.tag_ })

		for sent in doc.sents:
			tags = self.tagger.tagSentence(sent)
			print('sent: ', sent)
			print('tags: ', tags)
			if len(tags) <= 0:
				continue
			if not self.containsRightsOrAccess(tags):
				continue
			pattern = DependencyGraphConstructor.getSimplifiedDependencyGraph(sent, tags)
			#nx.algorithms.isomorphism.GraphMatcher(pattern, p, node_match=GraphCompare.nmatchCallback, edge_match=GraphCompare.ematchCallback)
			def getTagsFromGraph(depGraph):
				if depGraph: # added new
					return set([ n[2] for n in depGraph.nodes if n[2].isNotNone ])
			for p in self.patterns:
				#matcher pattern 
				print("graph matching")
				ptags = getTagsFromGraph(p)
				GM = nx.algorithms.isomorphism.GraphMatcher(pattern, p, node_match=GraphCompare.nmatchCallback, edge_match=GraphCompare.ematchCallback)
				for subgraph in GM.subgraph_isomorphisms_iter():
					#nx.draw(subgraph, with_labels=True, node_color='skyblue', node_size=1500, edge_cmap=plt.cm.Blues)
					#plt.show()                         
					#plt.savefig("./images/match.png")
					print(type(subgraph))
					print(subgraph)

	'''extract tuples'''
	def extract_tuples(self, sent):
		condition_tuples = self.pattern_match(self.condition_patterns, sent)
		seq_tuples = self.pattern_match(self.seq_patterns, sent)
		return condition_tuples, seq_tuples

	'''main'''
	def extract_main(self, content):
		#sents = self.split_sents(content)
		doc = self.parser(content)
		datas = []
		for sent in doc.sents:
			print('sent: ', sent)
			print('type(sent): ', type(sent))
			data = {}
			data['sent'] = sent

			condition_tuples, seq_tuples= self.extract_tuples(sent)
			if condition_tuples:
				data['type'] = 'condition'
				data['tuples'] = condition_tuples
			if seq_tuples:
				data['type'] = 'seq'
				data['tuples'] = seq_tuples
			if 'type' in data:
				datas.append(data)
		return datas

if __name__ == '__main__':
	nlp = spacy.load('en_core_web_lg') #self.defined entity 
	print(nlp.pipe_names)
	# parapraph = "If you have any questions related to data protection , or if you wish to exercise your rights , please contact EMAIL or the address stated above , adding the keyword Data Protection . "
	# test_sentence = 'if you wish to exercise your rights , please contact EMAIL '
	# extractor = EventsExtraction(nlpModel=nlp)
	# extractor.create_pattern(parapraph)
	# extractor.pattern_match(test_sentence)

	sentences = []
	ema = r"[a-zA-Z0-9_.+-]+ @ [ a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
	with open('./input/user_rights_sentences_dedup_test_output.tsv') as csvfile:
		reader = csv.reader(csvfile,delimiter='\t')
		for row in reader:
			email_without_whitespace = "".join(re.findall(ema,row[1])).replace(" ","")
			sentence = re.sub(ema, email_without_whitespace, row[1])
			sentences.append(sentence)	

	for sentence in sentences[:15]:
		extractor = EventsExtraction(nlpModel=nlp)
		extractor.create_pattern(sentence)
		extractor.pattern_match(sentence)
