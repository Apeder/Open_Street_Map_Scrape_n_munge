Open Street Map Data Cleaning and SQL Import
==========

When I moved to Philadelphia in 2003 to attend UPenn, I had spent the previous 18 years growing up in rural Northern Nevada, where my family has lived since just before 1900. As Philly was my entry in the wider, urban world of the East Coast, the town, its food, its art, its history and culture will always hold special charm. 

This project scrapes an Open Street Map (OSM) XML file and imports the data to a SQL databse that we can query to explore the map elements in the Philadelphia metro area. The first link below indicates the boundaries of the XML file, and to save time, the XML file was downloaded from mapzen from the second. 

Philadlphia, PA - City of Brotherly Love

* https://www.openstreetmap.org/relation/188022
* https://mapzen.com/data/metro-extracts/metro/philadelphia_pennsylvania/

## Dataset Overview

There are over 2.8 million node tags, over 261 thousand way tags and only about 4000 relation tags. There are also 
over 1.7 million tags nested below node, way and relation elements.
http://wiki.openstreetmap.org/wiki/OSM_XML

### Number of nodes, ways, etc.

```sql
sqlite> SELECT COUNT(*) FROM Nodes 
2811847
sqlite> SELECT COUNT(*) FROM Ways;
261503
sqlite> SELECT COUNT(*) FROM Way_Tags;
1369705
sqlite> SELECT COUNT(*) FROM Node_Tags;
334095
sqlite> SELECT COUNT(*) FROM Way_Nodes;
3387554
```

### Unique Users
```sql
sqlite> SELECT COUNT(DISTINCT(i.uid))
   ...> FROM (SELECT uid FROM Nodes UNION ALL SELECT uid FROM Ways) i;
1822
```

### Top ten users
```sql
SELECT e.user, COUNT(*) as num
FROM (SELECT user FROM Nodes UNION ALL SELECT user FROM ways) e
GROUP BY e.user
ORDER BY num DESC
LIMIT 10;

dchiles|799894
woodpeck_fixbot|571834
NJDataUploads|297483
kylegiusti|106160
Matt1993|92378
choess|86123
crystalwalrein|77304
Louise Belcher|65258
eugenebata|62532
bot-mode|44946
```

### Top post codes
```sql
SELECT tags.value, COUNT(*) as count 
FROM (SELECT * FROM Node_Tags 
      UNION ALL 
      SELECT * FROM Way_Tags) tags
WHERE tags.key='postcode'
GROUP BY tags.value
ORDER BY count DESC
LIMIT 15;

Top zipcode is in NJ... 
08068|2091
19061|1396
19106|394
19130|391
08043|358
19103|344
19107|308
19104|249
08003|196
19128|181
19428|174
19102|124
19123|124
19147|119
18914|117
19087|107
18901|105
19146|105
18974|100
08054|93
19072|66
19027|51
```

### Cities by count descending
```sql
SELECT tags.value, COUNT(*) as count 
FROM (SELECT * FROM Node_Tags UNION ALL 
      SELECT * FROM Way_Tags) tags
WHERE tags.key LIKE '%city'
GROUP BY tags.value
ORDER BY count DESC;

Philadelphia|3523
Pemberton|2092
Trenton city|1659
Lawrence twp|1157
Upper Chichester;Marcus Hook;Chichester|967
Boothwyn|844
Marcus Hook|374
Voorhees|211
Cherry Hill|207
Conshohocken|173
Voorhees Township|146
Ewing twp|137
Hopewell twp|121
Chalfont|119
Trenton|111
Ogden|104
1|102
Wayne|100
Doylestown|98
Linwood|95
Mount Laurel|92
Wilmington|87
New Jesery|84
Warminster|83
Lower Chichester;Marcus Hook;Chichester|74
```

### Top ten ammenities 
```sql
SELECT value, COUNT(*) as num
FROM Node_Tags
WHERE key='amenity'
GROUP BY value
ORDER BY num DESC
LIMIT 10;

school|1665
restaurant|904
place_of_worship|699
fire_station|457
fast_food|377
social_facility|280
parking|243
bench|235
bank|217
cafe|210
```

### Religious Institutions - search for wooder ice instead?
```sql
SELECT Node_Tags.value, COUNT(*) as num
FROM Node_Tags 
    JOIN (SELECT DISTINCT(id) FROM Node_Tags WHERE value='place_of_worship') i
    ON Node_Tags.id=i.id
WHERE Node_Tags.key='religion'
GROUP BY Node_Tags.value
ORDER BY num DESC
LIMIT 5;

christian|638
jewish|33
muslim|4
buddhist|2
Baptist|1
```

