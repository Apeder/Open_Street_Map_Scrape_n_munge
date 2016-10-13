Open Street Map Data Cleaning and SQL Import
==========

When I moved to Philadelphia in 2003 to attend UPenn, I had spent the previous 18 years growing up in rural Northern Nevada, where my family has lived since just before 1900. As Philly was my entry in the wider, urban world of the East Coast, the town, its food, its art, its history and culture will always hold special charm. 

Philadlphia, PA - City of Brotherly Love

* https://www.openstreetmap.org/relation/188022
* https://mapzen.com/data/metro-extracts/metro/philadelphia_pennsylvania/


Restaurants
Bicylcing
Universities
Art museums

## Data Problems Encountered

### What Streets are in Philly, and which are not? 
The best list of all streets in Philly was at http://www.geographic.org/streetview/usa/pa/philadelphia.html, and given some good parsing itself, we could specify that streetnames need to match within a few characters to be considered valid. 

[Philly.gov #fail](./Philly_gov_search_kaput.jpg)

### Garden Variety Typos and Abbreviations
Street name typos
'Atreet': {'Arch Atreet'}
'PIke': {'Princeton PIke'},
'Sreet': {'Bridge Sreet'},
             'Sstreet': {'South 9th Sstreet'},
'Steet': {'South 18th Steet'},

Addresses entered in the wrong order and have a phone number 
446-1234': {'1 Brookline BlvdHavertown, PA 19083(610) 446-1234'},

Over abbreviated addresses
N Olden Ave',
              'E Lancaster Ave',
              'E. Mt Airy Ave',

Some require street or avenue to be appended, others aren't in philly, like Mallon Avenue

Strange orphan words
'Bigler': {'Bigler'},

No Broadway in Philly
'Broadway': {'373 North Broadway',
              'North Broadway',
              'South Broadway'},
             'Brown': {'N 37th & Brown'},
             'Bypass': {'Pemberton Bypass'},
             'Center': {'Town Center'},
             'Chestnut': {'Chestnut'},
             'Chippendale': {'Chippendale'},

Missing "Street" after?
 'Front': {'S Front'},
             'Garden': {'Spring Garden'},
             'Greene': {'Greene'},
             'Hook': {'Calcon Hook'},
             'Hutchinson': {'North Hutchinson'},
              'Mallon': {'Mallon'},
             'Maple': {'South Maple'},
             'Market': {'Market'},
             'Master': {'15th and Master'},
             'Moore': {'Cecil B. Moore'},
             'NJ-73': {'NJ-73'},
             'Nixon': {'Shawmont & Nixon'}
             'Preston': {'N Preston'},
             'Reno': {'North 50th Street & Reno'},
             'Salina': {'Salina'},
             'Sheffield': {'Sheffield'},
             'Sloan': {'Sloan'},
             'Spruce': {'Spruce'},
             'Warminster': {'Warminster'},
             'Warren': {'Warren'},
             'king': {'West king'},
             'susquahana': {'thompson and susquahana'},

'Stiles': {'16th and Stiles'},
             'StreetPhiladelphia': {'117 South 18th StreetPhiladelphia'},
'Thompson': {'Sletcher and Thompson'},
             'Vine': {'12th and Vine'},
             'W': {'NJ 70 W'},
             'W5': {'Presidential Blvd, Ste W5'},

Case
'ROAD': {'DAVISVILLE ROAD', 'TERWOOD ROAD', 'TOWNSHIP LINE ROAD'},

Some cities and states included - do these values need to be added to the other fields, or stripped? 
19047': {'200 Manor Ave. Langhorne, PA 19047',
              '2245 E. Lincoln Hwy, Langhorne, PA 19047',
              '2275 E Lincoln Hwy, Langhorne, PA 19047',
              '2300  East Lincoln Highway, Pennsylvania 19047'},
             '19067': {'East Trenton Avenue Morrisville, PA 19067'

<node id="1698269474" lat="40.1781173" lon="-74.8801017" version="2" timestamp="2012-03-31T17:34:45Z" changeset="11169232" uid="70696" user="xybot">
		<tag k="name" v="Red Lobster"/>
		<tag k="amenity" v="restaurant"/>
		<tag k="addr:street" v="2275 E Lincoln Hwy, Langhorne, PA 19047"/>
		<tag k="addr:housename" v="2275"/>
	</node>

All address fields
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

 These were especially stubborn:
 {'19083(610)': {'Brookline Boulevard Havertown 19083(610)'},
             '37th': {'North 37th'},
             '43rd': {'North 43rd'},
             '80': {'North Lewis Road Unit #80'},
             'Avenue,': {'West Girard Avenue,'},
             'Center': {'Town Center'},
             'Jersey': {'New Jersey'},
             'NJ': {'NJ'},
             'NJ-73': {'NJ-73'},
             'PA': {'East Lincoln Highway PA'},
             'Route': {'Route'},
             'US': {'US', 'US and US'}})

Full addresses need to be parsed, and the non-street values assigned to the correct addr: sub tags.  If it begins and ends with numbers? Use python address parser? 

Abbreviations at the front of addresses need to be expanded. 

Numbers w/ >2 characters at the front need to assigned to housenumber, suite or unit

If any lowercase letters are right next to an uppercase, 'tP', space needs to be inserted

All caps need to be lowered 

Though it took a while, regular expressions were handy.  These two interactive Regex sites were very helpful to test expressions before running code. 

http://www.pyregex.com/
http://www.regexpal.com/ 
http://pythex.org/

Overview of the Data
Other ideas about the datasets
Try to include snippets of code and problematic tags (see MongoDB Sample Project or SQL Sample Project) and visualizations in your report if they are applicable.
Use the following code to take a systematic sample of elements from your original OSM region. Try changing the value of k so that your resulting SAMPLE_FILE ends up at different sizes. When starting out, try using a larger k, then move on to an intermediate k before processing your whole dataset.

Would be easier to use lists of streetnames and regular expressions to add validation to user input fields, ideally via a dropdown menu that narrows matches as you begin to type. This is difficult, as no canonical reference list of streets in philadelphia is readily available as a clean text file. 

Did find this csv on the Philly gov open data site: https://www.opendataphilly.org/dataset/street-name-alias-list/resource/2c7db78e-69a0-4d7d-bc60-c4415052a4d0

http://boto.cloudhackers.com/en/latest/s3_tut.html#storing-large-data
Was an easy way to play with AWS, though getting the credentials worked out required changing the bucket policy: http://stackoverflow.com/questions/10854095/boto-exception-s3responseerror-s3responseerror-403-forbidden

Still, hard to complain about the wonderful simplicity of AWS handy command line interface:
aws s3 cp philadelphia_pennsylvania.osm s3://apederphiladelphia/philadelphia_openstreet.osm

Then had to create a key-pair for EC2 before we can analyze the data using EMR
aws ec2 create-key-pair --key-name MyKeyPair

https://aws.amazon.com/python/ boto3
http://docs.aws.amazon.com//ElasticMapReduce/latest/ReleaseGuide/emr-spark.html
http://docs.aws.amazon.com/datapipeline/latest/DeveloperGuide/dp-importexport-ddb-part1.html





