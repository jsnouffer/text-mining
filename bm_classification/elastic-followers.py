#!/usr/bin/env python
# coding: utf-8

import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jason/notebooks/bm_classification')
import random
from imported_MBTI import Classifier, Thipe
from classifier import more_magic
from elasticsearch import Elasticsearch
from elasticsearch import helpers
scan = helpers.scan

import nltk
nltk.data.path.append('/home/jason/nltk_data')


es = Elasticsearch([{'host':'localhost','port':9200}])
es


# In[3]:


def classify(es, author, idx):
    classifier = None
    src_results = scan(es, scroll='10m',    
        query = {
            "query": {
                "query_string" : {
                    "query" : author,
                    "default_field" : "author"
                }
            }
        }, index = idx)
    
    count=0
    for src_doc in src_results:
        count = count + 1
        if count >= 100:
            break # limit to 100 comments for performance
        
        if classifier is None:
            classifier = Classifier() 
        text = src_doc['_source']['text_body']
        classifier.preprocess(text, web=False)
        
    return classifier


# In[5]:


import random
src_index = 'redditors.followers.sample'
dest_index = 'redditors.followers.sample.comments'

src_results = es.search(scroll='360m',
    body = {
    "query": {
      "function_score": {
        "query": {
          "bool": {
            "must": [
              {
                "bool": {
                  "must_not": [
                    {
                      "exists": {
                        "field": "bm"
                      }
                    }
                  ]
                }
              },
              {
                "term": {
                  "comments_indexed": {
                    "value": True
                  }
                }
              }
            ]
          }
        },
        "random_score": {
            "seed": random.randint(1,10000)
        },
        "boost_mode": "replace"
      }
    }
  }, index = src_index, size=1000)

for src_doc in src_results['hits']['hits']:
    author_doc = src_doc['_source']
    update = None
    
    classifier = classify(es, author_doc['name'], dest_index)
    if classifier is not None:
        if update is None:
            update = { "doc": { "bm": {} } }

        res = more_magic(classifier)
        res['type'] = ''.join([key[0] for key in res.keys()])
        update['doc']['bm']['overall'] = res

    if update is not None:
        es.update(index = src_index, id = src_doc['_id'], body = update)
    else:
        update = { "doc": { "bm": {} } }
        es.update(index = src_index, id = src_doc['_id'], body = update)

