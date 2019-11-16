#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import praw
from elasticsearch import Elasticsearch
from datetime import datetime
from elasticsearch import helpers
scan = helpers.scan
import random


# ## Setup Reddit API and ElasticSearch Connection

# In[2]:


reddit = praw.Reddit(client_id='Cz8OU1vxajnWDw',
                     client_secret='5qax29ZPI2_Rdjc1TsXXEypFduk',
                     redirect_uri='http://localhost:8080',
                     user_agent='my user agent')

print(reddit.auth.url(['identity'], '...', 'permanent'))

es = Elasticsearch([{'host':'localhost','port':9200}])
es


# ## Grab comments for indexed redditors

# In[3]:


def index_comment(comment, es, idx):

    try:
        es.indices.create(idx)
    except:
        pass
    
    doc = {}
    doc['id'] = comment.fullname
    doc['author'] = comment.author.name
    doc['created_date'] = datetime.fromtimestamp(comment.created_utc).isoformat()
    
    if comment.approved_by:
        doc['approver'] = comment.approved_by.name
    else:
        doc['approver'] = ""
        
    doc['approved_date'] = comment.approved_at_utc
    doc['archived'] = comment.archived
    doc['author_flair_text'] = comment.author_flair_text
    doc['banned_date'] = comment.banned_at_utc
    doc['banned_by'] = comment.banned_by
    doc['text_body'] = comment.body
    doc['text_body_html'] = comment.body_html
    doc['controversiality'] = comment.controversiality
    doc['distinguished'] = comment.distinguished
    doc['up_votes'] = comment.ups
    doc['down_votes'] = comment.downs
    
    if comment.edited:
        doc['edited'] = True
    else:
        doc['edited'] = False
    
    doc['gilded'] = comment.gilded
    doc['gildings'] = comment.gildings
    doc['locked'] = comment.locked
    doc['is_submitter'] = comment.is_submitter
    doc['title'] = comment.link_title
    doc['mod_note'] = comment.mod_note
    doc['mod_reports'] = comment.mod_reports
    doc['num_comments'] = comment.num_comments
    doc['num_reports'] = comment.num_reports
    doc['over_18'] = comment.over_18
    doc['parent_id'] = comment.parent_id
    doc['quarantine'] = comment.quarantine
    doc['removal_reason'] = comment.removal_reason
    doc['report_reasons'] = comment.report_reasons
    doc['score'] = comment.score
    doc['stickied'] = comment.stickied
    doc['subreddit'] = comment.subreddit.display_name
    doc['subreddit_category'] = comment.subreddit.advertiser_category
    doc['total_awards_received'] = comment.total_awards_received
    
    es.index(index = idx, id = doc['id'], body = doc)
    return doc
    
    


# In[ ]:


src_index = 'redditors.followers.sample'
dest_index = 'redditors.followers.sample.comments'
comment_sublistings = ['hot', 'new', 'top'] 

src_results = es.search(scroll='360m', body = 
{
  "query": {
    "function_score": {
      "query": {
        "bool": {
          "must_not": [
            {
              "exists": {
                "field": "comments_indexed"
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
}, index = src_index, size = 10000)

for src_doc in src_results['hits']['hits']:
    redditor = reddit.redditor(src_doc['_id'])
    author_doc = src_doc['_source']
    author_doc_updated: bool = False
    print(src_doc['_id'])
    
    count = 0
    for sublisting in comment_sublistings:
        if count >= 50:
            break
        try:
            for comment in getattr(redditor.comments, sublisting)(limit = 50):
                if count >= 50:
                    break
                comment_doc = index_comment(comment, es, dest_index)
                count = count + 1
                
                if comment_doc['subreddit_category'] not in author_doc['categories']:
                    author_doc['categories'].append(comment_doc['subreddit_category'])
                    author_doc_updated = True

                if comment_doc['subreddit'] not in author_doc['subreddits']:
                    author_doc['subreddits'].append(comment_doc['subreddit'])
                    author_doc_updated = True
        except:
            pass
    
    if author_doc_updated:
        es.index(index = src_index, id = src_doc['_id'], body = author_doc)
    
    update = {
        "doc": {
              "comments_indexed": True
        }
    }
    es.update(index = src_index, id = src_doc['_id'], body = update)


# In[ ]:




