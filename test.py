import sys,time,Queue
import mozCom
j,eventQ=mozCom.initCliFox("localhost")
g=j.gBrowser
try:
 url=sys.argv[1]
except:
 url="http://www.mpsaz.org/"
a=g.addTab(url)
l=[]
while 1:
 try:
  j.recv(0.01)
  a=eventQ.get_nowait()
  l.append(a)
  if a['m']=='e' and a['t']=='load':
   print a.keys()
   d=a['a'][0].target
   print d.location.href
   break
 except Queue.Empty:
  pass
 time.sleep(0.01)
ds=""
while ds!="complete":
 ds=d.readyState
 time.sleep(1)
#print "set"
try:
 j.dd=d
 j.d=d.wrappedJSObject
 d=j.d
 dd=j.dd
except:
 j.d=d
#j.eval("d.toString();");
#print j.d.toString()
#dir(j.d)
print j.d.title
aa=time.time()
docser="""
repl.getDocJson=function(doc)
{
function getNode(n,addToMap)
{
var a,at,al,j,i;
a=[];
a.push(addToMap(cur));
a.push(n.nodeName);
a.push(n.nodeValue);
a.push(n.nodeType);
at=n.attributes;
if(at)
{
al=at.length;
for(j=0;j<al;j++)
{
a.push(at[j].nodeName);
a.push(at[j].nodeValue);
};
};
return a;
};
var func;
if(repl.inMap(doc.firstChild)!=null && repl.inMap(doc.lastChild)!=null)
{
func=repl.inMap;
} else {
func=repl.justAddMap;
};
//func=repl.justAddMap;
var atime,w,l,cur;
atime=repl.time();
l=[];
w=doc.createTreeWalker(doc,NodeFilter.SHOW_ALL,null,0);
while(cur=w.nextNode())
{
l.push(getNode(cur,func));
};
//l.push(repl.time()-atime);
repl.print({"m":"w","a":["docSerializationTime",repl.time()-atime]});
return l;
};
function noop(){};
"""
j.eval(docser);
a=j.eval("repl.getDocJson(d)")
print j.gBrowser.tabs.length
#print a
#j.eval("d.defaultView.repl=repl;d.defaultView.nl=null;d.defaultView.getDocJson=repl.getDocJson;")
#print "write"
#s=d.body.appendChild(d.createElement("script"));
#s.type="text/javascript";
#s.appendChild(d.createTextNode('try{window.nl=getDocJson(document);}catch(e){window.nl=e;};'))
#print s.toString()
#print "write done"
#print d.defaultView.nl[d.defaultView.nl.length-1]
#s.appendChild(d.createTextNode('try{window.nl=getDocJson(document);}catch(e){window.nl=e;};'))
#j.gBrowser.addTab("http://www.mpsaz.org/")
a=time.time()
t=time.time()+1
while a<t:
 a=time.time()
 j.recv(0.1)
