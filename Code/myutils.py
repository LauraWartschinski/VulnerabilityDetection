from keras.datasets import imdb
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import Flatten
from keras.layers import LSTM
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
from keras.models import load_model
from keras.layers.embeddings import Embedding
from keras.layers import Bidirectional
from keras.preprocessing import sequence
from keras import backend as K
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.utils import class_weight
import tensorflow as tf
import builtins
import keyword
import pickle
import numpy
import os
from gensim.models import Word2Vec, KeyedVectors
import tensorflow as tf
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from termcolor import colored


  

def findComments(sourcecode):
  commentareas = []
  
  inacomment = False
  commentstart = -1
  commentend = -1
  
  
  for pos in range(len(sourcecode)):
    if sourcecode[pos] == "#":
      if not inacomment:
        commentstart = pos 
        inacomment = True
    
    if sourcecode[pos] == "\n":
      if inacomment:
        commentend = pos
        inacomment = False
    
    if commentstart >= 0 and commentend >= 0:
      t = [commentstart, commentend]
      commentareas.append(t)
      commentstart = -1
      commentend = -1


  return commentareas


def findposition(badpart,sourcecode):
  splitchars = ["\t", "\n", " ", ".", ":", "(", ")", "[", "]", "<", ">", "+", "-", "=","\"", "\'","*", "/","\\","~","{","}","!","?","*",";",",","%","&"]
  pos = 0
  matchindex = 0
  inacomment = False
  bigcomment = False
  bigcomment2 = False
  startfound = -1
  endfound = -1
  position = []
  end = False
  last = 0
  
  while "#" in badpart:
    f = badpart.find("#")
    badpart = badpart[:f]

  b = badpart.lstrip()
  if len(b) < 1:
  #  print(b)
  #  print("nope.\n\n")
    return[-1,-1]


  while(not end):
    #print("position : " + str(pos))
    
    if not inacomment:
      last = pos-1
    
    if pos >= len(sourcecode):
      end = True
      break
    
    if sourcecode[pos] == "\n":
 #     print("end of comment")
 #     print("[" + sourcecode[last]+ "]")
      inacomment = False
      
    if sourcecode[pos] == "\n" and (sourcecode[pos-1] == "\n" or sourcecode[last] == " "):
      #print("one further")
      pos = pos +1
      continue
      
    if sourcecode[pos] == " " and (sourcecode[pos-1] == " " or sourcecode[last] == "\n"):
     # print("one further")
      pos = pos +1
      continue
      
    if sourcecode[pos] == "#":
      
      inacomment = True
      

#    if sourcecode[pos] == "'":      
#      if pos+2 < len(sourcecode):
#        if sourcecode[pos+1] == "'" and sourcecode[pos+2] == "'":
#          if not bigcomment:
#            pos = pos+3
#            bigcomment = True
#        #    print(">>> BIGCOMMENT")
#            continue
#          else:
#            pos = pos+3
#            bigcomment = False
#         #   print(">>> BIGCOMMENT END")
#            continue