### Total Restaurants
```sql
SELECT COUNT(*)
FROM Node_Tags 
    JOIN (SELECT DISTINCT(id) FROM Node_Tags WHERE value='restaurant') i
    ON Node_Tags.id=i.id
WHERE Node_Tags.key='cuisine';

482
```

### Number of different kinds of restaurants
```sql
SELECT Node_Tags.value, COUNT(*) as num
FROM Node_Tags 
    JOIN (SELECT DISTINCT(id) FROM Node_Tags WHERE value='restaurant') i
    ON Node_Tags.id=i.id
WHERE Node_Tags.key='cuisine'
GROUP BY Node_Tags.value
ORDER BY num DESC;

pizza|102
italian|53
chinese|46
mexican|37
american|35
sandwich|23
burger|15
asian|14
japanese|12
indian|11
greek|7
spanish|6
steak_house|6
vietnamese|6
chicken|5
```

### All address fields
```
  addr:city': 1329,
 'addr:country': 203,
 'addr:full': 2,
 'addr:housename': 36,
 'addr:housenumber': 1426,
 'addr:interpolation': 28,
 'addr:postcode': 974,
 'addr:state': 793,
 'addr:street': 1752,
 'addr:suite': 7,
 'addr:unit': 1,
```

## Data Problems Encountered

### addr:street Attributes Contain Values for Other Fields
Several addr:street attributes included full addresses, with state, zipcode, phone, house, suite and unit numbers. The first cleaning function, 'clean_streets()' scans values in all addr:street attributes and uses regular expressions to match any values that should be in other fields. 

```
'1 Brookline BlvdHavertown, PA 19083(610) 446-1234'
'200 Manor Ave. Langhorne, PA 19047'
'2245 E. Lincoln Hwy, Langhorne, PA 19047',
'2275 E Lincoln Hwy, Langhorne, PA 19047',
'2300  East Lincoln Highway, Pennsylvania 19047'},
'East Trenton Avenue Morrisville, PA 19067'
```
If these values are found, the function inserts a new tag in the parent element with the appropriate attribute and value, unless a tag with that value already exists. For example:

```python
phone = re.compile(r'\(?\d{3}\)?[-\.\s]??\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}') 
phones = soup.find_all("tag", attrs={"k": "phone"})

call_me = phone.search(tag['v'])
if call_me:
  v_val = call_me.group()
  new_tag = soup.new_tag("tag", k="phone", v='{}'.format(v_val))
    if new_tag not in phones:
      tag.insert_after(new_tag) 
```
```xml
<node changeset="34353963" id="1483624883" lat="39.9787384" lon="-75.3038692" timestamp="2015-09-30T19:10:51Z" uid="3276050" user="JCarden" version="2">
  <tag k="name" v="Kettle"/>
  <tag k="amenity" v="restaurant"/>
  <tag k="cuisine" v="Diner"/>
  <tag k="addr:street" v="Brookline Boulevard"/>
  <tag k="addr:city" v="Havertown"/>
  <tag k="addr:state" v="Pennsylvania"/>
  <tag k="phone" v="(610) 446-1234"/>
  <tag k="addr:postcode" v="19083"/>
  <tag k="addr:housenumber" v="1"/>
 </node>
```

