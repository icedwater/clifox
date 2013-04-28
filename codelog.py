import sys,os,os.path
sig="#pyperflog"
if sys.argv[1]=="clean":
 files=[i for i in sys.argv[2:] if os.path.isfile(i)]
 if not files:
  files=[i for i in os.listdir("./") if os.path.isfile(i)]
 for fn in files:
  fh=open(fn,"rb")
  l=fh.read().split("\n")
  fh.close()
  if [i for i in l if sig in i]:
   fh=open(fn,"wb")
   fh.write("\n".join([i for i in l if sig not in i]))
   fh.close()
 sys.exit(0)
files=[i for i in sys.argv[1:] if os.path.isfile(i)]
for fn in files:
 fh=open(fn,"rb")
 fc=fh.read()
 fh.close()
 lines=fc.split("\n")
 i=len(lines)
 while i>0:
  i-=1
  l=lines[i].strip()
  if l.split(" ",1)[0]=="def" and l.split("(",1)[0].strip().rsplit(" ",1)[1]!="__getattr__":
   spaces=lines[i].find("def ")
   lines.insert(i,(" "*spaces)+"@profile %s" % (sig,))
 out="\n".join(lines)
 fh=open(fn,"wb")
 fh.write(out)
 fh.close()
