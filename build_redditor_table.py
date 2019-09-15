#!/usr/bin/env python
# coding: utf-8

# In[32]:


import praw
from elasticsearch import Elasticsearch

from elasticsearch import helpers
scan = helpers.scan

from datetime import datetime


# ## Setup Reddit API and ElasticSearch Connection

# In[2]:


reddit = praw.Reddit(client_id='Cz8OU1vxajnWDw',
                     client_secret='5qax29ZPI2_Rdjc1TsXXEypFduk',
                     redirect_uri='http://localhost:8080',
                     user_agent='my user agent')

print(reddit.auth.url(['identity'], '...', 'permanent'))

es = Elasticsearch([{'host':'localhost','port':9200}])
es


# ## Grab popular subreddits from API

# In[19]:


# Grab popular subreddits
count = 0
for subreddit in reddit.subreddits.popular():
    count += 1
    doc = {
        "id": subreddit.display_name,
        "title": subreddit.title,
        "description": subreddit.public_description,
        "subscribers": subreddit.subscribers,
        "created": datetime.fromtimestamp(subreddit.created_utc).isoformat(),
        "language": subreddit.lang,
        "category": subreddit.advertiser_category
    }
    
    # Ingest into Elastic
    es.index(index = 'subreddits.popular', id = subreddit.display_name, body = doc)
print(count)


# In[107]:


redditors = 'redditors'

try:
    es.indices.create(index = redditors)
except:
    pass

results = scan(es,
    query = {"query": {"match_all" : {}}},
    index = 'subreddits.popular'
)

for doc in results:
    subreddit = reddit.subreddit(doc['_id'])
    for comment in subreddit.comments(limit = 1000):
        doc = {}
        
        author = comment.author
        
        if (es.exists(index = redditors, id = comment.author)):
            doc = es.get(index = redditors, id = comment.author)
            print(doc)
        
        if 'name' not in doc.keys():
            doc['name'] = author.name
            
        if 'object_id' not in doc.keys():
            doc['object_id'] = author.fullname
            
        if 'categories' not in doc.keys(): 
            doc['categories'] = []
        
        if subreddit.advertiser_category not in doc['categories']:
            doc['categories'].append(subreddit.advertiser_category)
        
        if 'subreddits' not in doc.keys(): 
            doc['subreddits'] = []
        
        if subreddit.display_name not in doc['subreddits']:
            doc['subreddits'].append(subreddit.display_name)
        
        if 'trophies' not in doc.keys():
            doc['trophies'] = []
        
        for trophy in author.trophies():
            if trophy.name not in doc['trophies']:
                doc['trophies'].append(trophy.name)
    
    print(count)
    break