#    if sourcecode[pos] == '"':      
#      if pos+2 < len(sourcecode):
#        if sourcecode[pos+1] == '"' and sourcecode[pos+2] == '"':
#          if not bigcomment2:
#            pos = pos+3
#            bigcomment2 = True
#          #  print(">>> BIGCOMMENT")
#            continue
#          else:
#            pos = pos+3
#            bigcomment2 = False
#           # print(">>> BIGCOMMENT END")
#            continue
      
    if (False):
      
                      print("---------------------------------")
                      string1 = ""
                      string2 = ""
                      for i in range(0,pos):
                        string1 = string1 + sourcecode[i]

                      for i in range(pos+1,len(sourcecode)):
                        string2 = string2 + sourcecode[i]
                        
                      print(string1 + "[" + sourcecode[pos] + "]" + string2)
                      print("---------------------------------")


                      string1 = ""
                      string2 = ""
                      
                      for i in range(0,matchindex):
                        string1 = string1 + badpart[i]

                      for i in range(matchindex+1,len(badpart)):
                        string2 = string2 + badpart[i]
                        
                      print(string1 + "[" + badpart[matchindex] + "]" + string2)
  
                      print("---------------------------------")
                

    if not inacomment: # and not bigcomment and not bigcomment2:
      a = sourcecode[pos]
      if a == "\n":
        a = " "
      b = badpart[matchindex]
      
      c = ""
      if matchindex > 0:
        c = badpart[matchindex-1]
      
      d = ""
      if matchindex < len(badpart)-2:
        d = badpart[matchindex+1]
        
      if (a != b) and (a == " " or a == "\n") and ((b in splitchars) or (c in splitchars)):
        pos = pos+1
        continue
      
      if (a != b) and (b == " " or b == "\n"):
        #print("here")
        if (c in splitchars or d in splitchars):
          #print("here2")
          if (matchindex < len(badpart)-1):
            matchindex = matchindex + 1
            continue
        
      if a == b:
          if matchindex == 0:
            startfound = pos
         # print("\n>>match: " + badpart[matchindex] + "(" + str(matchindex) + "/" + str(len(badpart)) + ")\n\n")
          matchindex = matchindex + 1
          
      else:
          #print("\n>>no match" )
          matchindex = 0
          startfound = -1
        
      if matchindex == len(badpart):
        endfound = pos
    #    print("FOUND at pos "+ str(startfound) + ":" + str(endfound))
        break
        
    if pos == len(sourcecode):
      end = True
    pos = pos + 1
  
  position.append(startfound)
  position.append(endfound)
  
  if endfound < 0:
    startfound = -1
    
  if endfound < 0 and startfound < 0: #and not "#" in badpart and not '"""' in badpart and not "'''" in badpart:
#    print(sourcecode)
#    print(":::::::::::")
#    print(badpart)
#    print("-----------------")
    return[-1,-1]
  return position




def findpositions(badparts,sourcecode):
  
  positions = []
  
  
  for bad in badparts:
    
    if "#" in bad:
      find = bad.find("#")
      bad = bad[:find]
      
    place = findposition(bad,sourcecode)
    if place != [-1,-1]:
      positions.append(place)
    
    
  return positions
  








def nextsplit(sourcecode,focus):
  splitchars = [" ","\t","\n", ".", ":", "(", ")", "[", "]", "<", ">", "+", "-", "=","\"", "\'","*", "/","\\","~","{","}","!","?","*",";",",","%","&"]
  for pos in range(focus+1, len(sourcecode)):
      if sourcecode[pos] in splitchars:
        return pos
  return -1

def previoussplit(sourcecode,focus):
  splitchars = [" ","\t","\n", ".", ":", "(", ")", "[", "]", "<", ">", "+", "-", "=","\"", "\'","*", "/","\\","~","{","}","!","?","*",";",",","%","&"]
  pos = focus-1
  while(pos >= 0):
      if sourcecode[pos] in splitchars:
        return pos
      pos = pos-1
  return -1

def getcontextPos(sourcecode,focus,fulllength):

  
  startcontext = focus
  endcontext = focus
  if focus > len(sourcecode)-1:
    return None

  start = True
  
      
  while not len(sourcecode[startcontext:endcontext]) > fulllength:
   # print(str(startcontext) + ":" + str(endcontext))
   # print(len(sourcecode[startcontext:endcontext]))
    
    if previoussplit(sourcecode,startcontext) == -1 and nextsplit(sourcecode,endcontext) == -1:
   #   print("NONE!")
      return None
    
    if start:
      if previoussplit(sourcecode,startcontext) > -1:
        startcontext = previoussplit(sourcecode,startcontext)
      #print("new start: " + str(startcontext))
      start = False
    else:
      if nextsplit(sourcecode,endcontext) > -1:
        endcontext = nextsplit(sourcecode,endcontext)
      #print("new end: " + str(endcontext))
      start = True

        
#  print("focus: " + str(focus))
#  print("start: " + str(startcontext))
#  print("end: " + str(endcontext))
  return [startcontext,endcontext]

def getcontext(sourcecode,focus,fulllength):

  
  startcontext = focus
  endcontext = focus
  if focus > len(sourcecode)-1:
    return None

  start = True
  
      
  while not len(sourcecode[startcontext:endcontext]) > fulllength:
   # print(str(startcontext) + ":" + str(endcontext))
   # print(len(sourcecode[startcontext:endcontext]))
    
    if previoussplit(sourcecode,startcontext) == -1 and nextsplit(sourcecode,endcontext) == -1:
   #   print("NONE!")
      return None
    
    if start:
      if previoussplit(sourcecode,startcontext) > -1:
        startcontext = previoussplit(sourcecode,startcontext)
      #print("new start: " + str(startcontext))
      start = False
    else:
      if nextsplit(sourcecode,endcontext) > -1:
        endcontext = nextsplit(sourcecode,endcontext)
      #print("new end: " + str(endcontext))
      start = True

        
#  print("focus: " + str(focus))
#  print("start: " + str(startcontext))
#  print("end: " + str(endcontext))
  return sourcecode[startcontext:endcontext]
  











def getblocks(sourcecode, badpositions, step, fulllength):
      blocks = []
       
      focus = 0
      lastfocus = 0
      while (True):
        if focus > len(sourcecode):
          break
        
        focusarea = sourcecode[lastfocus:focus]
                
        if not (focusarea == "\n"):
              
            middle = lastfocus+round(0.5*(focus-lastfocus))              
            context = getcontextPos(sourcecode,middle,fulllength)
            #print([lastfocus,focus,len(sourcecode)])
            
            
            if context is not None:
              
              
                
              vulnerablePos = False
              for bad in badpositions:
                    
                  if (context[0] > bad[0] and context[0] <= bad[1]) or (context[1] > bad[0] and context[1] <= bad[1]) or (context[0] <= bad[0] and context[1] >= bad[1]):
                    vulnerablePos = True
            
                  
              q = -1
              if vulnerablePos:
                q = 0
              else:
                q = 1
              
              
              singleblock = []
              singleblock.append(sourcecode[context[0]:context[1]])
              singleblock.append(q)
                
              already = False
              for b in blocks:
                if b[0] == singleblock[0]:
                #  print("already.")
                  already = True
                  
              if not already:
                blocks.append(singleblock)


        if ("\n" in sourcecode[focus+1:focus+7]):
          lastfocus = focus
          focus = focus + sourcecode[focus+1:focus+7].find("\n")+1
        else:
          if nextsplit(sourcecode,focus+step) > -1:
            lastfocus = focus
            focus = nextsplit(sourcecode,focus+step)
          else:
            if focus < len(sourcecode):
              lastfocus = focus
              focus = len(sourcecode)
            else:
              break

      
      return blocks




def getBadpart(change):
  
  #print("\n")
  removal = False
  lines = change.split("\n")
  for l in lines:
    if len(l) > 0:
      if l[0] == "-":
        #print("a line is removed")
        removal = True
      
  
  if not removal:
    #print("There is no removal.")
    return None
  
  pairs = []
  
  badexamples = []
  goodexamples = []

  for l in range(len(lines)):
    
    line = lines[l]
    line = line.lstrip()
    if len(line.replace(" ","")) > 1:
        if line[0] == "-":
          if not "#" in line[1:].lstrip()[:3] and not "import os" in line:
            badexamples.append(line[1:])
        if line[0] == "+":
          if not "#" in line[1:].lstrip()[:3] and not "import os" in line:
            goodexamples.append(line[1:])
    
  if len(badexamples) == 0:
#    print("removed lines were empty or comments")
    return None
  
  return [badexamples,goodexamples]
    


  

