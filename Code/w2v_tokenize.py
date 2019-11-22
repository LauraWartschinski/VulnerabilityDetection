import sys
import StringIO
import subprocess
import time

pythondata = ""

mode = "withString" #default
#mode = "withoutString"    


if (len(sys.argv) > 1):
    mode = sys.argv[1]
    
#use the python tokenizer to tokenize the words in the corpus

p = subprocess.Popen(["python", "-m", "tokenize", "w2v/pythontraining" + "_edit.txt"], stdout=subprocess.PIPE)
out, err = p.communicate()

s = StringIO.StringIO(out)
count = 0
totalcount = 0
comment = 0
part = 0

for line in s:
    totalcount = totalcount+1
    count = count+1
    if(totalcount%1000 == 0):
      print(totalcount)
    position1 = line.find(":")+1
    position2 = line.find("'")
    position3 = line[position2+1:].find("'")
    
    cat = line[position1:position2]
    content = line[position2+1:-2]
    
    if ('"""' in line):
      comment = comment+1
      continue
    
    if ("COMMENT" in  cat):
      comment = comment+1
      continue
    
    
    if (mode == "withoutString"):
      if ("STRING" in cat):
        stringstart = line.find("\"")
        content = line[stringstart+1:-2]
        content = "\"string\""
    if ("NL" in cat) or ("NEWLINE" in cat):
      pythondata = pythondata + "\n"
    elif ("INDENT" in cat):
      for x in range(content.count('t')):
        pythondata = pythondata + "  "
    else:
      pythondata = pythondata + " " + content

    #save in parts to reduce computational load
    if count > 1000000:
      print("saving part " + str(part) + " (" + mode + ") " + str(totalcount))
      with open('w2v/pythontraining'+"_"+mode+"_"+str(part), 'w') as outfile:
        outfile.write(pythondata)
      pythondata = ""
      part = part+1
      count = 0

with open('w2v/pythontraining'  +"_"+mode+"_"+str(part), 'w') as outfile:
  outfile.write(pythondata)
