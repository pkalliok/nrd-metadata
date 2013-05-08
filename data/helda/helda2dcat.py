#!/usr/bin/env python

from rdflib import *
from xml.etree import ElementTree
import sys

OAI = "http://www.openarchives.org/OAI/2.0/"

DCAT = Namespace("http://www.w3.org/ns/dcat#")


g = Graph()
tree = ElementTree.parse(sys.argv[1])
root = tree.getroot()

for rec in root.findall(".//{%s}record" % OAI):
  print rec
  meta = rec.find("{%s}metadata" % OAI)
  print meta
  
  
