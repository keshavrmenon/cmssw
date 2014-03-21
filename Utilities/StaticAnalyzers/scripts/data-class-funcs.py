#! /usr/bin/env python
import re
datacl = re.compile("^class ")
mbcl = re.compile("(base|data) class")
farg = re.compile("\(\w+\)")
nsep = re.compile("\:\:")
topfunc = re.compile("::produce\(|::analyze\(|::filter\(::beginLuminosityBlock\(|::beginRun\(")
onefunc = re.compile("edm::one::ED(Producer|Filter|Analyzer)Base::(produce|filter|analyze)")
getfunc = re.compile("edm::eventsetup::EventSetupRecord::get\((.*)&\) const")
handle = re.compile("(.*)class edm::ES(.*)Handle<(.*)>")
statics = set()
toplevelfuncs = set()
onefuncs = set()
dataclassfuncs = set()
badclasses = set()
esdclasses = set()
flaggedclasses = set()

import networkx as nx
G=nx.DiGraph()
H=nx.DiGraph()


f = open('classes.txt.dumperft')
for line in f:
       if datacl.search(line) :
               classname = line.split("'")[1]
               esdclasses.add(classname)
f.close()

f = open('classes.txt.inherits')

for line in f:
       if datacl.search(line) :
               classname = line.split("'")[1]
               esdclasses.add(classname)
f.close()



f = open('class-checker.txt.sorted')
for line in f:
	if mbcl.search(line):
		fields = line.split("'")
		classname = fields[1]
		funcname = fields[3]
		if classname in esdclasses :
			badclasses.add(classname)
f.close()



f = open('classes.txt.dumperall.sorted')
for line in f :
	if mbcl.search(line) :
		fields = line.split("'")
		if fields[2] == ' member data class ':
			H.add_edge(fields[1],fields[3])
		if fields[2] == ' templated member data class ':
			H.add_edge(fields[1],fields[3])
		if fields[2] == ' base class ':
			H.add_edge(fields[1],fields[3])

f.close()



f = open('db.txt')

for line in f :
	fields = line.split("'")
	if fields[2] == ' calls function ' :
		G.add_edge(fields[1],fields[3])
		funcname = farg.split(fields[3])[0]
		if getfunc.search(fields[3]) :
			dataclassfuncs.add(fields[3])
		if topfunc.search(fields[1]):
			toplevelfuncs.add(fields[1])
	if fields[2] == ' overrides function ' :
		G.add_edge(fields[1],fields[3])
	if fields[2] == ' static variable ' :
		G.add_edge(fields[1],fields[3])
		statics.add(fields[3])
f.close()



for tfunc in toplevelfuncs:
	for key in G[tfunc].keys():
		if onefunc.search(key):
			onefuncs.add(tfunc)
			break



for esdclass in sorted(esdclasses):
	print "Event setup data class '"+esdclass+"'."
print

for badclass in sorted(badclasses):
	print "Event setup data class '"+badclass+"' is flagged."
print

objtree = nx.shortest_path(H)	

for badclass in sorted(badclasses):
	flaggedclasses.add(badclass)
	for esdclass in sorted(esdclasses):
		if H.has_node(badclass) and H.has_node(esdclass):
			if nx.has_path(H,esdclass, badclass) :
				print "Event setup data class '"+esdclass+"' contains or inherits from flagged class '"+badclass+"'."
				flaggedclasses.add(esdclass)
			
print

paths = nx.shortest_path(G)

for dataclassfunc in sorted(dataclassfuncs):
	for tfunc in sorted(toplevelfuncs):
		if nx.has_path(G,tfunc,dataclassfunc):
			m = getfunc.match(dataclassfunc)
			n = handle.match(m.group(1))
			if n : o = n.group(3)
			else : o = m.group(1)
			p = re.sub("class ","",o)
			dataclass = re.sub("struct ","",p)
			print "Event setup data '"+dataclass+"' is accessed in call stack '",
			for path in paths[tfunc][dataclassfunc]:
				print path+"; ",
			print "'."
			for flaggedclass in sorted(flaggedclasses):
				if re.search(flaggedclass,dataclass) :
					print "Flagged event setup data class '"+dataclass+"' is accessed in call stack '",
					for path in paths[tfunc][dataclassfunc]:
						print path+"; ",
					print "'."
