import os,sys,select,socket,time,Queue,chardet
import simplejson as json
dbg=1
dbgl=[]
true=True
false=False
null=None

rootVars="dlog,data,eventQ,sock,send,recv,map,rMap".split(",")
localVars="vars,eventQ,eval,rMap,checkIds,id,name,value,type,root,parent,map,sock,data,send,recv".split(",")
localVars=[i for i in localVars if i not in rootVars]

class JSClass(object):
 root=None
 id=None
 vars={}
 def __init__(self,name="",value="",id="",root=0,parent=None,type="object",q=None,vars={},hostname="localhost"):
  self.vars={}
  [self.vars.__setitem__(k,v) for k,v in vars.items()]
  self.root=root if root!=0 else self
  if self.root==self:
   self.dlog=[]
   self.map={}
   self.rMap={}
   self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
   self.sock.connect((hostname,4242))
   self.data=""
   self.eventQ=q
  self.name=name
  self.id=id
  self.parent=parent
  self.type=type
  self.value=value

 def recv(self,delay=None):
  if self.root!=self:
   return self.root.recv()
  else:
   while 1:
    if "\n" in self.data:
     ret,self.data=self.data.split("\n",1)
     self.dlog.append(ret)
     if dbg>=1: dbgl.append("in:"+str(ret))
     if dbg>1: print dbgl[-1]
#error in deserialization?
     etime1=time.time()
     encodings="latin-1,utf-8".split(",")
     for enc in encodings:
      try:
       ret=eval(unicode(ret,enc))
       break
      except UnicodeEncodeError:
       continue
     if dbg>1: print "jsonTime:",time.time()-etime1
#back from a request we generated? just return this data to the caller, e.g. __getattr__, who will process it.
     if ret['m']=="b":
      return ret
#an error was thrown on the javascript side. throw it here as well as a general Exception type.
     if ret['m']=="t":
      raise Exception(ret['a'][0])
#an event popped up, stick it in the q.
     if ret['m'] in ("w","e","E"):
      if ret['m'] in ("e","E"):
       x=JSClass(name=ret['t'],id=ret['a'][0],parent=None,root=self.root)
       self.root.map[x.id]=x
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
  if dbg>1: print dbgl[-1]
  self.sock.send(data)

 def xjs_s(self,o):
  if o['i'] not in self.map:
   p=self.map['jthis']
  else:
   p=self.map[o['i']]
  name=o['a'][0]
  v=o['a'][1]
  if self.isIdRef(v):
   m=JSObject(id=v[0],parent=p,name=o['a'][0],root=self.root)
  else:
   m=v
  p[name]=m

 def eval(self,s):
  self.root.send({"m":"x","i":self.id,"a":[s]})
  x=self.root.recv()
  for i in xrange(len(x['a'])):
   b=x['a'][i]
   if type(b)==list and len(b)==2 and str(b[0])=='j':
    x['a'][i]=self.map[b[0]]
  return x['a'][0]

 def checkIds(self):
  return 0
  l=[]
  p=self
  while p.parent:
   l.append((p,p.id))
   p=p.parent
  self.root.send({"m":"i","a":[[i[-1] for i in l]]})
  x=self.root.recv()
  ids=[i[0] for i in x['a'][0] if i[1]==0]
  ps=[i[0] for i in l if i[1] in ids]
  [self.root.map.pop(i.id) for i in ps if i.id in self.root.map]
  [p.parent.__getattr__(p.name) for p in ps]
  return len(ps)

 def __iter__(self):
  return JSIterator(self)

 def __len__(self):
  return self.length

 def __hash__(self):
  return self.id.__hash__()

 def __cmp__(self,other):
  oi=getattr(other,"id",None)
  if oi==self.id: return 0
  return -1 if oi<self.id else 1

 def __getitem__(self,x):
  return self.__getattr__(x)

 def __setitem__(self,x,y):
  return self.__setattr(x,y)

 def __repr__(self):
  return "js.%s@%s/%s" % (self.name,self.type,self.id,)

 def __dir__(self):
  d={"m":"d","a":[self.id],"i":self.id}
  self.root.send(d)
  ret=self.root.recv()
  return ret['a'][0]

 def __getattr__(self,x):
  if x in rootVars and object.__getattribute__(self,"root")!=self:
   return object.__getattribute__(object.__getattribute__(self,"root"),x)
  elif x in object.__getattribute__(self,"vars"):
   return object.__getattribute__(self,"vars")[x]
  elif x in localVars:
   return object.__getattribute__(self,x)
  else:
   pass #if self.root!=self: object.__getattribute__(self,"checkIds")()
  if self.root!=self and self.id not in self.root.map:
   return self.parent[self.name][x]
  if (self.id,x) in self.root.rMap:
   return self.root.rMap[(self.id,x)]
  d={"m":"g","a":[x],"i":self.id}
  self.root.send(d)
  ret=self.root.recv()
  a=JSClass(name=x,root=self.root,parent=self,id=ret['i'],type=ret['t'],value=ret['a'][0])
  if a.type=="undefined":
   raise AttributeError("%s has no attribute %s" % (self.name,str(a.name),))
  if a.type in ["array","object","function"]:
   self.root.map[a.id]=a
