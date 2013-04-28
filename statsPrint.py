import re,sys
try:
 import line_profiler
except:
 print """
statsPrint.py prints a line-by-line time usage summary of your python program.
install:
pip install line_profiler
Run:
python codelog.py script [script...]
kernprof.py -l script
python -mline_profiler script.lprof > script.lprof.txt
statsPrint.py script.lprof.txt
This program will print the top three lines from each function moving from longest running to least running.
The lines are ordered by the percentage of time each line takes in the function as a whole.
"""
 sys.exit()
db={}
funcs={}
lines=open(sys.argv[1],"rb").read().split("\n")
file=""
func=""
totalTime=0.0
idx=-1
while idx+1<len(lines):
# print "newFunc",idx
 idx+=1
 i=lines[idx]
# print i
 j=i.lstrip()
 if ":" in j:
  key,val=j.split(":",1)
  val=val.strip()
  if key=="File": file=val
  if key=="Function": func=val.replace(" at ",".")
  if key=="Total time": totalTime=float(val.split(" ",1)[0])
 if j=='':
#  print "blank line",idx
  if len(lines)<=idx+2:
#   print "breaking",len(lines),idx
   break
  if len(lines)>idx+2 and lines[idx+2].startswith("==="):
   idx+=2
   fl=[]
   while len(lines)>idx+1 and lines[idx+1]:
    idx+=1
    i=lines[idx]
#    print i
    try:
     ln,hits,time,perhit,percentTime,line=re.findall("^ *([0-9.]+) *([0-9.]+) *([0-9.]+) *([0-9.]+) *([0-9.]+)  (.*)$",i)[0]
    except:
     continue
#print i; continue
#ln,hits,time,perhit,percentTime=re.findall(r"^ *([0-9]+\.?[0-9]*?) *",i)
#     line=i.rsplit(perhit,1)[1].strip().split(" ",1)[1][6-len(percentTime):]
#    if not hits.strip(): continue
    fl.append({"ln":int(ln.strip()),"hits":int(hits.strip()),"time":int(time.strip()),"perhit":float(perhit.strip()),"percentTime":float(percentTime.strip()),"line":line})
   db['%s$%s$%3f' % (file,func,totalTime,)]=fl
   func=""
   totalTime=0.0
   file=""
   continue

a=sorted(db.items(),key=lambda x: float(x[0].rsplit("$",1)[-1]))
a=[(k,sorted(v,key=lambda x: float(x['percentTime']))) for k,v in a]
bad=[]
#sys.exit(0)
#print len(a)
for k,v in a[::-1]:
# print k
# print len(v)
 x=v[::-1][:3]
# print x
 for l in x:
#  print l['line']
  bad.append(k.rsplit("$",1)[0].replace("$",",")+" "+l['line'])
print "\n".join(bad)
