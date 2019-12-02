import myutils
from datetime import datetime
import os
import sys
import numpy
from keras.models import load_model
from gensim.models import Word2Vec, KeyedVectors



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
  
mode2 = mode + nr

now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("time:", nowformat)


mincount = 10
iterationen = 300
s = 200
w2v = "word2vec_"+"withString"+str(mincount) + "-" + str(iterationen) +"-" + str(s)
w2vmodel = "w2v/" + w2v + ".model"
w2v_model = Word2Vec.load(w2vmodel)
word_vectors = w2v_model.wv
                

model = load_model('model/LSTM_model_'+mode+'.h5',custom_objects={'f1_loss': myutils.f1_loss, 'f1':myutils.f1})


with open('examples/'+mode+"-"+nr+".py", 'r') as infile:
  sourcecodefull = infile.read()


commentareas = myutils.findComments(sourcecodefull)
myutils.getblocksVisual(mode2,sourcecodefull,[], commentareas, 200,5, 0, w2v_model,model,threshold2,"sourcecode")

