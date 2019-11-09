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


def classify(es, author, index_prefix, sublisting, all_classifier):
    classifier = None
    
    idx = index_prefix + '.' + sublisting
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
        all_classifier.preprocess(text, web=False)
    return classifier


src_index = 'redditors'
dest_index = 'comments'
comment_sublistings = ['controversial', 'hot', 'new', 'top'] 
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
            "seed": random.randint(1,1000)
        },
        "boost_mode": "replace"
      }
    }
  }, index = src_index, size=200)

for src_doc in src_results['hits']['hits']:
    author_doc = src_doc['_source']
    print(src_doc['_id'])

    controversial = None
    hot = None
    new = None
    top = None
    update = None
    
    all_classifier = Classifier()
    for sublisting in comment_sublistings:
        classifier = classify(es, author_doc['name'], dest_index, sublisting, all_classifier)
        
        if classifier is not None:
            if update is None:
                update = { "doc": { "bm": {} } }
            
            res = more_magic(classifier)
            res['type'] = ''.join([key[0] for key in res.keys()])
            update['doc']['bm'][sublisting] = res

    if update is not None:
        overall = more_magic(all_classifier)
        overall['type'] = ''.join([key[0] for key in overall.keys()])
        update['doc']['bm']['overall'] = overall
        es.update(index = src_index, id = src_doc['_id'], body = update)
    else:
        update = { "doc": { "bm": { "empty": True } } }
        es.update(index = src_index, id = src_doc['_id'], body = update)

