import sys,string
fh=open(sys.argv[1],"rb")
l=fh.read().split("\n")
fh.close()
i=-1
while 1:
 i+=1
 if len(l)<=i:
  break
 t=l[i].strip()
 if t.startswith("//"):
  continue
 tl=t.lower()
 if "function " in tl or "function(" in tl and (l[i+1].strip()=="{" or t.endswith("{")):
  if ":" in tl and not [j for j in tl.split(":",1)[0] if j not in string.letters+string.digits+"_"]:
   name=t.split(":",1)[0]
  else: #function test(args)
   name=t.split("(",1)[0].strip().rsplit(" ",1)[-1]
  #line is +1 because we read files 1-based, e.g. first line is line 1
  ls='error("clifox:js:func","%s, line %d");//$log' % (name,i+1,)
  l.insert(i+1,ls)
 else: #not a function
  continue
print "\n".join(l)

