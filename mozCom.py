import os,sys,select,socket,time,Queue,urllib
import utils,configParser
try:
 try:
  try:
   import ujson as json
  except:
   import json
 except:
  import simplejson as json
except:
 print("Either the JSON or simplejson module needs to be installed. Data is passed from Firefox to Python using the JSON format.")
 sys.exit(1)
try:
 dbg=configParser.config.dbg
except:
 dbg=0
dbgl=[]
from utils import log
true=True
false=False
null=None

class JSClass(object):
 def __init__(self,name="",value="",id="",root=0,parent=None,type="object",q=None,vars={},hostname="localhost",port=4242):
  self.ref=JSReference(name=name,value=value,id=id,root=root,parent=parent,type=type,q=q,vars=vars,hostname=hostname,port=port,proxy=self)
#getattr/setattr
#if x is ref, then do object.__method__(self,x)

 def __iter__(self):
  return JSIterator(self)

 def __len__(self):
  return self.length

 def __nonzero__(self):
  return 1

 def __hash__(self):
  return self.ref.idh

 def __cmp__(self,other):
  to=type(other)
  if to==JSReference:
   other=getattr(other,"proxy",None)
   to=JSClass
  if to==JSClass:
   oi=other.ref.id
   si=self.ref.id
   if oi==si: return 0
   return -1 if oi<si else 1
  return -1

 def __getitem__(self,x):
  return self.__getattr__(x)

 def __setitem__(self,x,y):
  return self.__setattr__(x,y,1)

 def __repr__(self):
  r=self.ref
  return "js.%s@%s/%s" % (r.name,r.type,r.id,)

 def __dir__(self):
  r=self.ref
  d={"m":"d","a":[r.id],"i":r.id}
  rr=r.root.ref
  rr.send(d)
  ret=rr.recv()
  return ret['a'][0]

 def __getattr__(self,x):
  if x=="ref":
   return object.__getattribute__(self,"ref")
  r=self.ref
  if x in r.vars:
   return r.vars[x]
#  print x
#  log("root",r.root,"self",self,"r.id",r.id,"r.map",r.map.keys(),"parent",r.parent)
  if r.root!=self and r.id not in r.map:
   return r.parent[r.name][x]
  if (r.id,x) in r.rMap:
   return r.rMap[(r.id,x)]
  d={"m":"g","a":[x],"i":r.id}
  rr=r.root.ref
  rr.send(d)
  ret=rr.recv()
  if ret['t'] not in ("undefined","array","object","function"):
#   if r.vars: r.vars['x']=ret['a'][0]
   return ret['a'][0]
  if ret['a'][0]==None: return None
  a=JSClass(name=x,root=r.root,parent=self,id=ret['i'],type=ret['t'],value=ret['a'][0])
  ar=a.ref
  if ar.type=="undefined":
   raise AttributeError("%s has no attribute %s" % (self.ref.name,str(ar.name),))
  if ar.type in ["array","object","function"]:
   r.map[ar.id]=a
   r.rMap[(r.id,ar.name)]=a
   return a

 def __setattr__(self,x,y,override=0):
  if x=="ref":
   return object.__setattr__(self,"ref",y)
  r=self.ref
  if x in r.vars and override==0 and x.startswith("_"):
   r.vars[x]=y
   return y
  name=x if type(x)!=JSClass else x.ref.name
  y=[y] if type(y)!=list else y
  ois=[y.index(i) for i in y if type(i)==JSClass]
  a=[(i.ref.id if type(i)==JSClass else i) for i in y]
  d={"m":"s","a":[name,a],"i":r.id,"oi":ois}
  r.root.ref.send(d)
  ret=r.root.ref.recv()
#~~
  if ret['t'] not in ("undefined","array","object","function"):
   if x in r.vars: r.vars[x]=ret['a'][0]
   return ret['a'][0]
  if ret['t']=="undefined":
   raise AttributeError("%s has no attribute %s" % (self.ref.name,str(x),))
  a=JSClass(name=x,root=r.root,parent=self,id=ret['i'],type=ret['t'],value=ret['a'][0])
  ar=a.ref
  if ar.type in ["array","object","function"]:
   r.map[ar.id]=a
   r.rMap[(r.id,ar.name)]=a
   if x in r.vars: r.vars[x]=a
   return a

 def __call__(self,*a,**kw):
  r=self.ref
  if r.root!=self and r.id not in r.root.ref.map:
   return r.parent[r.name](*a,**kw)
  ois=[a.index(i) for i in a if type(i)==JSClass]
  a=[(i.ref.id if type(i)==JSClass else i) for i in a]
  d={"m":"c","a":[r.name,a],"i":r.parent.ref.id,"oi":ois}
  r.root.ref.send(d)
  ret=r.root.ref.recv()
#~~
  if ret['a'][0]==None:
   return None
  if ret['t'] not in ("undefined","array","object","function"):
   return ret['a'][0]
  a=JSClass(name=r.name+".result",root=r.root,parent=self,id=ret['i'],type=ret['t'],value=ret['a'][0])
  ar=a.ref
  if ar.type=="undefined":
   return None
#raise AttributeError("%s has no attribute %s" % (self.name,str(a.name),))
  if ar.type in ["array","object","function"]:
   r.map[ar.id]=a
   r.rMap[(r.id,ar.name)]=a
   return a

class JSReference(object):
 def __init__(self,name="",value="",id="",root=0,parent=None,type="object",q=None,vars={},hostname="localhost",port=4242,proxy=None):
  self.id=id
  self.idh=self.id.__hash__()
  self.proxy=proxy
  self.root=self.proxy if root==0 else root
# if root!=0 else self
  self.name=name
  self.value=value
  self.type=type
  self.parent=parent
  if root==0:
#self.proxy:
   self.ldata={}
   self.dlog=[]
   self.map={}
   self.rMap={}
   self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
   self.sock.connect((hostname,port))
   self.data=""
   self.eventQ=q
  else:
   rr=self.root.ref
   self.rMap=rr.rMap
   self.map=rr.map
   self.ldata=rr.ldata
#all classes
  if id not in self.ldata: self.ldata[id]={}
  self.vars=self.ldata[id]
  for k,v in vars.items():
   self.vars[k]=v

 def recv(self,delay=None):
  while 1:
   if "\n" in self.data:
    ret,self.data=self.data.split("\n",1)
#    print ret
    self.dlog.append(ret)
    if dbg>=1: dbgl.append("in:"+str(ret))
    if dbg>1: log(dbgl[-1])
#error in deserialization?
    etime1=time.time()
    ret=json.loads(ret)
    if 0:
     encodings="latin-1,utf-8".split(",")
     for enc in encodings:
      try:
       ret=json.loads(ret.decode('latin-1'))
 #      ret=eval(ret)
 #ret.decode(enc).encode('raw_unicode_escape').decode(enc))
 #unicode(ret,enc))
       break
      except UnicodeDecodeError:
       continue
      except UnicodeEncodeError:
       continue
    if dbg>1: log("jsonTime:",time.time()-etime1)
#back from a request we generated? just return this data to the caller, e.g. __getattr__, who will process it.
    if ret['m']=="b":
     return ret
#an error was thrown on the javascript side. throw it here as well as a general Exception type.
    if ret['m']=="t":
     log("event:"+repr(ret))
     raise Exception("js/"+ret['a'][0])
#an event popped up, stick it in the q.
    if ret['m'] in ("w","e","E","ec"):
     if ret['m'] in ("e","E"):
      x=JSClass(name=ret['t'],id=ret['a'][0],parent=None,root=self.root)
      self.map[x.ref.id]=x
      ret['a'][0]=x
     self.eventQ.put(ret)
     continue
#set,get,remove,eXecute,call
    else:
     getattr(self,"js_"+ret['m'])(ret)
#     print "error:",str(ret)
   s=select.select([self.sock],[],[],delay)
   if delay and not s[0]: return
   self.data+=self.sock.recv(16384)

 def send(self,data):
  if type(data)!=str:
   data=json.dumps(data)
  if data[-1]!="\n":
   data+="\n"
  if dbg>=1: dbgl.append("out:"+str(data))
  if dbg>1: log(dbgl[-1])
  self.sock.send(data)

#this would be a method from the js side
 def xjs_s(self,o):
  if o['i'] not in self.map:
   p=self.map['jthis']
  else:
   p=self.map[o['i']]
  name=o['a'][0]
  v=o['a'][1]
  if self.isIdRef(v):
   m=JSClass(id=v[0],parent=p,name=o['a'][0],root=self.root)
  else:
   m=v
  p[name]=m

 def eval(self,s):
  self.root.ref.send({"m":"x","i":self.id,"a":[s]})
  x=self.root.ref.recv()
  for i in xrange(len(x.get("oi",[]))):
   b=x['a'][i]
#   if type(b)==list and len(b)==2 and str(b[0])=='j':
   x['a'][i]=self.map[b]
  return x['a'][0]

 def checkIds(self):
  return 0
  l=[]
  p=self
  while p.parent:
   l.append((p,p.id))
   p=p.parent
  self.root.ref.send({"m":"i","a":[[i[-1] for i in l]]})
  x=self.root.ref.recv()
  ids=[i[0] for i in x['a'][0] if i[1]==0]
  ps=[i[0] for i in l if i[1] in ids]
  [self.root.ref.map.pop(i.id) for i in ps if i.id in self.root.ref.map]
  [p.parent.__getattr__(p.name) for p in ps]
  return len(ps)

 def jsrefresh(self):
  c=self
#  log("clear",c.type,c.parent.ref.type)
  c.vars.clear()
  if c.parent.ref.type=="function":
   log("can't refresh function result, just cleared variables")
   return
  if c.id in self.map: del self.map[c.id]
  k=(c.parent.ref.id,c.name)
  if k in self.rMap:
   self.rMap.pop(k)
   l=[(id,name) for id,name in self.rMap if id==c.id]
   [self.rMap.pop(i) for i in l]
   [self.map.pop(i[0]) for i in l if i[0] in self.map]

class JSIterator(object):
 def __init__(self,cls):
  self.cls=cls
  self.id=0
  self.l=self.cls.length

 def next(self):
  if self.id<self.l:
   self.id+=1
   return self.cls[self.id-1]
  raise StopIteration()

def delMapKey(m,k):
 if type(k)!=str:
  k=k.id
 l=set()
 l.add(k)
 ol=0
 ll=len(l)
 while ll!=ol:
  [l.add(i) for i in m if m[i].parent.id in l]
  ol=ll
  ll=len(l)
 for k in l:
  del m[k]
 return list(l)

def initCliFox(hostname="localhost",port=4242,q=None,js=None,ignoreErrors=0):
 if js==None: js=mzjs
 eventQ=Queue.Queue() if not q else q
 j=JSClass(name="this",value=None,id="jthis",root=0,q=eventQ,hostname=hostname,port=port)
 try:
  w=j.ref.eval(js)
#  print "ret:",w
 except Exception,e:
#  print "e!",e
  if ignoreErrors==1:
   pass
  else:
   print e
#   print 'clifox:error, dialog "%s"' % (j.ref.eval("document.title"),)
   sys.exit(1)
 return j,eventQ

fh=open(utils.path+"/mozCom.js","rb")
mzjs=fh.read()
fh.close()
mzjs=mzjs.strip()
