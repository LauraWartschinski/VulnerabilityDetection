import nltk
from gensim.models import Word2Vec, KeyedVectors
import os.path
import pickle
import sys

all_words = []
    
mode = "withString" #default
if (len(sys.argv) > 1):
    mode = sys.argv[1]
    

# Loading the training corpus
print("Loading " + mode)  
with open('w2v/pythontraining' + '_'+mode+"_X", 'r') as file:
    pythondata = file.read().lower().replace('\n', ' ')

print("Length of the training file: " + str(len(pythondata)) + ".")
print("It contains " + str(pythondata.count(" ")) + " individual code tokens.")

# Preparing the dataset (or loading already processed dataset to not do everything again)
if (os.path.isfile('data/pythontraining_processed_' + mode)):
  with open ('data/pythontraining_processed_' + mode, 'rb') as fp:
    all_words = pickle.load(fp)
  print("loaded processed model.")
else:  
  print("now processing...")
  processed = pythondata
  all_sentences = nltk.sent_tokenize(processed)
  all_words = [nltk.word_tokenize(sent) for sent in all_sentences]
  print("saving")
  with open('data/pythontraining_processed_' + mode, 'wb') as fp:
    pickle.dump(all_words, fp)

print("processed.\n")

#trying out different parameters
for mincount in [10,30,50,100,300,500,5000]:
  for iterationen in [1,5,10,30,50,100]:
    for s in [5,10,15,30,50,75,100,200,300]:

      print("\n\n" + mode + " W2V model with min count " + str(mincount) + " and " + str(iterationen) + " Iterationen and size " + str(s))
      fname = "w2v/word2vec_"+mode+str(mincount) + "-" + str(iterationen) +"-" + str(s)+ ".model"

      if (os.path.isfile(fname)):
        print("model already exists.")
        continue
      
      else:
        print("calculating model...")
        # training the model
        model = Word2Vec(all_words, size=s, min_count=mincount, iter=iterationen, workers = 4)  
        vocabulary = model.wv.vocab

        #print some examples
        
        #words = ["import", "true", "while", "if", "try", "in", "+", "x", "=", ":", "[", "print", "str", "count", "len", "where", "join", "split", "==", "raw_input"]
        #for similar in words:
        #  try:
        #    print("\n")
        #    print(similar)
        #    sim_words = model.wv.most_similar(similar)  
        #    print(sim_words)
        #    print("\n")
        #  except Exception as e:
        #    print(e)
        #    print("\n")

        #saving the model
        model.save(fname)



