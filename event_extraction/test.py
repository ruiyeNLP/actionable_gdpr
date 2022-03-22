from lib2to3.pygram import pattern_grammar
import spacy
from spacy.matcher import Matcher
import re
from enum import Enum
import networkx as nx
import matplotlib.pyplot as plt
from spacy.matcher import DependencyMatcher
#import pymongo
#import urllib.parse

#test goal: trigger word, pattern match
#input: one sentence for extract pattern, one test sentence for yes, another test sentence for no
#output: 

class AnnotationType(Enum):
	NONE = 0
	DATA_OBJ = 1
	RIGHTS_VERB = 2
	ACCESS_VERB = 3
	SHARE_AND_COLLECT_VERB = 4
	ENTITY = 5

	@property
	def isRightsOrAccess(self):
		return self in [AnnotationType.RIGHTS_VERB, AnnotationType.ACCESS_VERB, AnnotationType.SHARE_AND_COLLECT_VERB]

	@property
	def isCollect(self):
		return self == AnnotationType.ACCESS_VERB

	@property
	def isData(self):
		return self == AnnotationType.DATA_OBJ

	@property
	def isEntity(self):
		return self == AnnotationType.ENTITY

	@property
	def isNotNone(self):
		return self != AnnotationType.NONE

	@property
	def isNone(self):
		return self == AnnotationType.NONE

'''tag keyphrase'''
class KeyphraseTagger:
	def __init__(self):
		self.rightsVerbs = [u'exercise']
		self.accessVerbs = [u'contact']

	def getTag(self, token):
		def isShareVerb(self, token):
			return token.pos == spacy.symbols.VERB and token.lemma_ in self.rightsVerbs

		def isCollectVerb(self, token):
			return token.pos == spacy.symbols.VERB and token.lemma_ in self.accessVerbs

		#TODO do we really want "service|app|application" here? And not check if it is a subject or how related to the verb? 
		def isEntity(self, token):
			return True if token.text.lower() in [u'we', u'i', u'us', u'me', u'you'] or token.ent_type_ in [u'PERSON', u'ORG'] else False

		def isDataObject(self, token): # TODO do we want to allow multi-token matches or just merge?
			return token.ent_type_ == u'DATA' and token.pos != spacy.symbols.VERB

		#############################
		if isShareVerb(self, token):
			return AnnotationType.RIGHTS_VERB
		elif isCollectVerb(self, token):
			return AnnotationType.ACCESS_VERB
		elif isDataObject(self, token):
			return AnnotationType.DATA_OBJ
		elif isEntity(self, token):
			return AnnotationType.ENTITY
		return AnnotationType.NONE

	def tagSentence(self, sentence):
		res = {}
		for token in sentence:
			tag = self.getTag(token)
			if tag.isNotNone:
				res[(token.i, token)] = self.getTag(token)
		return res

