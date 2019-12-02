import myutils
from datetime import datetime
import sys
import os
import pickle
from keras.models import load_model
from gensim.models import Word2Vec, KeyedVectors
from keras.preprocessing import sequence
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
import tensorflow as tf
import numpy


#default mode / type of vulnerability
mode = "sql"

#get the vulnerability from the command line argument
if (len(sys.argv) > 1):
  mode = sys.argv[1]

model = load_model('model/LSTM_model_'+mode+'.h5',custom_objects={'f1_loss': myutils.f1_loss, 'f1':myutils.f1})
  

with open('data/' + mode + '_dataset_finaltest_X', 'rb') as fp:
  FinaltestX = pickle.load(fp)
with open('data/' + mode + '_dataset_finaltest_Y', 'rb') as fp:
  FinaltestY = pickle.load(fp)

now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")

#Prepare the data for the LSTM model

X_finaltest =  numpy.array(FinaltestX)
y_finaltest =  numpy.array(FinaltestY)

#in the original collection of data, the 0 and 1 were used the other way round, so now they are switched so that "1" means vulnerable and "0" means clean.
    
for i in range(len(y_finaltest)):
  if y_finaltest[i] == 0:
    y_finaltest[i] = 1
  else:
    y_finaltest[i] = 0


now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")

print(str(len(X_finaltest)) + " samples in the final test set.")
  
  
csum = 0
for y in y_finaltest:
  csum = csum+y

print("percentage of vulnerable samples: "  + str(int((csum / len(X_finaltest)) * 10000)/100) + "%")
print("absolute amount of vulnerable samples in test set: " + str(csum))

#padding sequences on the same length
max_length = 200   
X_finaltest = sequence.pad_sequences(X_finaltest, maxlen=max_length)

      
      
yhat_classes = model.predict_classes(X_finaltest, verbose=0)
accuracy = accuracy_score(y_finaltest, yhat_classes)
precision = precision_score(y_finaltest, yhat_classes)
recall = recall_score(y_finaltest, yhat_classes)
F1Score = f1_score(y_finaltest, yhat_classes)
  
print("Accuracy: " + str(accuracy))
print("Precision: " + str(precision))
print("Recall: " + str(recall))
print('F1 score: %f' % F1Score)
print("\n")




