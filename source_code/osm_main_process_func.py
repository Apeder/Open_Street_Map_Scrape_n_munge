import osm_audit_func
import osm_cleaning_funcs

import csv
import codecs
import re
import xml.etree.cElementTree as ET
import schema

OSM_PATH = "philadelphia_pennsylvania.osm"

NODES_PATH = "./db_csvs/nodes.csv"
NODE_TAGS_PATH = "./db_csvs/node_tags.csv"
WAYS_PATH = "./db_csvs/ways.csv"
WAY_NODES_PATH = "./db_csvs/way_nodes.csv"
WAY_TAGS_PATH = "./db_csvs/way_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  

    for e in element.iter("tag"):
        id = element.get('id')
        key = e.get('k')
        if key == 'addr:street': 
            init_val = e.get('v')
            clean_val = filter_words(init_val)
            value = fix_street_names(clean_val)
            if value != init_val:
                print 'Changed {} => {}'.format(init_val, value)
        else: value = e.get('v')
        low = LOWER_COLON.search(key)
        prob = PROBLEMCHARS.search(key)
        if low and not prob:
            kt = key.split(':', 1)
            tags.append({"id": id, "key": kt[1], "value": value, "type": kt[0]})
        if not low and not prob:
            tags.append({"id": id, "key": key, "value": value, "type": 'regular'})
        if prob:
            continue
    
    if element.tag == 'node':
        for idx, val in enumerate(NODE_FIELDS):
            k = NODE_FIELDS[idx] 
            val = element.get(val)
            node_attribs.update({k: val})    
        if node_attribs:
            return {'node': node_attribs, 'node_tags': tags}
        else:
            return None   
    
    elif element.tag == 'way':
        for idx, val in enumerate(WAY_FIELDS):
            k = WAY_FIELDS[idx]
            val = element.get(val)
            way_attribs.update({k: val})
        i = 0
        for w in element.iter('nd'):
            id = element.get('id')
            n_id = w.get('ref')
            way_nodes.append({"id": id, "node_id": n_id, "position": i})
            i += 1
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
    
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()
            
def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

# 31 min with validator on 1/5 file
from __future__ import division
import cerberus
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""
    start_time = time.time()
    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()
        
        map_xml = clean_streets(file_in)

        for element in get_element(map_xml, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
    print("--- {}min ---".format((time.time() - start_time)/60))
