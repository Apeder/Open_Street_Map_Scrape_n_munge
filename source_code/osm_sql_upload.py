from sqlalchemy import create_engine, ForeignKey, Column, Integer, Float, Date, String
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlite3 import dbapi2 as sqlite

engine = create_engine('sqlite:///./db_csvs/philly_test_sql.db', module=sqlite)

Base = declarative_base()

class Node(Base):
    __tablename__ = 'Nodes'
    id = Column(Integer, primary_key=True, nullable=False) 
    lat = Column(Float)
    lon = Column(Float)
    user = Column(String)
    uid = Column(Integer)
    version = Column(String)
    changeset = Column(Integer)
    timestamp = Column(String)
    
class Node_Tag(Base):
    __tablename__ = 'Node_Tags'
    id = Column(Integer, ForeignKey("Nodes.id"), nullable=False) 
    key = Column(String)
    value = Column(String)
    type = Column(String)
    idx = Column(Integer, primary_key=True, index=True, unique=True, nullable=True)

class Way(Base):
    __tablename__ = 'Ways'
    id = Column(Integer, primary_key=True, nullable=False) 
    user = Column(String)
    uid = Column(Integer)
    version = Column(String)
    changeset = Column(Integer)
    timestamp = Column(String)

class Way_Node(Base):
    __tablename__ = 'Way_Nodes'
    id = Column(Integer, ForeignKey("Ways.id"), nullable=False) 
    node_id = Column(Integer)
    position = Column(Integer, nullable=True)
    idx = Column(Integer, primary_key=True, index=True, unique=True, autoincrement=True)

class Way_Tag(Base):
    __tablename__ = 'Way_Tags'
    id = Column(Integer, ForeignKey("Ways.id"), nullable=False) 
    key = Column(String)
    value = Column(String)
    type = Column(String)
    idx = Column(Integer, primary_key=True, index=True, unique=True, nullable=False)


Base.metadata.create_all(engine)

import csv
from time import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def UnicodeDictReader(utf8_data, **kwargs):
    csv_reader = csv.DictReader(utf8_data, **kwargs)
    for row in csv_reader:
        yield {key: unicode(value, 'utf-8') for key, value in row.iteritems()}

def load_dat(filename):
    """Open a csv file and upload each row as a new record in a SQL database table determined by the file name and the 
    number of fields.
    
    Args:
        filename (csv): CSV file formatted as Python dictionary
    """
    table_stem = filename.split('/')[2]
    table_name = '_'.join([x.capitalize() for x in table_stem.split('_')]).strip('.csv')+'s'
    
    engine = create_engine('sqlite:///./db_csvs/philly_test_sql.db')
    session = sessionmaker()
    session.configure(bind=engine)
    s = session()

    with open(filename, 'rb') as f:
        fiel = csv.DictReader(f)
        fields = list(fiel)[0].keys()
        n = len(fields)
        if n == 8:
            with open(filename, 'rb') as g:
                fr = UnicodeDictReader(g)
                dat = [{'id': i['id'], 'lat': i['lat'], 'lon': i['lat'], 'user': i['user'], 'uid': i['uid'], 
                        'version': i['version'], 'changeset': i['changeset'], 'timestamp': i['timestamp']} for i in fr]      
            for row in dat:
                record = Node(**row)
                s.add(record)
            s.commit()
            s.close()    
        if n == 6:
            with open(filename, 'rb') as g:
                fr = UnicodeDictReader(g)
                dat = [{'id': i['id'], 'user': i['user'], 'uid': i['uid'], 'version': i['version'], 'changeset': i['changeset'],
                        'timestamp': i['timestamp']} for i in fr]
            for row in dat:
                record = Way(**row)
                s.add(record)
            s.commit()
            s.close()
        if n == 4:
            with open(filename, 'rb') as g:
                fr = UnicodeDictReader(g)
                dat = [{'id': i['id'], 'key': i['key'], 'value': i['value'], 'type': i['type']} for i in fr]       
            for row in dat:
                if table_name == 'Node_Tags':
                    record = Node_Tag(**row)
                    s.add(record)
                if table_name == 'Way_Tags':
                    record = Way_Tag(**row)
                    s.add(record)
            s.commit()
            s.close
        if n == 3:
            with open(filename, 'rb') as g:
                fr = UnicodeDictReader(g)
                dat = [{'id': i['id'], 'node_id': i['node_id'], 'position': i['position']} for i in fr]
            for row in dat:
                record = Way_Node(**row)
                s.add(record)
            s.commit()
            s.close()        

# Upload all CSV files in our directory to the SQL DB
import fnmatch
import os

files = fnmatch.filter(os.listdir('./db_csvs'), '*.csv')

for f in files:
    fname = './db_csvs/{}'.format(f)
    load_dat(fname) 