def getTokens(change):
  tokens = []  
  
  change = change.replace(" .",".")
  change = change.replace(" ,",",")
  change = change.replace(" )",")")
  change = change.replace(" (","(")
  change = change.replace(" ]","]")
  change = change.replace(" [","[")
  change = change.replace(" {","{")
  change = change.replace(" }","}")
  change = change.replace(" :",":")
  change = change.replace("- ","-")
  change = change.replace("+ ","+")
  change = change.replace(" =","=")
  change = change.replace("= ","=")
  splitchars = [" ","\t","\n", ".", ":", "(", ")", "[", "]", "<", ">", "+", "-", "=","\"", "\'","*", "/","\\","~","{","}","!","?","*",";",",","%","&"]
  start = 0
  end = 0
  for i in range(0, len(change)):
    if change[i] in splitchars:
      if i > start:
        start = start+1
        end = i
        if start == 1:
          token = change[:end]
        else:
          token = change[start:end]
        if len(token) > 0:
          tokens.append(token)
        tokens.append(change[i])
        start = i
  return(tokens)
  



def removeDoubleSeperatorsString(string):
  return ("".join(removeDoubleSeperators(getTokens(string))))







def removeDoubleSeperators(tokenlist):
    last = ""
    newtokens = []
    for token in tokenlist:
      if token == "\n":
        token = " "
      if len(token) > 0:
        if ((last == " ") and (token == " ")):
          o = 1 #noop
          #print("too many \\n.")
        else:
          newtokens.append(token)
          
        last = token
        
    return(newtokens)
  
  
def isEmpty(code):
  token = getTokens(stripComments(code))
  for t in token:
    if (t != "\n" and t != " "):
      return False
  return True

def is_builtin(name):
    return name in builtins.__dict__
def is_keyword(name):
      return name in keyword.kwlist



def removeTripleN(tokenlist):
    secondlast = ""
    last = ""
    newtokens = []
    for token in tokenlist:
      if len(token) > 0:
        
        if ((secondlast == "\n") and (last == "\n") and (token == "\n")):
          #print("too many \\n.")
          o = 1 #noop
        else:
          newtokens.append(token)
          
        
        thirdlast = secondlast
        secondlast = last
        last = token
        
    return(newtokens)
  
  



def getgoodblocks(sourcecode,goodpositions,fullength):
  blocks = []
  if (len(goodpositions) > 0):
    for g in goodpositions:
     # print("g " + str(g))
      if g != []:
        focus = g[0]
        while (True):
          if focus >= g[1]:
            #print("  too far.")
            break

    #        print("Focus is on " + str(focus) + " " + sourcecode[focus])
            
          
          context = getcontext(sourcecode,focus,fulllength)
          
          if context is not None:
            singleblock = []
            singleblock.append(context)
            singleblock.append(1)
              
            already = False
            for b in blocks:
              if b[0] == singleblock[0]:
              #  print("already.")
                already = True
                  
            if not already:
              blocks.append(singleblock)
              
              
            if nextsplit(sourcecode,focus+15) > -1:
              focus = nextsplit(sourcecode,focus+15)
            else:
              break
      
#  if len(blocks) > 0:
#    print(blocks)
  return blocks




def stripComments(code):
    
  withoutComments = ""
  lines = code.split("\n")
  withoutComments = ""
  therewasacomment = False
  for c in lines:
    if "#" in c:
      therewasacomment = True
      position = c.find("#")
      c = c[:position]
    withoutComments = withoutComments + c + "\n"
  
  
  change = withoutComments
  
  withoutComments = change

  return withoutComments





#Define F1 loss and measurement

def f1_loss(y_true, y_pred):
    
    tp = K.sum(K.cast(y_true*y_pred, 'float'), axis=0)
    tn = K.sum(K.cast((1-y_true)*(1-y_pred), 'float'), axis=0)
    fp = K.sum(K.cast((1-y_true)*y_pred, 'float'), axis=0)
    fn = K.sum(K.cast(y_true*(1-y_pred), 'float'), axis=0)

    p = tp / (tp + fp + K.epsilon())
    r = tp / (tp + fn + K.epsilon())

    f1 = 2*p*r / (p+r+K.epsilon())
    f1 = tf.where(tf.is_nan(f1), tf.zeros_like(f1), f1)
    return 1 - K.mean(f1)
  
  
