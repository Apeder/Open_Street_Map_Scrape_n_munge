import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
import csv

# Matches words beginning with any non-whitespace character that repeats >1 time, possibly ends with a period and occurs at the end of a line. 
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE) 

# Search through a list of strings to confirm they terminate with items in the 'expected' list. If strings end with an item that's not a member of 'expected,' add the group of strings surrounding this item to the list 'street_types'

expected = ["Street", "Streets", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", "Bypass", "Trail", "Parkway", "Commons", "Pike", "Alley", "Circle", "East", "North", "South", "West", "Crossing", "Extension", "Highway", "Plaza", "Terrace", "Walk", "Way", "Run", "Tunnel", "Broadway", "Park", "Close"]

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

# Audit an osm file and return a dictionary of strings that don't terminate with any of the words in the expected list 
def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types