#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().run_line_magic('run', 'classifier.py')


# In[ ]:


classifier = Classifier()
with open('/home/jason/git/trumptweets/data/clean.txt') as f:
    count = 0
    for line in f:
        count = count + 1
        classifier.preprocess(line, web=False)
        
        if count % 1000 == 0:
            print("Loaded " + str(count) + " lines so far")
    print("Loaded all " + str(count) + " lines")
    print("Starting prediction")
    res = more_magic(classifier)
    res['type'] = ''.join([key[0] for key in res.keys()])
    print(res)