def f1(y_true, y_pred):
    def recall(y_true, y_pred):
        true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
        possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
        recall = true_positives / (possible_positives + K.epsilon())
        return recall
    def precision(y_true, y_pred):
        true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
        predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
        precision = true_positives / (predicted_positives + K.epsilon())
        return precision
    precision = precision(y_true, y_pred)
    recall = recall(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))



def predict(vectorlist,model): 
  
  if (len(vectorlist) > 0):
    one = []
    one.append(vectorlist)
    one = numpy.array(one)
    max_length = 200
    one = sequence.pad_sequences(one, maxlen=max_length)
    yhat_probs = model.predict(one, verbose=0)
    prediction = int(yhat_probs[0][0] * 100000)
    prediction = 0.00001 * prediction 
    return prediction
    
  else:
    return -1




def getblocksVisual(mode,sourcecode, badpositions,commentareas, fulllength,step, nr,w2v_model,model,threshold,name):

      word_vectors = w2v_model.wv
      
      ypos = 0
      xpos = 0
      
      lines = (sourcecode.count("\n"))
      #print("lines: " + str(lines))
      img = Image.new('RGBA', (2000, 11*(lines+1)))
      color = "white"
      
      blocks = []
       
      focus = 0
      lastfocus = 0
      
      string = ""
      
      trueP = False
      falseP = False
      
      while (True):
        if focus > len(sourcecode):
          break
        
        
        
        comment = False
        for com in commentareas:
          
          if (focus >= com[0] and focus <= com[1] and lastfocus >= com[0] and lastfocus < com[1]):
                focus = com[1]
                #print("within")
                comment = True
          if (focus > com[0] and focus <= com[1] and  lastfocus < com[0]):
              focus = com[0]
              #print("before")
              comment = False                   
          elif (lastfocus >= com[0] and lastfocus < com[1] and focus > com[1]):
              focus = com[1]
              #print("up to the end")
              comment = True
      
        #print([lastfocus,focus,comment, "["+sourcecode[lastfocus:focus]+"]"])
        focusarea = sourcecode[lastfocus:focus]
     
        if(focusarea == "\n"):
          string = string + "\n"
          
        else:
          if comment:
              color = "grey"
              string = string + colored(focusarea,'grey')
          else:
              
              
              middle = lastfocus+round(0.5*(focus-lastfocus))              
              context = getcontextPos(sourcecode,middle,fulllength)
              
              
              if context is not None:
              
                vulnerablePos = False
                for bad in badpositions:
                    if (context[0] > bad[0] and context[0] <= bad[1]) or (context[1] > bad[0] and context[1] <= bad[1]) or (context[0] <= bad[0] and context[1] >= bad[1]):
                      vulnerablePos = True
                      
                predictionWasMade = False
                text = sourcecode[context[0]:context[1]].replace("\n", " ")
                token = getTokens(text)
                if (len(token) > 1):                  
                  vectorlist = []                  
                  for t in token:
                    if t in word_vectors.vocab and t != " ":
                      vector = w2v_model[t]
                      vectorlist.append(vector.tolist())   
                      
                  if len(vectorlist) > 0:
                      p = predict(vectorlist,model)
                      if p >= 0:
                        predictionWasMade = True
                        
                      #  print(p)
                        if vulnerablePos:
                          if p > 0.5:
                            color = "royalblue"
                            string = string + colored(focusarea,'cyan')
                          else:
                            string = string + colored(focusarea,'magenta')
                            color = "violet"
                            
                        else:
                          
                        
                          if p > threshold[0]:
                            color = "darkred"
                          elif p >  threshold[1]:
                            color = "red"
                          elif p >  threshold[2]:
                            color = "darkorange"
                          elif p >  threshold[3]:
                            color = "orange"
                          elif p >  threshold[4]:
                            color = "gold"
                          elif p >  threshold[5]:
                            color = "yellow"
                          elif p >  threshold[6]:
                            color = "GreenYellow"
                          elif p >  threshold[7]:
                            color = "LimeGreen"
                          elif p >  threshold[8]:
                            color = "Green"
                          else:
                            color = "DarkGreen"
                
                          if p > 0.8:
                            string = string + colored(focusarea,'red')
                          elif p > 0.5:
                            string = string + colored(focusarea,'yellow')
                          else:
                            string = string + colored(focusarea,'green')
                            
                if not predictionWasMade:
                  string = string + focusarea
              else:
                string = string + focusarea
                
        
        
            
        try:
          if len(focusarea) > 0:
            d = ImageDraw.Draw(img)
