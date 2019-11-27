#!/usr/bin/env python
# coding: utf-8

# In[39]:


import random
import praw
from elasticsearch import Elasticsearch
from elasticsearch import helpers
scan = helpers.scan


# ## Setup Reddit API and ElasticSearch Connection

# In[2]:


reddit = praw.Reddit(client_id='Cz8OU1vxajnWDw',
                     client_secret='5qax29ZPI2_Rdjc1TsXXEypFduk',
                     redirect_uri='http://localhost:8080',
                     user_agent='my user agent')

print(reddit.auth.url(['identity'], '...', 'permanent'))

es = Elasticsearch([{'host':'localhost','port':9200}])
es


# In[ ]:


src_results = es.search(scroll='360m',      
    body =
    {
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
                          "field": "commenters"
                        }
                      }
                    ]
                  }
                },
                {
                  "exists": {
                    "field": "bm.overall"
                  }
                }
              ]
            }
          },
          "random_score": {
            "seed": random.randint(1, 1000)
          },
          "boost_mode": "replace"
        }
      }
    }, index = 'redditors', size = 2000)

for src_doc in src_results['hits']['hits']:
    redditor = reddit.redditor(src_doc['_id'])
    commenters = set()
    
    #print(redditor.name)
    try:
        for submission in redditor.submissions.hot():
            for comment in submission.comments:
                try:
                    if comment.author is not None and comment.author != redditor.name:
                        commenters.add(str(comment.author))
                except:
                    pass
    except:
        print("Forbidden: " + redditor.name)
        pass
    
    update = {
        "doc": {
            "commenters": list(commenters)
        }
    }
    es.update(index = 'redditors', id = src_doc['_id'], body = update)
    

