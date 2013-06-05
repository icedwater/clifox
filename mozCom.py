import os,sys,select,socket,time,Queue,urllib
try:
 try:
  import json
 except:
  import simplejson as json
except:
 print("Either the JSON or simplejson module needs to be installed. Data is passed from Firefox to Python using the JSON format.")
 sys.exit(1)
dbg=0
dbgl=[]
from utils import log
true=True
false=False
null=None

class JSClass(object):
 def __init__(self,name="",value="",id="",root=0,parent=None,type="object",q=None,vars={},hostname="localhost"):
  self.ref=JSReference(name=name,value=value,id=id,root=root,parent=parent,type=type,q=q,vars=vars,hostname=hostname,proxy=self)
#getattr/setattr
#if x is ref, then do object.__method__(self,x)

 def __iter__(self):
  return JSIterator(self)

 def __len__(self):
  return self.length

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
  return self.__setattr(x,y,1)

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
  ids=[i.ref.id for i in y if type(i)==JSClass]
  a=[[i.ref.id,''] if type(i)==JSClass else i for i in y]
  a.insert(0,name)
  d={"m":"s","a":a,"i":r.id}
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
  ids=[i.ref.id for i in a if type(i)==JSClass]
  a=[[i.ref.id,''] if type(i)==JSClass else i for i in a]
  d={"m":"c","a":[r.name,a],"i":r.parent.ref.id,"ids":ids}
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
 def __init__(self,name="",value="",id="",root=0,parent=None,type="object",q=None,vars={},hostname="localhost",proxy=None):
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
   self.sock.connect((hostname,4242))
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
    self.dlog.append(ret)
    if dbg>=1: dbgl.append("in:"+str(ret))
    if dbg>1: log(dbgl[-1])
#error in deserialization?
    etime1=time.time()
    encodings="latin-1,utf-8".split(",")
    for enc in encodings:
     try:
      ret=json.loads(ret)
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
    if ret['m'] in ("w","e","E"):
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
  self.root.ref.send({"m":"i","a":[[i[-1] for i in l]]})
  x=self.root.ref.recv()
  ids=[i[0] for i in x['a'][0] if i[1]==0]
  ps=[i[0] for i in l if i[1] in ids]
  [self.root.ref.map.pop(i.id) for i in ps if i.id in self.root.ref.map]
  [p.parent.__getattr__(p.name) for p in ps]
  return len(ps)

 def jsrefresh(self):
  c=self
  if c.id in self.map: del self.map[c.id]
  k=(c.parent.ref.id,c.name)
  if k in self.rMap:
   self.rMap.pop(k)
   l=[(id,name) for id,name in self.rMap if id==c.id]
   [self.rMap.pop(i) for i in l]

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

def initCliFox(hostname="localhost",q=None,js=None,ignoreErrors=0):
 if js==None: js=mzjs
 eventQ=Queue.Queue() if not q else q
 j=JSClass(name="this",value=None,id="jthis",root=0,q=eventQ,hostname=hostname)
 try:
  j.ref.eval(js)
 except Exception,e:
  if ignoreErrors==1:
   pass
  else:
   print e
   print 'clifox:error, dialog "%s"' % (j.ref.eval("document.title"),)
   sys.exit(1)
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
//if (endings && n){
//l.push([0,n]);
//}
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
gBrowser.tabContainer.addEventListener("TabSelect", this, false);
gBrowser.tabContainer.addEventListener("TabOpen", this, false);
gBrowser.tabContainer.addEventListener("TabClose", this, false);
},

uninit:function() {
gBrowser.browsers.forEach(function (browser){
this._toggleProgressListener(browser.webProgress, false);
}, this);
gBrowser.tabContainer.removeEventListener("TabSelect", this, false);
gBrowser.tabContainer.removeEventListener("TabOpen", this, false);
gBrowser.tabContainer.removeEventListener("TabClose", this, false);
},

handleEvent:function(aEvent) {
if(aEvent.type=="TabSelect")
{
try{
var e=aEvent;
repl.print({"m":"e","t":e.type,"a":[repl.addMap(e)]});
}catch(e){
repl.print({"m":"t","a":[e.toString()]});
};
} else {
let tab = aEvent.target;
let webProgress = gBrowser.getBrowserForTab(tab).webProgress;
this._toggleProgressListener(webProgress, ("TabOpen" == aEvent.type));
}
},