#            print(list(focusarea))
            if focusarea[0] == "\n":
              ypos = ypos + 11
              xpos = 0
              d.text((xpos, ypos), focusarea[1:], fill=color)
              xpos = xpos + d.textsize(focusarea)[0]
            else:
              d.text((xpos, ypos), focusarea, fill=color)
              xpos = xpos + d.textsize(focusarea)[0]

        except Exception as e:
          print(e)

        if ("\n" in sourcecode[focus+1:focus+7]):
          lastfocus = focus
          focus = focus + sourcecode[focus+1:focus+7].find("\n")+1
        else:
          if nextsplit(sourcecode,focus+step) > -1:
            lastfocus = focus
            focus = nextsplit(sourcecode,focus+step)
          else:
            if focus < len(sourcecode):
              lastfocus = focus
              focus = len(sourcecode)
            else:
              break

      
      
      #print(string)
      
      for i in range(1,100):
        if not os.path.isfile('demo_' + mode + "_" + str(i) +"_"+ name + '.png'):
                img.save('demo_' + mode + "_" + str(i) + "_" + name + '.png')    
                print("saved png.")
                break
      return blocks



def getIdentifiers(mode,nr):
  #print("getting " + mode + " " + nr)
  if mode == "sql":
    if nr == "1":
      rep = "instacart/lore"
      com = "a0a5fd945a8bf128d4b9fb6a3ebc6306f82fa4d0"
      myfile = "/lore/io/connection.py"
    elif nr == "2":
      rep = "uktrade/export-wins-data"
      com = "307587cc00d2290a433bf74bd305aecffcbb05a2"
      myfile = "/wins/views/flat_csv.py"
    elif nr == "3":
      rep = "onewyoming/onewyoming"
      com = "54fc7b076fda2de74eeb55e6b75b28e09ef231c2"
      myfile = "/experimental/python/buford/model/visitor.py"
  if mode == "xss":
    if nr == "1":
      rep = "AMfalme/Horizon_Openstack"
      com = "a835dbfbaa2c70329c08d4b8429d49315dc6d651"
      myfile = "/openstack_dashboard/dashboards/identity/mappings/tables.py"
    elif nr == "2":
      rep = "omirajkar/bench_frappe"
      com = "2fa19c25066ed17478d683666895e3266936aee6"
      myfile = "/frappe/website/doctype/blog_post/blog_post.py"
    elif nr == "3":
      rep = "Technikradio/C3FOCSite"
      com = "6e330d4d44bbfdfce9993dffea97008276771600"
      myfile = "/c3shop/frontpage/management/reservation_actions.py"
  if mode == "command_injection":
    if nr == "1":
      rep = "dgabbe/os-x"
      com = "bb2ded2dbbbac8966a77cc8aa227011a8b8772c0"
      myfile = "/os-x-config/standard_tweaks/install_mac_tweaks.py"
    elif nr == "2":
      rep = "Atticuss/ajar"
      com = "5ed8aba271ad20e6168f2e3bd6c25ba89b84484f"
      myfile = "/ajar.py"
    elif nr == "3":
      rep = "yasong/netzob"
      com = "557abf64867d715497979b029efedbd2777b912e"
      myfile = "/src/netzob/Simulator/Channels/RawEthernetClient.py"
  if mode == "xsrf":
    if nr == "1":
      rep = "deepnote/notebook"
      com = "d7becafd593c2958d8a241928412ddf4ba801a42"
      myfile = "/notebook/files/handlers.py"
    elif nr == "2":
      rep = "wbrxcorp/forgetthespiltmilk"
      com = "51bed3f7f01079d91864ddc386a73eb3e1ca634b"
      myfile = "/frontend/app.py"
    elif nr == "3":
      rep = "tricycle/lesswrong"
      com = "ef303fe078c60d964e3f9e87d3da1a67fecd2c2b"
      myfile = "/r2/r2/models/account.py"
  if mode == "remote_code_execution":
    if nr == "1":
      rep = "Internet-of-People/titania-os"
      com = "9b7805119938343fcac9dc929d8882f1d97cf14a"
      myfile = "/vuedj/configtitania/views.py"
    elif nr == "2":
      rep = "Scout24/monitoring-config-generator"
      com = "2191fe6c5a850ddcf7a78f7913881cef1677500d"
      myfile = "/src/main/python/monitoring_config_generator/yaml_tools/readers.py"
    elif nr == "3":
      rep = "pipermerriam/flex"
      com = "329c0a8ae6fde575a7d9077f1013fa4a86112d0c"
      myfile = "/flex/core.py"
  if mode == "path_disclosure":
    if nr == "1":
      rep = "fkmclane/python-fooster-web"
      com = "80202a6d3788ad1212a162d19785c600025e6aa4"
      myfile = "/fooster/web/file.py"
    elif nr == "2":
      rep = "zms-publishing/zms4"
      com = "3f28620d475220dfdb06f79787158ac50727c61a"
      myfile = "/ZMSItem.py"
    elif nr == "3":
      rep = "cuckoosandbox/cuckoo"
      com = "168cabf86730d56b7fa319278bf0f0034052666a"
      myfile = "/cuckoo/web/controllers/submission/api.py"
  if mode == "open_redirect":
      if nr == "1":
        rep = "karambir/mozilla-django-oidc"
        com = "22b6ecb953bbf40f0394a8bfd41d71a3f16e3465"
        myfile = "/mozilla_django_oidc/views.py"
      elif nr == "2":
        rep = "nyaadevs/nyaa"
        com = "b2ddba994ca5e78fa5dcbc0e00d6171a44b0b338"
        myfile = "/nyaa/views/account.py"
      elif nr == "3":
        rep = "richgieg/flask-now"
        com = "03df8ce6bddc56b2487df3898758f4c1624d906f"
        myfile = "/app/auth/views.py"


  
  result = []
  result.append(rep)
  result.append(com)
  result.append(myfile)
  return result
  