#might should change from self.id to a.parent.id (points to self.id)
   self.root.rMap[(self.id,a.name)]=a
   return a
  return a.value

 def __setattr__(self,x,y):
  if x in rootVars and object.__getattribute__(self,"root")!=self:
   return object.__setattr__(object.__getattribute__(self,"root"),x,y)
  elif x in rootVars:
   return object.__setattr__(self,x,y)
  elif x in object.__getattribute__(self,"vars"):
   object.__getattribute__(self,"vars")[x]=y
  elif x in localVars:
   return object.__setattr__(self,x,y)
  else:
   pass #if self.root!=self: object.__getattribute__(self,"checkIds")()
  if self.root!=self and self.id not in self.root.map:
   return self.parent[self.name][x]
  name=x if type(x)!=JSClass else x.name
  y=[y] if type(y)!=list else y
  ids=[i.id for i in y if type(i)==JSClass]
  a=[[i.id,''] if type(i)==JSClass else i for i in y]
  a.insert(0,name)
  d={"m":"s","a":a,"i":self.id}
  self.root.send(d)
  ret=self.recv()
  a=JSClass(name=x,root=self.root,parent=self,id=ret['i'],type=ret['t'],value=ret['a'][0])
  if a.type in ("object","array","function"):
   self.root.map[a.id]=a
   self.root.rMap[(a.parent.id,a.name)]=a
   return a
  return a.value

 def __call__(self,*a,**kw):
  if self.root!=self and self.id not in self.root.map:
   return self.parent[self.name](*a,**kw)
  else:
   pass #if self.root!=self: object.__getattribute__(self,"checkIds")()
  ids=[i.id for i in a if type(i)==JSClass]
  a=[[i.id,''] if type(i)==JSClass else i for i in a]
  d={"m":"c","a":[self.name,a],"i":self.parent.id,"ids":ids}
  self.root.send(d)
  ret=self.root.recv()
  a=JSClass(name=self.name,root=self.root,parent=self,id=ret['i'],type=ret['t'],value=ret['a'][0])
  if a.value==None:
   return None
  if a.type=="undefined":
   return None
  if a.type in ["array","object","function"]:
   self.root.map[a.id]=a
   self.root.rMap[(a.parent.id,a.name)]=a
   return a
  return a.value

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

def initCliFox(hostname="localhost",q=None,js=None):
 if js==None: js=mzjs
 eventQ=Queue.Queue() if not q else q
 j=JSClass(name="this",value=None,id="jthis",root=0,q=eventQ,hostname=hostname)
 j.eval(js)
 return j,eventQ