### Which Streets Are in Philly, and Which Are Not? 
The XML includes elements from a square bounding box around Philadelphia, so some streets are from nearby towns in PA, like Havertown and Langhorne as well as some from New Jersey, just accross the Delaware River.  With a list of clean, unique street names in Philadelphia, we can clean and validate the data with an [approximate (fuzzy) string matching algorithm](https://marcobonzanini.com/2015/02/25/fuzzy-string-matching-in-python/).

One surprising discovery is that no clean, canonical list of the streets in Philadelphia is easily accessbile.  In fact, searching for this on the Philadelphia government webpage raised an immediate red flag.

![Philly.gov #fail](https://github.com/Apeder/Open_Street_Map_Scrape_n_munge/blob/master/Philly_gov_search_kaput.png)

Although Philly's Open Data site did have two csv files with streetnames available, neither was cleaned or comprehensive enough to use as a canoncial list for fuzzy string matching. 

* [Street Name Alias](https://www.opendataphilly.org/dataset/street-name-alias-list/resource/2c7db78e-69a0-4d7d-bc60-c4415052a4d0)
* [Street Place Names](https://www.opendataphilly.org/dataset/street-place-names/resource/ed10ab8b-e998-4853-b440-81df22c39bfc)

Fortunately, the US Census' [Topologically Integrated Geographic Encoding and Referencing (TIGER) data](http://www.census.gov/geo/maps-data/data/tiger.html) imported into the 'Way' elements includes both "tiger:name_base" attributes as well as "name" attributes with full street names. 

```xml
<way changeset="37014829" id="43117631" timestamp="2016-02-05T08:40:51Z" uid="3057995" user="oini" version="11">
  <nd ref="110421617"/>
  <nd ref="2906080683"/>
  <tag k="name" v="West Girard Avenue"/>
  <tag k="layer" v="1"/>
  <tag k="bridge" v="yes"/>
  <tag k="highway" v="secondary"/>
  <tag k="tiger:cfcc" v="A21"/>
  <tag k="ref:penndot" v="SR2008"/>
  <tag k="tiger:zip_left" v="19131"/>
  <tag k="tiger:name_base" v="Girard"/>
  <tag k="tiger:name_type" v="Ave"/>
  <tag k="tiger:zip_right" v="19104"/>
  <tag k="tiger:name_base_1" v="United States Highway 30"/>
  <tag k="old_ref_legislative" v="67301"/>
  <tag k="tiger:name_direction_prefix" v="W"/>
 </way>
```
The downside is that sometimes a 'Way' element's 'name' attribute is a street name, and other times, it's a location name. 

```xml
<way changeset="10677130" id="150255661" timestamp="2012-02-13T20:23:59Z" uid="594684" user="kumpel75" version="1">
  <nd ref="1631799891"/>
  <nd ref="1631799894"/>
  <nd ref="1631799920"/>
  <nd ref="1631799922"/>
  <nd ref="1631799962"/>
  <nd ref="1631799959"/>
  <nd ref="1631799945"/>
  <nd ref="1631799914"/>
  <nd ref="1631799891"/>
  <tag k="name" v="Red Lion Diner"/>
  <tag k="building" v="restaurant"/>
  <tag k="addr:street" v="US and US Streets"/>
  <tag k="addr:postcode" v="08088"/>
  <tag k="addr:housename" v="Red Lion Diner"/>
 </way>
```
Upon closer examination, the 'tiger:name_base' attribute contained 15,284 elements, and many contained typos and were obviously not streets. 

```
u'Norfolk Southern Railway:Pennsylvania Railroad', u'Belmont;Green', u'United States Highway 1; Lincoln', u'Mantua;Harrison', u'Reading Railroad:Septa Railroad', u'Baltimore and Ohio Railroad:Norfolk Southern Railway', u'Franklin:Hampton', u'State Route 68; State Route 68; State Route 68A; State Route 68; State Route 68', u'United States Highway 206;Old York', u'Perry; Lincoln', u'Norfolk Southern Railway; Csx Railway; Conrail Railroad', u'Township Line;Big Oak', u'Market:United States Highway 13 (Bus)', u'Coursey; College', u'I-295:I-76', u'Early; Davis', u'of the Arts', u'\x7f\x7fBeech', u'Bridge; Main', Spring:Pond View', u'Cypress:Longacre', u'Delmar;84th', u'New Jersey Transit:Penn Central Railroad; Conrail Railroad'
```
The 'Way' element 'name' attributes, however, once filtered to exclude non-street names, was comprehensive and clean enough to use as a canonical reference list for appoximate string matching. Though not perfect, with 31,489 names, chances of finding correctly spelled matches are high, and the cases tested from this dataset worked well. 

As building an approximate string matching algorithm from scratch would be time consuming, the open source [FuzzyWuzzy](https://github.com/seatgeek/fuzzywuzzy) approximate string matching module came in handy. The module is based on [Levenshtein distance](https://en.wikipedia.org/wiki/Levenshtein_distance), and when given a string and list of strings as input, outputs the highest ranked match between the string provided and the choices in the list.

For example:

```python
from fuzzywuzzy import process

    for tag in street_tags:
        m = street_type_re.search(tag['v'])
        street_end = m.group()
        intersect = intersection.search(tag['v'])

        if street_end not in expected and not intersect and tag['v'] not in no_fix: 
            st_name = process.extractOne(tag['v'], possible_streets)
            if st_name[1] >= 90:
                tag['v'] = st_name[0]
```

```
'US 70 and US 206', ('Campus Crossings E and F street', 86)
'Route 33', ('South 33rd Street', 68)
'North 37th', ('North 37th Street', 90)
'North 43rd', ('North 43rd Street', 90)
'1 Brookline Boulevard Havertown PA 19083(610) 446-1234', ('Brookline Boulevard', 90)
'West Girard Avenue, 5', ('West Girard Avenue', 95)
'DAVISVIL LE RO AD', ('Davisville Road', 94)
```
Not all matches are perfect, so strings are only replaced if they score 90 or above. This ratio is calculated from Levenshtein distance, so a score of 0 would indicate that the number of changes required is the maximum possible, while a score of 100 indicates that the number of changes required is the minimum possible. 

If we wanted to be super thorough, we could use the Census Bureau's latest TIGER Roads National Geodatabase:

* http://www.census.gov/geo/maps-data/data/tiger-geodatabases.html
* http://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2016/2016_TIGER_GDB_Record_Layouts.pdf

![Tiger National Roads](https://raw.githubusercontent.com/Apeder/Open_Street_Map_Scrape_n_munge/master/natlroads.png)

The file is 2.1 GB, though, so we would have to upload it to S3 and rewrite our code in Spark to make use of it. Perhaps it could be used for n-gram matching? Would that be faster? Databricks/Spark is probably a better way to test if this is possible.  It's also not clear how to query this dataset by city or state, so more processing would be required.

### Garden Variety Typos and Abbreviations
The 'filter_words()' function scans each word in the addr:street field and replaces mispellings and abbreviations with a mapping. 

#### Street name typos
```
'Atreet': {'Arch Atreet'}
'PIke': {'Princeton PIke'},
'Sreet': {'Bridge Sreet'},
'Sstreet': {'South 9th Sstreet'},
'Steet': {'South 18th Steet'},
```

#### Over abbreviated addresses
```
'N Olden Ave',
'S. 41st',
'Shannondell Blvd',
'Portsmouth Ct',
'Deerpath Dr',
'Anderson Rd',
'S 19th St'
```
#### Improper Case
```
'ROAD': {'DAVISVILLE ROAD', 'TERWOOD ROAD', 'TOWNSHIP LINE ROAD'},
```
# Conclusion

Would be easier to use lists of streetnames and regular expressions to add validation to user input fields, ideally via a dropdown menu that narrows matches as you begin to type. This is difficult, as no canonical reference list of streets in philadelphia is readily available as a clean text file. 

http://www.chokkan.org/software/simstring/
Could build simstring from source and make a python module
These guys use SimString with a TF/IDF pre-processing and Support Vector Machine: 
http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.251.2922&rep=rep1&type=pdf

http://boto.cloudhackers.com/en/latest/s3_tut.html#storing-large-data
Was an easy way to play with AWS, though getting the credentials worked out required changing the bucket policy: http://stackoverflow.com/questions/10854095/boto-exception-s3responseerror-s3responseerror-403-forbidden

Still, hard to complain about the wonderful simplicity of AWS handy command line interface:
aws s3 cp philadelphia_pennsylvania.osm s3://apederphiladelphia/philadelphia_openstreet.osm

Then had to create a key-pair for EC2 before we can analyze the data using EMR
aws ec2 create-key-pair --key-name MyKeyPair

https://aws.amazon.com/python/ boto3
http://docs.aws.amazon.com//ElasticMapReduce/latest/ReleaseGuide/emr-spark.html
http://docs.aws.amazon.com/datapipeline/latest/DeveloperGuide/dp-importexport-ddb-part1.html

Another project might be to write a validator in Django for Open Street Map' iD online editor
https://docs.djangoproject.com/en/1.10/ref/validators/

![OsmiDeditor](https://raw.githubusercontent.com/Apeder/Open_Street_Map_Scrape_n_munge/master/OSMeditor.png)

http://wiki.openstreetmap.org/wiki/Comparison_of_editors#online
Wasn't incredibly successful. 

Databricks is probably the best way to try Spark to speed up the analysis. Ehhh... lots of extra work. Maybe Elastic Beanstalk to build a simple mapping app that creates SQL queries from user input and maps using d3? 

