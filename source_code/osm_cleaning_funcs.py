mapping = { "St": "Street",
            "St.": "Street",
           "st.": "Street",
           "ST": "Street",
           "st": "Street",
           "Sreet": "Street",
           "Sstreet": "Street",
            "Atreet": "Street",
           "Steet": "Street",
           "street": "Street",
           "Sts.": "Streets",
           "AVE": "Avenue",
           "Ave": "Avenue",
           "Ave.": "Avenue",
           "ave": "Avenue",
           "Av": "Avenue",
           "Ave,": "Avenue",
           "avenue": "Avenue",
           "E": "East",
           "E.": "East",
           "e": "East",
           "N": "North",
           "N.": "North",
           "s": "South",
           "S": "South",
           "S.": "South",
           "south": "South",
           "W": "West",
           "Blvd": "Boulevard", 
           "Blvd.": "Boulevard",
           "Blv": "Boulevard",
           "Blvd,": "Boulevard",
           "Cir": "Circle",
           "Ct": "Court",
           "Dr": "Drive",
           "Ln": "Lane",
           "ln": "Lane",
           "lane": "Lane",
           "Hwy":"Highway",
           "Hwy,": "Highway",
           "PIke": "Pike",
           "Rd": "Road",
           "Rd.": "Road",
           "rd": "Road",
           "road": "Road",
           "ROAD": "Road",
           "RD": "Road",
           "ext": "Extension",
           "way": "Way",
           "&": "and",
           "Exp": "Expressway",
           "Rmp": "Ramp",
           "Pky": "Parkway",
           "Ter": "Terrace",
           "Tr": "Trail",
           "Sq": "Square",
           "Pkwy": "Parkway",
           "pky": "Parkway",
           "Pl": "Place",
           "Ext": "Exit",
           "Wlk": "Walk",
           "wlk": "Walk",
           "Brg": "Bridge",
           "Tun": "Tunnel",
           "Tnl": "Tunnel",
           "Cre": "Crescent",
           "al": "Alley",
           "Ste": "Suite"
            }

import re

# Between 1 and 4 digits at the beginning or a line, exclude numbered street names like 34th, 23rd, 1st, 42nd
house_number = re.compile(r'^(\d{2,4}|\b\d{1}\b)(?!th|rd|st|nd)', re.IGNORECASE)

# |(?<!route )(?<!us )(?<!nj )(?<!jersey )(\d{2,4}|\b\d{1}\b)(?!th|rd|st|nd)$

# unit_number needs to match two digits at the end of a line, unless they follow a state name Or US or have a number ending
unit_num = re.compile(r'u.*it ?#?(\d{2,4} ?|\b\d{1}\b)(?!th|rd|st|nd)$', re.IGNORECASE)

# Also suite, ste, ste. Little more complicated, as suite has letters in common with "Street"
suite_num = re.compile(r'(?<!u)s[u|t]?[i|t]?t?e?.? ?#?(?<!rsey )(?<!ania )(\d{2,4} ?|\b\d{1}\b)(?!th|rd|st|nd)$', re.IGNORECASE)

 # Five consecutive digits is very likely a zipcode in this context, though could also restrict to a list of known zipcodes in the Phillly metro area. 
zipcode = re.compile(r'\d{5}')

# any chr, 3 digits, any chr, 3 digits, any chr, 4 digits. As bonus, this will ensure that phone numbers in the DB are unique
phone = re.compile(r'\(?\d{3}\)?[-\.\s]??\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}') 

# There should technically be only one city, Philadelphia, though there a few other suburban cities close to Philly included
cities = re.compile(r'Philadelphia|Langhorne|Morrisville|Havertown|Levittown|Springfield', re.IGNORECASE)

#Try to abbreviate 'Pennsylvania' or 'New Jersey', I dare you! 
pa_state = re.compile(r'\bpen.*\.?ia\b|\bpa\.?\b', re.IGNORECASE)

#Calibrated to accept regional vernacular varients such as 'Joizy' or 'Joisey'
nj_state = re.compile(r'\bnj\b|new ?j.*y|j.*y', re.IGNORECASE)

# If words aren't spaced, like 'BrooklineBlvd'
abutted = re.compile(r'([A-Z]{1}\w+)([A-Z]\w+)')

# ALL CAPS
all_cap = re.compile(r'[A-Z]{3,}') # At least 3 caps 

#fix all lower to normal case
all_low = re.compile(r'\b[a-z]{4,}\b') # At least 4 lower case chrs with whitespace before and after

# If two words joined by 'and' or '&', add "Streets" Doesn't yet match '&amp'
intersection = re.compile(r'(\w+\s\band\b\s\w+)|(\w+\s\b&\b\s\w+)')

import sys
from bs4 import BeautifulSoup

