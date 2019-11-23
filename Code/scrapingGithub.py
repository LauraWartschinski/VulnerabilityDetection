import os
import requests
import time
import sys
import json
from requests_oauthlib import OAuth1Session
from requests_oauthlib import OAuth1


def searchforkeyword(key, commits, access):
  #collect links from the github API response
  maximum = 9999  
  new = 0


  #craft request for Github
  params = (
      ('q', key),('per_page',100)
  )
  myheaders = {'Accept': 'application/vnd.github.cloak-preview', 'Authorization': 'token ' + access}
  nextlink = "https://api.github.com/search/commits"

  for i in range(0,maximum):
      print(str(len(commits)) + " commits so far.")
      print
      limit = 0
      while(limit == 0):
          #request search results
          response = requests.get(nextlink, headers=myheaders,params=params)
          h = response.headers
          if 'X-RateLimit-Remaining' in h:
            limit = int(h['X-RateLimit-Remaining'])
            if limit == 0:
                # Limit of requests per time was reached, sleep to wait until we can request again
                print("Rate limit. Sleep.")
                time.sleep(35)
            #else:
            #  print(h)
      if 'Link' not in h:
        break;
      
      #go through all elements in Github's reply
      content = response.json()
      for k in range(0, len(content["items"])):
          #get relevant info
          repo = content["items"][k]["repository"]["html_url"]
          if repo not in commits:
              #new repository, new commit
              c = {}
              c["url"] = content["items"][k]["url"]
              c["html_url"] = content["items"][k]["html_url"]
              c["message"] = content["items"][k]["commit"]["message"]
              c["sha"] = content["items"][k]["sha"]
              c["keyword"] = key
              commits[repo] = {}
              commits[repo][content["items"][k]["sha"]] = c;
          else:
              if not content["items"][k]["sha"] in commits[repo]:
                #new commit for this already known repository
                new = new + 1
                c = {}
                c["url"] = content["items"][k]["url"]
                c["html_url"] = content["items"][k]["html_url"]
                c["sha"] = content["items"][k]["sha"]
                c["keyword"] = key
                commits[repo][content["items"][k]["sha"]] = c;
                
                
      #get the links to the next results
      link = h['Link']
      reflinks = analyzelinks(link)
      if "last" in reflinks:
          lastnumber = reflinks["last"].split("&page=")[1]
          maximum = int(lastnumber)-1
      if not "next" in reflinks:
          #done with all that could be collected
          break
      else:
          nextlink = reflinks["next"]
          
  #save the commits that were found
  with open('all_commits.json', 'w') as outfile:
      json.dump(commits, outfile)



def analyzelinks(link):
    #get references to the next page of results
    
    link = link + ","
    reflinks = {}
    while "," in link:
        pos = link.find(",")
        text = link[:pos]
        rest = link[pos+1:]
        try:
          if "\"next\"" in text:
              text = text.split("<")[1]
              text = text.split(">;")[0]
              reflinks["next"]=text
          if "\"prev\"" in text:
              text = text.split("<")[1]
              text = text.split(">;")[0]
              reflinks["prev"]=text
          if "\"first\"" in text:
              text = text.split("<")[1]
              text = text.split(">;")[0]
              reflinks["first"]=text
          if "\"last\"" in text:
              text = text.split("<")[1]
              text = text.split(">;")[0]
              reflinks["last"]=text
        except IndexError as e:
            print(e)
            print("\n")
            print(text)
            print("\n\n")
            sys.exit()
        link = rest
    return(reflinks)





#------------------------------------



if not os.path.isfile('access'):
  print("please place a Github access token in this directory.")
  sys.exit()
  
with open('access', 'r') as accestoken:
  access = accestoken.readline().replace("\n","")

commits = {}

#load previously scraped commits
with open('all_commits.json', 'r') as infile:
    commits = json.load(infile)
    

keywords = ["buffer overflow","denial of service", "dos", "XXE","vuln","CVE","XSS","NVD","malicious","cross site","exploit","directory traversal","rce","remote code execution","XSRF","cross site request forgery","click jack","clickjack","session fixation","cross origin","infinite loop","brute force","buffer overflow","cache overflow","command injection","cross frame scripting","csv injection","eval injection","execution after redirect","format string","path disclosure","function injection","replay attack","session hijacking","smurf","sql injection","flooding","tampering","sanitize","sanitise", "unauthorized", "unauthorised"]

prefixes =["prevent", "fix", "attack", "protect", "issue", "correct", "update", "improve", "change", "check", "malicious", "insecure", "vulnerable", "vulnerability"]

#for all combinations of keywords and prefixes, scrape github for commits
for k in keywords:
  for pre in prefixes:
      searchforkeyword(k + " " + pre, commits, access);
