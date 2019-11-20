#!/usr/bin/env python2
# coding: utf-8

import os
import sys
import socket
import string
import time
import urllib2
import HTMLParser
import zlib

import libirc

HOST="irc.freenode.net"
PORT=6667
NICK="titlebot"
IDENT="titlebot"
REALNAME="titlebot"
CHANS=["##Orz"]

def ParseURL(s):
    http_idx=s.find('http:')
    https_idx=s.find('https:')
    if https_idx==-1:
        if http_idx==-1:
            return None
        else:
            return s[http_idx:]
    else:
        if http_idx==-1:
            return s[https_idx:]
        else:
            return s[min(http_idx, https_idx):]

try:
    c=libirc.IRCConnection()
    c.connect((HOST, PORT))
    c.setnick(NICK)
    c.setuser(IDENT, REALNAME)
    for CHAN in CHANS:
        c.join(CHAN)
except:
    time.sleep(10)
    sys.stderr.write("Restarting...\n")
    os.execlp("python2", "python2", __file__)
    raise
CHAN=CHANS[0]
socket.setdefaulttimeout(10)

html_parser=HTMLParser.HTMLParser()

quiting=False
while not quiting:
    if not c.sock:
        quiting=True
        time.sleep(10)
        sys.stderr.write("Restarting...\n")
        os.execlp("python2", "python2", __file__)
        break
    try:
        line=c.recvline(block=True)
        if not line:
            continue
        sys.stderr.write("%s\n" % line.encode('utf-8', 'replace'))
        line=c.parse(line=line)
        if line and line["cmd"]=="PRIVMSG":
            if line["dest"]==NICK:
                if line["msg"]==u"Get out of this channel!": # A small hack
                    c.quit(u"%s asked to leave." % line["nick"])
                    quiting=True
            else:
                CHAN=line["dest"]
                for w in line["msg"].split():
                    w=ParseURL(w)
                    if w:
                        w=w.split(">", 1)[0].split('"', 1)[0]
                        if re.match("https?:/*git.io(/|$)", w): # Fix buggy git.io
                            continue
                        opener=urllib2.build_opener()
                        opener.addheaders = [("Accept-Charset", "utf-8, iso-8859-1"), ("Accept-Language", "zh-cn, zh-hans, zh-tw, zh-hant, zh, en-us, en-gb, en"), ("Range", "bytes=0-16383"), ("User-Agent", "Mozilla/5.0 (compatible; Titlebot; like IRCbot; +https://github.com/m13253/titlebot)"), ("X-Forwarded-For", "10.2.0.101"), ("X-moz", "prefetch"), ("X-Prefetch", "yes")]
                        h=opener.open(w.encode("utf-8", "replace"))
                        if h.code==200 or h.code==206:
                            if not "Content-Type" in h.info() or h.info()["Content-Type"].split(";")[0]=="text/html":
                                wbuf=h.read(16384)
                                read_times=1
                                while len(wbuf)<16384 and read_times<4:
                                    read_times+=1
                                    wbuf_=h.read(16384)
                                    if wbuf_:
                                        wbuf+=wbuf_
                                    else:
                                        break
                                if "Content-Encoding" in h.info() and h.info()["Content-Encoding"]=="gzip": # Fix buggy www.bilibili.tv
                                    try:
                                        gunzip_obj=zlib.decompressobj(16+zlib.MAX_WBITS)
                                        wbuf=gunzip_obj.decompress(wbuf)
                                    except:
                                        pass
                                if wbuf.find("<title>")!=-1:
                                    titleenc=wbuf.split("<title>")[1].split("</title>")[0]
                                    title=None
                                    for enc in ("utf-8", "gbk", "gb18030", "iso-8859-1"):
                                        try:
                                            title=titleenc.decode(enc)
                                            break
                                        except UnicodeDecodeError:
                                            pass
                                    if title==None:
                                        title=title.decode("utf-8", "replace")
                                    title=html_parser.unescape(title).replace("\r", "").replace("\n", " ").strip()
                                    c.say(CHAN, u"⇪标题: %s" % title)
                                else:
                                    c.say(CHAN, u"⇪无标题网页")
                            else:
                                if "Content-Range" in h.info():
                                    c.say(CHAN, u"⇪文件类型: %s, 文件大小: %s 字节\r\n" % (h.info()["Content-Type"], h.info()["Content-Range"].split("/")[1]))
                                elif "Content-Length" in h.info():
                                    c.say(CHAN, u"⇪文件类型: %s, 文件大小: %s 字节\r\n" % (h.info()["Content-Type"], h.info()["Content-Length"]))
                                else:
                                    c.say(CHAN, u"⇪文件类型: %s\r\n" % h.info()["Content-Type"])
                        else:
                            c.say(CHAN, u"⇪HTTP %d 错误\r\n" % h.code)
    except Exception as e:
        try:
            c.say(CHAN, u"哎呀，%s 好像出了点问题: %s" % (NICK, e))
        except:
            pass
    except socket.error as e:
        sys.stderr.write("Error: %s\n", e)
        c.quit("Network error.")

# vim: et ft=python sts=4 sw=4 ts=4