mzjs="""
repl.parentNodeNames=function(n)
{
var l=[];
var p;
p=n.parentNode;
while(p)
{
l.push(p.nodeName);
p=p.parentNode;
}
return l;
};
Array.prototype.indexOf=(function(obj){var idx=this.length;do{if(this[i]==obj){return i;};idx--;} while(idx>=0);return -1;});
repl.getDomList=function(root,endings)
{
var n,l,i;
l=[];
n=root;
i=0;
while (n && (i==0 || n!=root))
{
i+=1;
l.push(n);
if (n.hasChildNodes())
{
n=n.firstChild;
continue;
}
if (n.nextSibling)
{
n=n.nextSibling;
continue;
}
while (n && !n.nextSibling)
{
n=n.parentNode;
if (endings){
l.push([0,n]);
}
}
if (!n)
{
break;
}
n=n.nextSibling;
}
return l;
};
repl.time=function(){return new Date().getTime()/1000;};
repl.closeAll=function(){for(var i=this.gBrowser.tabs.length;i>0;i--){this.gBrowser.tabs[i].linkedBrowser.contentWindow.close();};};
repl.lsbrs=function(){var j,i,x;i=0;j=[];for(i=0;i<this.gBrowser.tabs.length;i++){x=this.gBrowser.tabs[i].linkedBrowser.contentDocument.location.href;j.push(x);};return j.toString();};
repl.ls=function(obj){var z,i;z=[];for(i in obj){z.push(i);};return z;};
repl.genid=function(){this._id+=1;return "j"+this._id.toString();};
repl.findAllInMap=function(parent){var i,ret;ret=[];for(i=repl.map.length-1;i>=0;i--){var oid,x;oid=repl.map[i].id;x=repl.map[i];while (x.parent){if (x.id==parent){ret.push(oid);break;}}}return ret;};
repl.inMap=function(obj)
{
var where,i;
where=repl.mapObjList.indexOf(obj);
if(where>-1)
{
return repl.mapIdList[where];
};
return null;
};
repl.addMap=function(obj,opts)
{
//repl.print({"m":"w","a":repl.inMap.toString()});
var x;
x=repl.inMap(obj);
if(x!=null)
{
return x;
};
return repl.justAddMap(obj,opts);
};
repl.justAddMap=function(obj,opts)
{
var i;
i=repl.genid();
opts=opts?opts:{};
parent=opts.parent?opts.parent:null;
name=opts.name?opts.name:"";
repl.map[i]={"parent":parent,"id":i,"value":obj,"type":typeof(obj),"name":name};
repl.mapIdList.push(i);
repl.mapObjList.push(obj);
return i;
};
repl._loadHandler = function(e) {try{if(e.target.nodeName=="#document"&&e.target.location.href!="about:blank"){};repl.print({"m":"e","t":e.type,"a":[repl.addMap(e)]});}catch(e){repl.print({"m":"w","a":["error:"+e.toString()]});};};
//repl._unloadHandler=function(e){if(e.target.nodeName=="#document"){e.target.defaultView.removeEventListener("load",this._loadHandler,true);};};
//repl._loadHandler({});
gBrowser.addEventListener("load", repl._loadHandler, true);
repl.events.push([gBrowser,"load",repl._loadHandler,true]);
//gBrowser.addEventListener("unload", repl._unloadHandler, true);
repl.web_progress_listener={
init:function() {
//repl.print({"m":"w","a":["R.WPL init"]});
gBrowser.browsers.forEach(function (browser) {
this._toggleProgressListener(browser.webProgress, true);
}, this);
gBrowser.tabContainer.addEventListener("TabOpen", this, false);
gBrowser.tabContainer.addEventListener("TabClose", this, false);
},

uninit:function() {
gBrowser.browsers.forEach(function (browser){
this._toggleProgressListener(browser.webProgress, false);
}, this);
gBrowser.tabContainer.removeEventListener("TabOpen", this, false);
gBrowser.tabContainer.removeEventListener("TabClose", this, false);
},

handleEvent:function(aEvent) {
let tab = aEvent.target;
let webProgress = gBrowser.getBrowserForTab(tab).webProgress;
this._toggleProgressListener(webProgress, ("TabOpen" == aEvent.type));
},

onStatusChange:function(aWebProgress,aRequest,aStatus,aMessage)
{
try{
var o={"aWebProgress":aWebProgress,"aRequest":aRequest,"aMessage":aMessage,"aStatus":aStatus};
var oid=repl.justAddMap(o);
repl.print({"m":"E","a":[oid],"t":"onStatusChange"});
}catch(e){
repl.print({"m":"t","a":[e.toString()]});
};
},

onStateChange:function(aWebProgress,aRequest,aStateFlags,aStatus)
{
//repl.print({"m":"w","a":["onStatusChange"]});
if ((aStateFlags & Components.interfaces.nsIWebProgressListener.STATE_START) && (aStateFlags & Components.interfaces.nsIWebProgressListener.STATE_IS_DOCUMENT) && (aWebProgress.DOMWindow==aWebProgress.DOMWindow.top))
{
//repl.print({"m":"w","a":["onStatusChange2"]});
try{
var o={"aWebProgress":aWebProgress,"aRequest":aRequest,"aStateFlags":aStateFlags,"aStatus":aStatus};
var oid=repl.justAddMap(o);
repl.print({"m":"E","a":[oid],"t":"onStateChange"});
}catch(e){
repl.print({"m":"t","a":[e.toString()]});
};
}
},

QueryInterface: function(aIID)
{
if (aIID.equals(Components.interfaces.nsIWebProgressListener) || aIID.equals(Components.interfaces.nsISupportsWeakReference) || aIID.equals(Components.interfaces.nsISupports))
{
return this;
};
throw Components.results.NS_NOINTERFACE;
},

_toggleProgressListener:function(aWebProgress, aIsAdd)
{
if (aIsAdd)
{
aWebProgress.addProgressListener(this, aWebProgress.NOTIFY_ALL);
} else {
aWebProgress.removeProgressListener(this);
}
},
};
repl.web_progress_listener.init();
repl.killers.push([repl.web_progress_listener,repl.web_progress_listener.uninit]);
repl.getDocJson=function(root,end)
{
function getNode(n,addToMap,endNode)
{
var a,at,al,j,i;
a=[];
a.push(endNode?1:0);
a.push(addToMap(n));
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
if(repl.inMap(root.firstChild)!=null && repl.inMap(root.lastChild)!=null)
{
func=repl.inMap;
} else {
func=repl.justAddMap;
};
//func=repl.justAddMap;
var atime,w,l,cur,ll;
l=[];
atime=repl.time();
w=this.getDomList(root,end);
ll=w.length;
for(var i=0;i<ll;i++)
{
var t=w[i];
if (t[0]===0 && t[1])
{
l.push(getNode(t[1],repl.inMap,1));
} else {
if (t===root)
{
l.push(getNode(t,repl.addMap,0));
} else {
l.push(getNode(t,func,0));
}
}
};
//l.push(repl.time()-atime);
repl.print({"m":"w","a":["docSerializationTime",repl.time()-atime]});
return l;
};
"""
mzjs=mzjs.strip()
