#!/usr/bin/env python3

################
# Imports
################

import os
import pickle
from bs4 import BeautifulSoup
import urllib3
import certifi
import re
import sys
import argparse as ap
#from argparse import ArgumentParser, REMINDER

################
# Functions
################

# Function to flatten a list
flatten = lambda l: [item for sublist in l for item in sublist]
# cheers to https://stackoverflow.com/a/952952

# Get and parse out links
def getytlinks(link):
    pm = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
    html_page = pm.request('GET', link)
    soup = BeautifulSoup(html_page.data, "lxml")
    links = [a.get('href') for a in soup('a') if a.get('href')]

    # Pick out youtube links
    new_links = [x for x in links if re.match("^https://youtu\.be", x)]
    newer_links = [x for x in links if re.match("^https://www\.youtube\.com/watch", x)]
    # the youtube.com links are not always well formatted for mpv, so we reformat them:
    for lk in newer_links:
        videolabel = re.search('v=([^&?]*)', lk)[1]
        if videolabel is None:
            print('Reddytt: skipping URL without video label:', lk)
            continue
        new_links.append('https://www.youtube.com/watch?v=' + videolabel)
    # in principal, add anything here you want. I guess all of these should work: https://rg3.github.io/youtube-dl/supportedsites.html
    return new_links, links

################
# Main
################

if __name__ == '__main__':

    parser = ap.ArgumentParser(usage='%(prog)s [options] <subreddit> [-- [mpv-arguments]]', description='Play the youtube links from your favourite subreddit.')

    parser.add_argument('--depth', metavar='d', type=int, default=0, help='How many pages into the subreddit you want to go.')
    parser.add_argument('subreddit', type=str, help='The subreddit you want to play.')
    parser.add_argument('mpv', nargs=ap.REMAINDER, help='Arguments to pass to `mpv`.')

    args = parser.parse_args()

    subreddit = args.subreddit
    depth = args.depth
    mpv = " ".join(args.mpv)

    subreddit_link = "https://reddit.com/r/" + subreddit

    # Setup working directory
    work_dir = os.environ['HOME'] + "/.reddytt"
    sr_dir = work_dir + "/%s" % subreddit
    seen_file = sr_dir + "/seen"
    seen_links = []
    unseen_file = sr_dir + "/unseen"
    unseen_links = []
    print("Reddytt: Checking for reddytt working directory (%s)." % work_dir)

    if not os.path.isdir(work_dir):
        print("Reddytt: Working directory not found. Creating %s, and files." % work_dir)
        os.mkdir(work_dir)
        os.mkdir(sr_dir)
        os.system("touch %s" % seen_file)
        with open(seen_file, 'wb') as f:
            pickle.dump(seen_links, f)
        os.system("touch %s" % unseen_file)
        with open(unseen_file, 'wb') as f:
            pickle.dump(unseen_links, f)
    elif not os.path.isdir(sr_dir):
        print("Reddytt: Working directory found, but no subreddit directory. Creating %s, and files." % sr_dir)
        os.mkdir(sr_dir)
        os.system("touch %s" % seen_file)
        with open(seen_file, 'wb') as f:
            pickle.dump(seen_links, f)
        os.system("touch %s" % unseen_file)
        with open(unseen_file, 'wb') as f:
            pickle.dump(unseen_links, f)
    else:
        print("Reddytt: Working directory found. Loading variables.")
        with open(seen_file, 'rb') as f:
            seen_links = pickle.load(f)
        with open(unseen_file, 'rb') as f:
            unseen_links = pickle.load(f)

    new_links, links = getytlinks(subreddit_link)

    # Go deeper
    if depth > 0:
        for d in range(depth):
            link = ""
            for l in links:
                if re.search("after=", l):
                    link = l
            if link == "":
                print("Reddytt: Could not identify 'after'-variable to progress deeper.")
            else:
                newer_links, links = getytlinks(link)
                new_links += newer_links
                new_links = list(set(new_links))

    # we also want to watch the stored ones
    new_links += unseen_links
    new_links = list(set(new_links))

    # Start watching
    save_links = new_links
    for link in new_links:
        if link in seen_links:
            print("Reddytt: Link seen. Skipping.")
        else:
            x = os.system("mpv %(args)s %(link)s" % {"link": link, "args": mpv})
            print("Reddytt: That was: %s" % link)
            if x == 0:
                # The video finished or you hit 'q' (or whatever your binding is), this is a good exit.
                # Store the video in seen_links.
                seen_links.append(link)
                save_links.remove(link)
            elif x == 1024:
                # You made a hard exit, and want to stop. (Ctrl+C)
                # Store the links and exit the program.
                print("Reddytt: Forced exit detected. Saving and exiting.")
                with open(seen_file, 'wb') as f:
                    pickle.dump(seen_links, f)
                with open(unseen_file, 'wb') as f:
                    pickle.dump(save_links, f)
                # Exit program.
                sys.exit()
            else:
                # Something else happened. Bad link perhaps.
                # Store in seen_links to avoid in the future.

                seen_links.append(link)
                save_links.remove(link)

    # The playlist is finished. Save everything.
    with open(seen_file, 'wb') as f:
        pickle.dump(seen_links, f)
    with open(unseen_file, 'wb') as f:
        pickle.dump(save_links, f)
