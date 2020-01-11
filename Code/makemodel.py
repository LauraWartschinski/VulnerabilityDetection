import myutils
import sys
import os.path
import json
from datetime import datetime
import random
import pickle
import numpy
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.preprocessing import sequence
from keras import backend as K
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.utils import class_weight
import tensorflow as tf
from gensim.models import Word2Vec, KeyedVectors



#default mode / type of vulnerability
mode = "sql"

#get the vulnerability from the command line argument
if (len(sys.argv) > 1):
  mode = sys.argv[1]

progress = 0
count = 0


### paramters for the filtering and creation of samples
restriction = [20000,5,6,10] #which samples to filter out
step = 5 #step lenght n in the description
fulllength = 200 #context length m in the description

mode2 = str(step)+"_"+str(fulllength) 

### hyperparameters for the w2v model
mincount = 10 #minimum times a word has to appear in the corpus to be in the word2vec model
iterationen = 100 #training iterations for the word2vec model
s = 200 #dimensions of the word2vec model
w = "withString" #word2vec model is not replacing strings but keeping them

#get word2vec model
w2v = "word2vec_"+w+str(mincount) + "-" + str(iterationen) +"-" + str(s)
w2vmodel = "w2v/" + w2v + ".model"

#load word2vec model
if not (os.path.isfile(w2vmodel)):
  print("word2vec model is still being created...")
  sys.exit()
  
w2v_model = Word2Vec.load(w2vmodel)
word_vectors = w2v_model.wv

#load data
with open('data/plain_' + mode, 'r') as infile:
  data = json.load(infile)
  
now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("finished loading. ", nowformat)

allblocks = []

for r in data:
  progress = progress + 1
  
  for c in data[r]:
    
    if "files" in data[r][c]:                      
    #  if len(data[r][c]["files"]) > restriction[3]:
        #too many files
    #    continue
      
      for f in data[r][c]["files"]:
        
  #      if len(data[r][c]["files"][f]["changes"]) >= restriction[2]:
          #too many changes in a single file
   #       continue
        
        if not "source" in data[r][c]["files"][f]:
          #no sourcecode
          continue
        
        if "source" in data[r][c]["files"][f]:
          sourcecode = data[r][c]["files"][f]["source"]                          
     #     if len(sourcecode) > restriction[0]:
            #sourcecode is too long
     #       continue
          
          allbadparts = []
          
          for change in data[r][c]["files"][f]["changes"]:
            
                #get the modified or removed parts from each change that happened in the commit                  
                badparts = change["badparts"]
                count = count + len(badparts)
                
           #     if len(badparts) > restriction[1]:
                  #too many modifications in one change
           #       break
                
                for bad in badparts:
                  #check if they can be found within the file
                  pos = myutils.findposition(bad,sourcecode)
                  if not -1 in pos:
                      allbadparts.append(bad)
                      
             #   if (len(allbadparts) > restriction[2]):
                  #too many bad positions in the file
             #     break
                      
          if(len(allbadparts) > 0):
         #   if len(allbadparts) < restriction[2]:
              #find the positions of all modified parts
              positions = myutils.findpositions(allbadparts,sourcecode)

              #get the file split up in samples
              blocks = myutils.getblocks(sourcecode, positions, step, fulllength)
              
              for b in blocks:
                  #each is a tuple of code and label
                  allblocks.append(b)


keys = []

#randomize the sample and split into train, validate and final test set
for i in range(len(allblocks)):
  keys.append(i)
random.shuffle(keys)

cutoff = round(0.7 * len(keys)) #     70% for the training set
cutoff2 = round(0.85 * len(keys)) #   15% for the validation set and 15% for the final test set

keystrain = keys[:cutoff]
keystest = keys[cutoff:cutoff2]
keysfinaltest = keys[cutoff2:]

print("cutoff " + str(cutoff))
print("cutoff2 " + str(cutoff2))


with open('data/' + mode + '_dataset_keystrain', 'wb') as fp:
  pickle.dump(keystrain, fp)
with open('data/' + mode + '_dataset_keystest', 'wb') as fp:
  pickle.dump(keystest, fp)
with open('data/' + mode + '_dataset_keysfinaltest', 'wb') as fp:
  pickle.dump(keysfinaltest, fp)

TrainX = []
TrainY = []
ValidateX = []
ValidateY = []
FinaltestX = []
FinaltestY = []


print("Creating training dataset... (" + mode + ")")
for k in keystrain:
  block = allblocks[k]    
  code = block[0]
  token = myutils.getTokens(code) #get all single tokens from the snippet of code
  vectorlist = []
  for t in token: #convert all tokens into their word2vec vector representation
    if t in word_vectors.vocab and t != " ":
      vector = w2v_model[t]
      vectorlist.append(vector.tolist()) 
  TrainX.append(vectorlist) #append the list of vectors to the X (independent variable)
  TrainY.append(block[1]) #append the label to the Y (dependent variable)

print("Creating validation dataset...")
for k in keystest:
  block = allblocks[k]
  code = block[0]
  token = myutils.getTokens(code) #get all single tokens from the snippet of code
  vectorlist = []
  for t in token: #convert all tokens into their word2vec vector representation
    if t in word_vectors.vocab and t != " ":
      vector = w2v_model[t]
      vectorlist.append(vector.tolist()) 
  ValidateX.append(vectorlist) #append the list of vectors to the X (independent variable)
  ValidateY.append(block[1]) #append the label to the Y (dependent variable)

