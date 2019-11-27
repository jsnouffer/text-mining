#!/usr/bin/env python
# coding: utf-8

# In[12]:


import re
import pandas as pd
import numpy as np
from sklearn.model_selection import ParameterGrid
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


# In[4]:


df = pd.read_csv('/home/jason/sentiment_data/clean.txt', sep='&&&', header=None, names=['id','sentiment','text'],
                engine='python', index_col=0)


# In[22]:


SAMPLE_PERCENTAGE: float = 0.01
RANDOM_SAMPLE_SEED: int = 42

param_template = {
    'C': [0.01, 0.05, 0.25, 0.5, 1, 2, 3, 5, 8, 13, 20, 40, 80, 100],
    'dual': [True, False],
    'tol':  [0.05], #np.arange(0.001, 0.01, 0.0002),
    'fit_intercept': [True, False],
    'intercept_scaling': [0.01, 0.05, 0.25, 0.5, 1, 2, 3, 5, 8, 13, 20, 40, 80, 100],
    'solver': ['liblinear'],
    'multi_class': ['ovr', 'multinomial', 'auto'],
}

parameter_grid = ParameterGrid(param_template)
len(parameter_grid)


# In[ ]:


def preprocess(text):
    # remove links and special characters
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", text).split())

df_sample = df.sample(frac=SAMPLE_PERCENTAGE, random_state=RANDOM_SAMPLE_SEED)
df_sample['text_processed'] = df_sample['text'].apply(preprocess)

cv = CountVectorizer(binary=True, stop_words='english')
cv.fit(df_sample['text_processed'])
X = cv.transform(df_sample['text_processed'])

X_train, X_val, y_train, y_val = train_test_split(
    X, df_sample['sentiment'], train_size = 0.8)
    
for parameters in parameter_grid:
    
    lr = LogisticRegression(C=parameters['C'],
                            dual=parameters['dual'],
                            tol=parameters['tol'],
                            fit_intercept=parameters['fit_intercept'],
                            intercept_scaling=parameters['intercept_scaling'],
                            solver=parameters['solver'],
                            multi_class=parameters['multi_class'],
                            n_jobs=-1)
    
    try:
        lr.fit(X_train, y_train)
        parameters['score'] = str(accuracy_score(y_val, lr.predict(X_val)))
        print (str(parameters))
    except:
        pass