def clean_streets(osmfile):
    """If the OSM file addr:street attribute contains information for other fields, extract this information and create a new tag.
    Open an Open Street Map (OSM) file, find all street names, iterate through the list of street names and check if any match a state name, house number, phone number or zipcode. If one of the words matches, insert it into the tree as a new tag. 
    
    Args:
        osmfile (XML): Open Street Map XML file 
    
    Returns:
        map_xml: XML object from BeautifulSoup 
    """

    reload(sys)
    sys.setdefaultencoding('utf-8')
    
    with open(osmfile, "r+b") as input_file:
        soup = BeautifulSoup(input_file, "xml")
        street_tags = soup.find_all("tag", attrs={"k": "addr:street"})
        phones = soup.find_all("tag", attrs={"k": "phone"})
        
        for tag in street_tags:
            par = tag.find_parent("node")

            city = cities.search(tag['v'])    
            if city:
                new_tag = soup.new_tag("tag", k="addr:city", v='{}'.format(city.group()))
                tag.insert_after(new_tag)

            # Check if string contains a housenumber and insert new tag if so
            num = house_number.search(tag['v'])
            if num and par != None:
                snum = par.find_all("tag", attrs={"k": "addr:housenumber"})
                v_val = num.group()
                new_tag = soup.new_tag("tag", k="addr:housenumber", v='{}'.format(v_val))
                if new_tag not in snum:
                    tag.insert_after(new_tag)
                    re.sub(house_number,'', tag['v']) # None of these substitutions are working

            #Check if string contains phone number and insert new tag if so
            call_me = phone.search(tag['v'])
            if call_me:
                v_val = call_me.group()
                new_tag = soup.new_tag("tag", k="phone", v='{}'.format(v_val))
                if new_tag not in phones:
                    tag.insert_after(new_tag)
                    re.sub(phone,'',tag['v'])

            post = zipcode.search(tag['v'])
            if post and par != None:
                ezips = par.find_all("tag", attrs={"k": "addr:postcode"})
                v_val = post.group()
                new_tag = soup.new_tag("tag", k="addr:postcode", v='{}'.format(v_val))
                if new_tag not in ezips:    
                    tag.insert_after(new_tag)        
                    re.sub(zipcode,'', tag['v'])

            sweet = suite_num.search(tag['v'])
            if sweet and par != None: 
                sweets = par.find_all("tag", attrs={"k": "addr:suite"})
                v_val = sweet.group()
                new_tag = soup.new_tag("tag", k="addr:suite", v='{}'.format(v_val))
                if new_tag not in sweets:
                    tag.insert_after(new_tag)
                    re.sub(suite_num,'', tag['v'])

            uno = unit_num.search(tag['v'])
            if uno and par != None: 
                units = par.find_all("tag", attrs={"k": "addr:unit"})
                v_val = uno.group()
                new_tag = soup.new_tag("tag", k="addr:unit", v='{}'.format(v_val))
                if new_tag not in units:
                    tag.insert_after(new_tag)
                    re.sub(unit_num,'', tag['v'])

            keystone = pa_state.search(tag['v'])
            if keystone:
                new_tag = soup.new_tag("tag", k="addr:state", v="Pennsylvania")
                tag.insert_after(new_tag)
                re.sub(pa_state,'', tag['v'])

            joizy = nj_state.search(tag['v'])        
            if joizy:
                new_tag = soup.new_tag("tag", k="addr:city", v="New Jesery")
                tag.insert_after(new_tag)
                re.sub(nj_state,'', tag['v'])

        map_xml = soup.prettify()
        return map_xml

# Clean up words in the addr:street attributes 
def filter_words(val):
    """Split the addr:street string into a list of words and check if any words are base name orphans or contains typographic 
    errors and/or a word to be replaced by the mapping.
    
    Args:
        val (str): String value passed by process_map() when a tag's k attribute is 'addr:street'
    
    Returns:
        val (str): Cleaned string value to be approximate string matched before being written to disk
    """

    reload(sys)
    sys.setdefaultencoding('utf-8')

    words = val.split()
            
    street_orphans = ['Spruce', 'Bigler', 'Warren', 'Chippendale', 'Front', 'Greene', 'Market', 'Sloan', 'Salina'
                         'Warren', 'Chestnut', 'North 37th']
        
    if val in street_orphans:
        words.append('Street')
            
    av_orphans = ['Mallon']
        
    if val in av_orphans:
        words.append('Avenue')
                
    for idx, word in enumerate(words):    
        no_space = re.search(abutted, word)
        if no_space:
            words[idx] = abutted.sub(r'\1', word).strip(',')
            words.insert(idx+1, re.sub(abutted, r'\2', word).strip(','))
        caps = all_cap.search(word) #caps nor lowered don't seem to be working
        if caps:
            words[idx] = word[idx].title()
        lowered = all_low.search(word)
        if lowered:
            words[idx] = words[idx].capitalize()
        
    clean_name = ' '.join(str(mapping.get(word, word)) for word in words).strip(',')
    val = str(clean_name)

from fuzzywuzzy import fuzz, process

def fix_street_names(val):
    """Use canonical list of street names to search for approximate string matches for street names that don't end with an 
    expected value and aren't intersections and calculate a match score based on Levenshtein distance. If the match score is 90 or
    above, replace the input string with its match from the canonical list. 
    
    Args:
        val (str): addr:street attribute string

    Returns:
        val (str): Approximate string match from canonical list with Levenshtein score >= 90
    
    """
    reload(sys)
    sys.setdefaultencoding('utf-8')
    
    with open('./philly_street_full_names_canon.csv', 'r') as streets_canon:
        reader = csv.reader(streets_canon)
        possible_streets = list(reader)[0]
    
    no_fix = ['Mallon Avenue']
    
    # Only run for those records yielded from the audit function
    m = street_type_re.search(val)
    street_end = m.group()
    intersect = intersection.search(value)

    if street_end not in expected and not intersect and val not in no_fix: 
        st_name = process.extractOne(tag['v'], possible_streets)
        if st_name[1] >= 90:
            val = st_name[0]