//readd if needed; for now, onStateChange tethered to a page_stop||is_window is doing the trick
xx_onLocationChange: function(aWebProgress, aRequest, aURI)
{
try{
var o={"aWebProgress":aWebProgress,"aRequest":aRequest,"aURI":aURI};
var oid=repl.justAddMap(o);
repl.print({"m":"E","a":[oid],"t":"onAddressChange"});
}catch(e){
repl.print({"m":"t","a":[e.toString()]});
};
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
if ((aStateFlags & Components.interfaces.nsIWebProgressListener.STATE_STOP) && (aStateFlags & Components.interfaces.nsIWebProgressListener.STATE_IS_WINDOW) && (aWebProgress.DOMWindow==aWebProgress.DOMWindow.top))
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
if (aIID.equals(Components.interfaces.nsIAuthPrompt2)||aIID.equals(Components.interfaces.nsIAuthPrompt)||aIID.equals(Components.interfaces.nsIWebProgressListener) || aIID.equals(Components.interfaces.nsISupportsWeakReference) || aIID.equals(Components.interfaces.nsISupports))
{
return this;
};
throw Components.results.NS_NOINTERFACE;
},

prompt: function(dialogTitle, text, passwordRealm, savePassword, defaultText, result)
{
repl.print({"M":"w","a":["authPrompt",dialogTitle, text, passwordRealm, savePassword, defaultText, result]});
return true;
},
promptPassword: function(dialogTitle, text, passwordRealm, savePassword, pwd)
{
repl.print({"M":"w","a":["authPromptPassword",dialogTitle, text, passwordRealm, savePassword, pwd]});
return true;
},
promptUsernameAndPassword: function(dialogTitle, text, passwordRealm, savePassword, user, pwd)
{
repl.print({"M":"w","a":["authPromptUsernameAndPassword",dialogTitle, text, passwordRealm, savePassword, user, pwd]});
return true;
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

repl.windowGuiKiller=
{
obs:null,
observe : function(aSubject, aTopic, aData)
{
repl.print({"m":"w","a":["observer",aTopic]});
if(aTopic=="content-document-global-created")
{
var wo;
aSubject.QueryInterface(Ci.nsIDOMWindow);
wo=aSubject.wrappedJSObject;
wo.alert=function(){};
wo.confirm=function(){};
wo.prompt=function(){};
}
if(aTopic=="dom-window-destroyed")
//"content-document-global-created")
{
//this.kill();
aSubject.QueryInterface(Ci.nsIDOMWindow);
wo=aSubject.wrappedJSObject;
delete wo.alert;
delete wo.confirm;
delete wo.prompt;
}
},
kill: function()
{
this.obs.removeObserver(this,"content-document-global-created");
this.obs.removeObserver(this,"dom-window-destroyed");
}
}

var obs;
obs=Components.classes["@mozilla.org/observer-service;1"].getService(Components.interfaces.nsIObserverService);
repl.windowGuiKiller.obs=obs;
obs.addObserver(repl.windowGuiKiller, "content-document-global-created", false);
obs.addObserver(repl.windowGuiKiller, "dom-window-destroyed", false);
//content-document-global-created", false);
repl.killers.push([repl.windowGuiKiller,repl.windowGuiKiller.kill]);

repl.getDocJson=function(root,end)
{
grabVars={
"A":["textContent","href"],
"SELECT":["textContent"],
"INPUT":["type","value","checked","lable","name"],
"OPTION":["textContent"],
"IMG":["alt","src"]
}
function getNode(n,addToMap,endNode)
{
var a,at,al,j,i;
a=[];
a.push(endNode?1:0);
a.push(addToMap(n));
if (endNode)
{
return a;
};
a.push(n.nodeName);
a.push(n.nodeValue);
a.push(n.nodeType);
a.push(repl.inMap(n.parentNode));
if (n.nodeName in grabVars)
{
var gv=grabVars[n.nodeName];
var gvl=gv.length;
for (var i=0;i<gvl;i++)
{
a.push(gv[i]);
a.push(n[gv[i]]);
}
} else {
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
}
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
var z;
if (t===root)
{
z=getNode(t,repl.addMap,0);
} else {
z=getNode(t,func,0);
}
zl=z.length;
if(1==0)
{
for (var j=2;j<zl;j++)
{
if (typeof(z[j])=='string')
{
z[j]=encodeURIComponent(z[j]);
}
}
}
l.push(z);
}
};
//l.push(repl.time()-atime);
repl.print({"m":"w","a":["docSerializationTime",repl.time()-atime]});
return l;
};
"""
mzjs=mzjs.strip()