def getFromDataset(identifying,data):
  
  result = []
  rep = identifying[0]
  com = identifying[1]
  myfile = identifying[2]
  #print("\n")
  #print("getting from dataset: " + rep + "/commit/" + com + " " + myfile)
  repfound = False
  comfound = False
  filefound = False
  for r in data:
        if  "https://github.com/"+rep ==r:
         #   print("  found repository.")
            repfound = True
            for c in data[r]:
              if c == com:
          #      print("    found commit.")
                comfound = True
                if "files" in data[r][c]:
                    for f in data[r][c]["files"].keys():
                      if myfile == f:  
                          filefound = True
           #               print("      found file")
                          if "source" in data[r][c]["files"][f]:                          
                              allbadparts = []
                              sourcecode = data[r][c]["files"][f]["source"]
                              sourcefull = data[r][c]["files"][f]["sourceWithComments"]
                              
                              
                              for change in data[r][c]["files"][f]["changes"]:
                                badparts = change["badparts"]
                                
                                if (len(badparts) < 20):
                                  for bad in badparts:
                                    pos = findposition(bad,sourcecode)
                                    if not -1 in pos:
                                      allbadparts.append(bad)
                                      
                                                                  
                              result.append(sourcefull)
                              result.append(allbadparts)
                              
                              if not repfound:
                                print("Rep found " + str(repfound))
                              elif not comfound:
                                print("Com found " + str(comfound))
                              elif not filefound:
                                print("File found " + str(filefound))
                              return(result)
                        

  if not repfound:
    print("Rep found " + str(repfound))
  elif not comfound:
    print("Com found " + str(comfound))
  elif not filefound:
    print("File found " + str(filefound))
  return []