class DependencyGraphConstructor:
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
		return t1 == t2 or t1.isShareOrCollect and t2.isShareOrCollect

	@staticmethod
	def collapseConjugatedVerbs(graph, sentence, tokenTags):
		def getNewTag(n1, n2):
			if n2[2] != AnnotationType.SHARE_AND_COLLECT_VERB and n1[2].isNotNone and n1[2] != n2[2]:
				if n2[2].isNone:
					return n1[2]
				elif (n1[2] == AnnotationType.SHARE_VERB and n2[2] == AnnotationType.COLLECT_VERB) or (n1[2] == AnnotationType.COLLECT_VERB and n2[2] == AnnotationType.SHARE_VERB) or n1[2] == AnnotationType.SHARE_AND_COLLECT_VERB:
					return AnnotationType.SHARE_AND_COLLECT_VERB
			return n2[2]

		def replaceNode(graph, origNode, newNode):
			# Add out edges
			for s,t in graph.out_edges(origNode):
				graph.add_edge(newNode, t, label = graph[s][t]['label'])

			# Add in edges
			for s,t in graph.in_edges(origNode):
				graph.add_edge(s, newNode, label = graph[s][t]['label'])
			
			# Remove node from graph
			graph.remove_node(origNode)
		
		def addNewVerbNode(graph, node1, node2, docStart, docEnd):
			newTag = getNewTag(node1, node2) # Get new annotation tag
			newKey = (node2[0], node2[1], newTag)#FIXME this doesn't really represent the updated tag...
			negation = graph.node[node2]['neg'] # CHECKME can node1 ever be negated if node2 is not?
			newLemma = u'{},{}'.format(graph.nodes[node1]['lemma'], graph.nodes[node2]['lemma'])
			newNodeLabel = u'{}({}{})'.format(newTag, newLemma, u' - NOT' if negation else u'')
			newLemmaList = []
			newLemmaList.extend(graph.nodes[node1]['lemmaList'])
			newLemmaList.extend(graph.nodes[node2]['lemmaList'])
			if newKey != node2:
				graph.add_node(newKey, label=newNodeLabel, lemma=newLemma, lemmaList=newLemmaList, tag = newTag, dep=node2[1].dep_, pos=node2[1].pos_, neg=negation, docStart=docStart, docEnd=docEnd)
				return (newKey, True)
			graph.nodes[node2]['lemma'] = newLemma
			graph.nodes[node2]['label'] = newNodeLabel
			graph.nodes[node2]['neg'] = negation
			graph.nodes[node2]['lemmaList'] = newLemmaList
			graph.nodes[node2]['tag'] = newTag
			graph.nodes[node2]['startDoc'] = docStart
			graph.nodes[node2]['endDoc'] = docEnd
			return (node2, False)

		######################################
		# Let's just walk the damn graph...
		def traverseDownward(graph, node):
			outEdges = [ dst for src,dst in graph.out_edges(node) ] # Treat it as a stack instead...
			while len(outEdges) > 0:
				n = outEdges.pop()
				if graph[node][n]['label'] == u'conj' and DependencyGraphConstructor.areAnnotationTagsEqual(node, n) and DependencyGraphConstructor.isVerb(graph, node) and DependencyGraphConstructor.isVerb(graph, n):
					#TODO the key changes due to the annotation tag potentially changing...
					#TODO ensure separation
					nodeTok = node[1]
					nodeChildTok = n[1]
					if nodeChildTok in DependencyGraphConstructor.getConjugatedVerbs(sentence, targetTok = nodeTok):
						#Remove link from X --> Y
						graph.remove_edge(node, n)
						# Get new Tag
						newTag = getNewTag(node, n)
						if newTag == node:
							graph.nodes[node]['lemma'] = u'{},{}'.format(graph.nodes[node]['lemma'], graph.nodes[n]['lemma'])
							graph.nodes[node]['lemmaList'].extend(graph.nodes[n]['lemmaList'])
							graph.nodes[node]['label'] = u'{}({}) - {}'.format(node[2], graph.nodes[node]['lemma'], node[1].i)
							# Add all out links from Y --> Z to X --> Z (return all nodes, so we can add to outEdges...)
							for src,dst in graph.out_edges(n):
								graph.add_edge(node, dst, label = graph[src][dst]['label'])
								graph.remove_edge(src,dst)
								outEdges.append(dst)
							graph.remove_node(n)
						else:
							# Add new tag...
							startDoc = nodeTok.i if nodeTok.i < nodeChildTok.i else nodeChildTok.i
							endDoc = nodeTok.i if nodeTok.i > nodeChildTok.i else nodeChildTok.i
							newNode,addedNewNode = addNewVerbNode(graph, n, node, startDoc, endDoc)

							if addedNewNode:
								# Add in edges
								for s,t in graph.in_edges(node):
									graph.add_edge(s, newNode, label = graph[s][t]['label'])
									graph.remove_edge(s,t)

								# Add out edges
								for s,t in graph.out_edges(node):
									graph.add_edge(newNode, t, label = graph[s][t]['label'])
									graph.remove_edge(s,t)

							if not addedNewNode:
								newNode = node

							# Add all out links from Y --> Z to X --> Z (return all nodes, so we can add to outEdges...)
							for src,dst in graph.out_edges(n):
								graph.add_edge(newNode, dst, label = graph[src][dst]['label'])
								graph.remove_edge(src,dst)
								outEdges.append(dst)

							# Remove node from graph
							if addedNewNode:
								graph.remove_node(node)
							node = newNode
							graph.remove_node(n)
						continue
				traverseDownward(graph, n)
		roots = DependencyGraphConstructor.getRootNodes(graph)
		for r in roots:
			traverseDownward(graph, r)

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
				if key[2].isRightsOrAccess:
					negation = DependencyGraphConstructor.isVerbNegated(node, sentence)
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
		plt.show()    
		plt.savefig("graph_convertDTreeToNxGraph.png")
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
		#for i,(itok,itag) in enumerate(taggedTokens):
		#	if itag.isRightsOrAccess:
	    #			for _, dst in g.out_edges(DependencyGraphConstructor.getKey(itok, tokenTags)):
	    #				if dst[1].dep in [spacy.symbols.dobj, spacy.symbols.nsubj, spacy.symbols.nsubjpass] and dst[2].isNone:
	    #					graphs.append(getPathBetweenNodes(g, itok, dst[1], tokenTags))

		#################################

		g = nx.compose_all(graphs)

		DependencyGraphConstructor.collapseConjugatedVerbs(g, sentence, tokenTags)
		nx.draw(g)
		plt.show()    
		plt.savefig("graph_getSimplifiedDependencyGraph.png")

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

		if n1['tag'].isRightsOrAccess and n2['tag'].isRightsOrAccess:
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
        #self.matcher = DependencyMatcher(nlp.vocab)

    def containsRightsOrAccess(self, tags):
        return any(tags[k].isRightsOrAccess for k in tags)

    '''creat pattern'''
    def create_pattern(self, paragraph):
        doc = self.parser(paragraph)
        patterns = []
        for sent in doc.sents:
            tags = self.tagger.tagSentence(sent)
            print('sent: ', sent)
            print('tags: ', tags)
            if len(tags) <= 0:
                continue
            if not self.containsRightsOrAccess(tags):
                continue
            pattern = DependencyGraphConstructor.getSimplifiedDependencyGraph(sent, tags)
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

            for p in self.patterns:
                #matcher pattern 
                print("graph matching")
                print(nx.is_matching(pattern, p))
                #print(self.matcher(sent))
                #print(nx.algorithms.isomorphism.GraphMatcher(pattern, p, node_match=GraphCompare.nmatchCallback, edge_match=GraphCompare.ematchCallback))
        return results

                #extract tuple in the pattern 
        #for p in patterns:
        #    matcher = Matcher(self.parser.vocab)
        #    matcher.add('test', [p])
        #    matches = matcher(sent)
        #    print([sent[start:end] for match_id, start, end in matches])
        #    #ress = p.findall(sent)
        #    #if ress:
        #    #    for res in ress:
        #    #        data = {'pre_wd': res[0], 'pre_part': res[1], 'post_wd': res[2], 'post_part ': res[3]}
        #    #        len_res = len(res[0] + res[2])
        #    #        if len_res > max:
        #    #            datas = data
        #    #            max = len_res
        #return results
        #return datas
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
    nlp = spacy.load('./')
    print(nlp.pipe_names)
    parapraph = "if you wish to exercise your rights , please contact EMAIL. "
    extractor = EventsExtraction(nlpModel=nlp)
    extractor.create_pattern(parapraph)
    extractor.pattern_match(parapraph)
    #datas = extractor.extract_main(parapraph)
    #print(datas)
