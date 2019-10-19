#!/usr/bin/env python
# coding: utf-8

import tweepy
import time
from datetime import datetime
from newsapi import NewsApiClient
from geopy.geocoders import Nominatim
import pandas as pd

# Format of config.py:
# twitter_public_key = "XXXXXXXXXXXXXXXXXXXXXXXX"
# twitter_private_key = "XXXXXXXXXXXXXXXXXXXXXXXX"
# twitter_public_token = "XXXXXXXXXXXXXXXXXXXXXXXX"
# twitter_private_token = "XXXXXXXXXXXXXXXXXXXXXXXX"
# google_news_key = "XXXXXXXXXXXXXXXXXXXXXXXX"

exec(open("config.py").read())
newsapi = NewsApiClient(api_key = google_news_key)


# ## Twitter Authentication

def authenticate(api_key, secret_key, access_token, secret_token):

    auth = tweepy.OAuthHandler(api_key, secret_key)
    auth.set_access_token(access_token, secret_token)
    twitter = tweepy.API(auth, 
                     wait_on_rate_limit=True, 
                     wait_on_rate_limit_notify=True)
  
    return twitter

twitter = authenticate(twitter_public_key, twitter_private_key, twitter_public_token, twitter_private_token)

rateLimitStatus = twitter.rate_limit_status()
print("Trends Remaining: ", rateLimitStatus['resources']['trends']['/trends/place']['remaining'])
print("Tweets Remaining: ", rateLimitStatus['resources']['tweets']['/tweets/search/:product/:label']['remaining'])
timestamp = rateLimitStatus['resources']['tweets']['/tweets/search/:product/:label']['reset']
print("Will reset at: ", datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'))


def limit_handled(cursor):
    
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            time.sleep(2)
            continue


# ## Lookup Yahoo WOEID for Desired Location

LOC = "Philadephia, Pa"
geolocator = Nominatim(user_agent="my-application")
coordinates = geolocator.geocode(LOC)
trend_node = twitter.trends_closest(coordinates.latitude, coordinates.longitude)[0]
woeid = trend_node['woeid']
print(trend_node)


# ## Compile a list of hashtags from trending tweets

trends = twitter.trends_place(woeid)
tags = set()
for trend in trends[0]['trends']:
    tweets = twitter.search(trend['query'], lang="en", rpp=10)
    for tweet in tweets:
        for tag in tweet._json['entities']['hashtags']:
            tags.add(tag['text'].lower())
print (tags)


# ## Search Google News with compiled tags; then dump results in a dataframe

df = pd.DataFrame(columns = ['date', 'source', 'author', 'title', 'description', 'url'])
for tag in tags:
    results = newsapi.get_everything(q = tag, language = 'en', sort_by = 'relevancy')
    for result in results['articles']:
        df = df.append(pd.Series(
            [result['publishedAt'], result['source']['name'], result['author'], result['title'], result['description'], result['url']],
            index = df.columns ), ignore_index=True)


# ## Remove duplicate search results from dataframe and export to CSV

wdir = '/home/jason/documents/'
date = datetime.now().strftime("%Y%m%d_%H%M%S")

df.drop_duplicates(subset = "url", keep = False, inplace = True)
df.to_csv(wdir + '/' + 'news_' + date + '.csv')
df

