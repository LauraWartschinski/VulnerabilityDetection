fulltext = ""
text = []
for i in range(0,71):
  f=open("w2v/pythontraining_" + mode + "_" + str(i), "r")
  contents =f.read()
  fulltext = fulltext + contents
  print("loaded " + str(i))
with open('w2v/pythontraining_'+mode+"_X", 'w') as outfile:
  outfile.write(fulltext)
