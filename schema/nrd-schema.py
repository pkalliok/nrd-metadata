#!/usr/bin/env python
# coding: utf-8

from rdflib import *
import csv
import sys
import datetime
import urllib2

CSVURL='https://docs.google.com/spreadsheet/ccc?key=0AimHYUU2ktEydGdjSEhNbVVORmJFaUFTR0kwZWVUblE&output=csv'
request = urllib2.Request(CSVURL)
cookie_handler = urllib2.HTTPCookieProcessor()
redirect_handler = urllib2.HTTPRedirectHandler()
opener = urllib2.build_opener(redirect_handler,cookie_handler)
cu = opener.open(request)

OWL = Namespace('http://www.w3.org/2002/07/owl#')
SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
DC = Namespace('http://purl.org/dc/elements/1.1/')
DCT = Namespace('http://purl.org/dc/terms/')
NRD = Namespace('http://purl.org/net/nrd#')
VOID = Namespace('http://rdfs.org/ns/void#')
FOAF = Namespace('http://xmlns.com/foaf/0.1/')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
FP = Namespace('http://downlode.org/Code/RDF/File_Properties/schema#')
ARPFO = Namespace('http://vocab.ox.ac.uk/projectfunding#')

NS = {
  'nrd': NRD,
  'dc': DC,
  'dct': DCT,
  'org': Namespace('http://www.w3.org/ns/org#'),
  'skos': SKOS,
  'rdfs': Namespace('http://www.w3.org/2000/01/rdf-schema#'),
  'owl': OWL,
  'xsd': Namespace('http://www.w3.org/2001/XMLSchema#'),
  'schema': Namespace('http://schema.org/'),
  'void': VOID,
  'foaf': FOAF,
  'dcat': DCAT,
  'fp': FP,
  'arpfo': ARPFO,
}

typemap = {
  'rdfs:Literal': (OWL.DatatypeProperty, RDFS.Literal),
  'xsd:string': (OWL.DatatypeProperty, XSD.string),
  'xsd:dateTime': (OWL.DatatypeProperty, XSD.dateTime),
  'xsd:integer': (OWL.DatatypeProperty, XSD.integer),
}
propmap = {}

m = Graph()

for prefix, ns in NS.items():
  m.namespace_manager.bind(prefix, ns)

def to_uri(name):
  if ':' in name:
    prefix, ln = name.split(':')
    return NS[prefix][ln]
  raise ValueError, name

reader = csv.reader(cu)
csvdata = []
for row in list(reader)[1:]:
  if len(row) == 0: continue
  
  # pad with blanks
  row.extend([''] * (8 - len(row)))
  csvdata.append(row)

# 1st pass: expand Finnish -> English type and property maps with local types
for row in csvdata:
  clname = row[0]
  propname = row[1]
  lname = row[3]
  
  if not lname: continue
  if propname:
    propmap[propname] = NS['nrd'][lname]
  else:
    typemap[clname] = (OWL.ObjectProperty, NS['nrd'][lname])

# 2nd pass: build RDF data
for row in csvdata:
  clname = row[0]
  propname = row[1]
  typename = row[2]
  lname = row[3]
  engname = row[4]
  findesc = row[5].strip()
  engdesc = row[6].strip()
  upper = row[7]
  
  if not clname:
    continue
  if not lname:
    continue
    
  isclass = False
    
  if not propname: # class def
    isclass = True
    finname = clname
  else:
    finname = propname
  
  uri = NS['nrd'][lname]

  if isclass:
    m.add((uri, RDF.type, OWL.Class))
    m.add((uri, RDF.type, RDFS.Class))
  else:
    typespec = typemap.get(typename)
    if typespec is None:
      typespec = (OWL.ObjectProperty, to_uri(typename))
    pt, range = typespec
    m.add((uri, RDF.type, pt))
    m.add((uri, RDFS.range, range))

    pt, domain = typemap[clname]
    m.add((uri, RDFS.domain, domain))

  if upper:
    for u in upper.split(','):
      upperuri = to_uri(u.strip())
      if isclass:
        m.add((uri, RDFS.subClassOf, upperuri))
      else:
        m.add((uri, RDFS.subPropertyOf, upperuri))
  
  m.add((uri, RDFS.label, Literal(finname, 'fi')))
  m.add((uri, RDFS.label, Literal(engname, 'en')))
  if findesc:
    m.add((uri, RDFS.comment, Literal(findesc, 'fi')))
  if engdesc:
    m.add((uri, RDFS.comment, Literal(engdesc, 'en')))

# remove multiple rdfs:domain statements
dommap = {}
for prop, cl in m.subject_objects(RDFS.domain):
  dommap.setdefault(prop, [])
  dommap[prop].append(cl)

for prop, classes in dommap.items():
  if len(classes) > 1:
    m.remove((prop, RDFS.domain, None))
    m.remove((prop, RDFS.comment, None))

print "# National Research Datasets RDF Schema"
print "# Tutkimuksen tietoaineistot (TTA) RDF-skeema"
print "# version", datetime.date.today().isoformat()
print 

nrd = URIRef(NS['nrd'][:-1]) # URI of namespace without the hash

m.add((nrd, RDF.type, OWL.Ontology))
m.add((nrd, RDFS.label, Literal("Tutkimuksen tietoaineistot metatietoskeema", 'fi')))
m.add((nrd, RDFS.label, Literal("National Research Datasets metadata schema", 'en')))
m.add((nrd, DC.title, Literal("Tutkimuksen tietoaineistot metatietoskeema", 'fi')))
m.add((nrd, DC.title, Literal("National Research Datasets metadata schema", 'en')))
m.add((nrd, DC.date, Literal(datetime.date.today().isoformat(), datatype=XSD.date)))
# FIXME, these violate DCT range declarations
m.add((nrd, DC.creator, Literal("Osma Suominen")))
m.add((nrd, DC.contributor, Literal("Panu Kalliokoski")))

print m.serialize(format='n3'),
