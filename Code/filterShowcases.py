import requests
import time
import sys
import json
import os 

repositories = {}
data = {}


#get mined commits
repositories = {}
with open('all_commits.json', 'r') as infile:
    repositories = json.load(infile)
    
#load progress
if os.path.isfile('DataFilter.json'):
  with open('DataFilter.json', 'r') as infile:
      data = json.load(infile)


if not "showcase" in data:
  data["showcase"] = {}
if not "noshowcase" in data:
  data["noshowcase"] = {}
    
    

toomuchsecurity = ['offensive', 'pentest', 'vulnerab', 'security', 'hack', 'exploit', 'ctf ', ' ctf', 'capture the flag','attack'] #keywords that are not allowed to appear in the repository name
alittletoomuch = ['offensive security', 'pentest', 'exploits', 'vulnerability research', 'hacking', 'security framework', 'vulnerability database', 'simulated attack', 'security research'] #keywords that are not allowed to appear in the readme description



#get access token
if not os.path.isfile('access'):
  print("please place a Github access token in this directory.")
  sys.exit()
with open('access', 'r') as accestoken:
  access = accestoken.readline().replace("\n","")
myheaders = {'Authorization': 'token ' + access}


for repo in repositories:
    #get name of the repository
    name = repo.split('https://github.com/')[1]
    
    #if we don't know yet if it is a showcase...
    if (name in data['showcase']):
        continue
    if (name in data['noshowcase']):
        continue
    
    #check all the 'toomuch' keywords to see if they already appear in the name of the repository
    for toomuch in toomuchsecurity:
      if toomuch in name:
        #put it in the showcase categpry
        data['showcase'][name] = {}
        print(name + ": showcase")
        continue

    #get the readme of the repository
    response = requests.get('https://github.com/'+name+'/blob/master/README.md', headers = myheaders)        
    h = response.headers
            
    if ("markdown-body") in response.text:
      #find the description of the project
      pos = response.text.find("markdown-body")
      pos2 = response.text.find("/article")
      description = response.text[pos:pos2]
      
      #check all keywords from the 'alittletoomuch' category
      for toomuch in alittletoomuch: 
        if toomuch in description:
          #put it in the showcase category
          data['showcase'][name] = {}
          print(name + ": showcase")
          continue
      

    #otherwise, put it in the "noshowcase" category
    print(name + ": not a showcase")
    data['noshowcase'][name] = {}
      
    with open('DataFilter.json', 'w') as outfile:
          json.dump(data, outfile)


