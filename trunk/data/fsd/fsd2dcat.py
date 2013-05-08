#!/usr/bin/env python

from rdflib import *
from lxml.etree import parse
import sys

FSD = Namespace("http://example.org/fsd/") # FIXME
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

g = Graph()
g.namespace_manager.bind('fsd', FSD)
g.namespace_manager.bind('dcat', DCAT)
g.namespace_manager.bind('dct', DCT)
g.namespace_manager.bind('foaf', FOAF)
g.namespace_manager.bind('xsd', XSD)
tree = parse(sys.argv[1])
root = tree.getroot()

def node_lang(node):
  """return the xml:lang value of the given node, possibly inherited"""
  return node.xpath('(ancestor-or-self::*/@xml:lang)[1]')[0]

def html2text(node):
  """return the text contents of the node, stripped of HTML markup"""
  return lxml.html.fragment_fromstring(node.text)


# ID / URI for Dataset and CatalogRecord
idno = root.find('.//IDNo')
dataset = FSD["dataset" + idno.text]
record = FSD["record" + idno.text]
g.add((dataset, RDF.type, DCAT.Dataset))
g.add((record, RDF.type, DCAT.CatalogRecord))
g.add((record, FOAF.primaryTopic, dataset))

# Dataset title / parallel title
for title in root.findall('stdyDscr//titl') + root.findall('stdyDscr//parTitl'):
  g.add((dataset, DCT['title'], Literal(title.text, node_lang(title))))

# Record title / parallel title
for title in root.findall('docDscr//titl') + root.findall('docDscr//parTitl'):
  g.add((record, DCT['title'], Literal(title.text, node_lang(title))))

# Record date
date = root.find('.//prodDate')
g.add((record, DCT.modified, Literal(date.get('date'), datatype=XSD.date)))

# Dataset description
abstract = root.findtext('.//abstract')
print abstract
g.add((dataset, DCT.description, Literal(abstract.text, node_lang(abstract))))


g.serialize(format='turtle', destination=sys.stdout)  
