import myutils
from termcolor import colored
from datetime import datetime
import sys
from keras.models import load_model
from keras.preprocessing import sequence
from gensim.models import Word2Vec, KeyedVectors
import json
threshold = []
threshold1 = [0.9,0.8,0.7,0.6,0.5,0.4,0.3,0.2,0.1]
threshold2 = [0.9999,0.999,0.99,0.9,0.5,0.1,0.01,0.001,0.0001]


mode = "sql"
nr = "1"
fine = ""

if (len(sys.argv) > 1):
  mode = sys.argv[1]
  if len(sys.argv) > 2:
    nr = sys.argv[2]
    if len(sys.argv) > 3:
      fine = sys.argv[3]
      
if fine == "fine":
  threshold = threshold2
else:
  threshold = threshold1

mincount = 10
iterationen = 100
s = 200
w2v = "word2vec_"+"withString"+str(mincount) + "-" + str(iterationen) +"-" + str(s)
w2vmodel = "w2v/" + w2v + ".model"

w2v_model = Word2Vec.load(w2vmodel)
word_vectors = w2v_model.wv


step = 5
fulllength = 200
                

rep = ""
com = ""
myfile = ""
    
progress = 0
count = 0

step = 5
fulllength = 200


if (len(sys.argv) > 1):
  mode = sys.argv[1]
  if len(sys.argv) > 2:
    nr = sys.argv[2]
    if len(sys.argv) > 3:
      fine = sys.argv[3]
      

  


print(mode)
model = load_model('model/LSTM_model_'+mode+'.h5',custom_objects={'f1_loss': myutils.f1_loss, 'f1':myutils.f1})

with open('data/plain_' + mode, 'r') as infile:
  data = json.load(infile)
  

print("finished loading")  
identifying = myutils.getIdentifiers(mode,nr)
info = myutils.getFromDataset(identifying,data)
sourcefull = info[0]
allbadparts = info[1]
positions = myutils.findpositions(allbadparts,sourcefull)
commentareas = myutils.findComments(sourcefull)
myutils.getblocksVisual(mode,sourcefull, positions, commentareas, fulllength, step, nr, w2v_model, model, threshold, "labeled-"+mode+"-"+nr  )
                            