print("Creating finaltest dataset...")
for k in keysfinaltest:
  block = allblocks[k]  
  code = block[0]
  token = myutils.getTokens(code) #get all single tokens from the snippet of code
  vectorlist = []
  for t in token: #convert all tokens into their word2vec vector representation
    if t in word_vectors.vocab and t != " ":
      vector = w2v_model[t]
      vectorlist.append(vector.tolist()) 
  FinaltestX.append(vectorlist) #append the list of vectors to the X (independent variable)
  FinaltestY.append(block[1]) #append the label to the Y (dependent variable)

print("Train length: " + str(len(TrainX)))
print("Test length: " + str(len(ValidateX)))
print("Finaltesting length: " + str(len(FinaltestX)))
now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("time: ", nowformat)


# saving samples

#with open('data/plain_' + mode + '_dataset-train-X_'+w2v + "__" + mode2, 'wb') as fp:
#  pickle.dump(TrainX, fp)
#with open('data/plain_' + mode + '_dataset-train-Y_'+w2v + "__" + mode2, 'wb') as fp:
#  pickle.dump(TrainY, fp)
#with open('data/plain_' + mode + '_dataset-validate-X_'+w2v + "__" + mode2, 'wb') as fp:
#  pickle.dump(ValidateX, fp)
#with open('data/plain_' + mode + '_dataset-validate-Y_'+w2v + "__" + mode2, 'wb') as fp:
#  pickle.dump(ValidateY, fp)
with open('data/' + mode + '_dataset_finaltest_X', 'wb') as fp:
  pickle.dump(FinaltestX, fp)
with open('data/' + mode + '_dataset_finaltest_Y', 'wb') as fp:
  pickle.dump(FinaltestY, fp)
#print("saved finaltest.")

    

#Prepare the data for the LSTM model

X_train =  numpy.array(TrainX)
y_train =  numpy.array(TrainY)
X_test =  numpy.array(ValidateX)
y_test =  numpy.array(ValidateY)
X_finaltest =  numpy.array(FinaltestX)
y_finaltest =  numpy.array(FinaltestY)

#in the original collection of data, the 0 and 1 were used the other way round, so now they are switched so that "1" means vulnerable and "0" means clean.

for i in range(len(y_train)):
  if y_train[i] == 0:
    y_train[i] = 1
  else:
    y_train[i] = 0
    
for i in range(len(y_test)):
  if y_test[i] == 0:
    y_test[i] = 1
  else:
    y_test[i] = 0
    
for i in range(len(y_finaltest)):
  if y_finaltest[i] == 0:
    y_finaltest[i] = 1
  else:
    y_finaltest[i] = 0


now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("numpy array done. ", nowformat)

print(str(len(X_train)) + " samples in the training set.")      
print(str(len(X_test)) + " samples in the validation set.") 
print(str(len(X_finaltest)) + " samples in the final test set.")
  
csum = 0
for a in y_train:
  csum = csum+a
print("percentage of vulnerable samples: "  + str(int((csum / len(X_train)) * 10000)/100) + "%")
  
testvul = 0
for y in y_test:
  if y == 1:
    testvul = testvul+1
print("absolute amount of vulnerable samples in test set: " + str(testvul))

max_length = fulllength 
  

#hyperparameters for the LSTM model

dropout = 0.2
neurons = 100
optimizer = "adam"
epochs = 100
batchsize = 128

now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("Starting LSTM: ", nowformat)


print("Dropout: " + str(dropout))
print("Neurons: " + str(neurons))
print("Optimizer: " + optimizer)
print("Epochs: " + str(epochs))
print("Batch Size: " + str(batchsize))
print("max length: " + str(max_length))

#padding sequences on the same length
X_train = sequence.pad_sequences(X_train, maxlen=max_length)
X_test = sequence.pad_sequences(X_test, maxlen=max_length)
X_finaltest = sequence.pad_sequences(X_finaltest, maxlen=max_length)

#creating the model  
model = Sequential()
model.add(LSTM(neurons, dropout = dropout, recurrent_dropout = dropout)) #around 50 seems good
model.add(Dense(1, activation='sigmoid'))
model.compile(loss=myutils.f1_loss, optimizer='adam', metrics=[myutils.f1])

now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("Compiled LSTM: ", nowformat)

#account with class_weights for the class-imbalanced nature of the underlying data
class_weights = class_weight.compute_class_weight('balanced',numpy.unique(y_train),y_train)

#training the model
history = model.fit(X_train, y_train, epochs=epochs, batch_size=batchsize, class_weight=class_weights) #epochs more are good, batch_size more is good

#validate data on train and test set

for dataset in ["train","test","finaltest"]:
    print("Now predicting on " + dataset + " set (" + str(dropout) + " dropout)")
    
    if dataset == "train":
      yhat_classes = model.predict_classes(X_train, verbose=0)
      accuracy = accuracy_score(y_train, yhat_classes)
      precision = precision_score(y_train, yhat_classes)
      recall = recall_score(y_train, yhat_classes)
      F1Score = f1_score(y_train, yhat_classes)
      
    if dataset == "test":
      yhat_classes = model.predict_classes(X_test, verbose=0)
      accuracy = accuracy_score(y_test, yhat_classes)
      precision = precision_score(y_test, yhat_classes)
      recall = recall_score(y_test, yhat_classes)
      F1Score = f1_score(y_test, yhat_classes)
      
      
    if dataset == "finaltest":
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



now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("saving LSTM model " + mode + ". ", nowformat)
model.save('model/LSTM_model_'+mode+'.h5')  # creates a HDF5 file 'my_model.h5'
print("\n\n")



