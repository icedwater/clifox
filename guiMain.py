import os,curses,mozCom,utils,re,unidecode
from utils import log,generate_error_report
import configParser
config=configParser.config
from guiObjects import *
import guiTree
"""holds classes for handling page rendering and element navigation"""
class forms(object):
 form_screens=[]

 def save(self):
  pos=self.screen.getyx()
  log("save:pos",pos)
  screenFN=os.tempnam(None,"pywb.scrnfrm.")
  fh=open(screenFN,"wb")
  self.screen.putwin(fh)
  fh.close()
  self.form_screens.append((pos,screenFN))

 def restore(self):
  self.screen.clear()
  pos,fn=self.form_screens.pop(-1)
  fh=open(fn,"rb")
  self.screen=curses.getwin(fh)
  self.screen.move(pos[0],pos[1])
  log("restore:pos",pos)
  fh.close()
  os.remove(fn)

 def gFileBrowser(self,**kw):
  kw['screen']=self.screen
  kw['maxy']=self.maxy
  kw['maxx']=self.maxx
  ret=None
  try:
   self.save()
  except Exception,e:
   generate_error_report()
  try:
   fb=FileBrowser(**kw)
   ret=fb.keyHandler()
  except Exception, e:
   generate_error_report()
  try:
   self.restore()
  except Exception,e :
   generate_error_report()
   log("gDirBrowser:error restoring window")
  return ret

 def gListbox(self,**kw):
  log("gListbox:called:",str(kw))
  kw['screen']=self.screen
  kw['maxy']=self.maxy
  kw['maxx']=self.maxx
  ret=None
  try:
   self.save()
  except Exception,e:
   generate_error_report()
   log("gListbox:error saving")
  try:
   l=Listbox(**kw)
   ret=l.loop()
  except Exception, e:
   generate_error_report()
  try:
   self.restore()
  except Exception,e :
   generate_error_report()
   log("gListbox:error restoring window")
  return ret

 def gEditbox(self,**kw):
  kw['screen']=self.screen
  ret=None
  try:
   self.save()
  except:
   generate_error_report()
  try:
   e=Editbox(**kw)
   ret=e.loop()
  except Exception,e:
   ret=generate_error_report()
  try:
   self.restore()
  except:
   pass
  return ret

 def gTree(self,params,**kw):
  self.save()
  if "treeview" in kw:
   tvType=kw.pop("treeview")
   g=getattr(guiTree,tvType)(params,**kw)
  else:
   g=guiTree.nodeTreeview(params)
  x=g(self.screen)
  self.restore()
  return x

 def gCheckbox(self,**kw):
  kw['screen']=self.screen
  kw['maxy']=self.maxy
  kw['maxx']=self.maxx
  self.save()
  ret=None
  try:
   c=Checkbox(**kw)
   ret=c.loop()
  except Exception,e:
   generate_error_report()
  self.restore()
  return ret

class gui(forms):
 """Holds methods for drawing and painting a screen
"""
 @property
 def x(self):
  return self.curPos[1]
 @x.setter
 def x(self,v):
  self.curPos[1]=v
 @property
 def y(self):
  return self.curPos[0]
 @y.setter
 def y(self,v):
  self.curPos[0]=v

 formElements=set("TEXTAREA,BUTTON,INPUT,SELECT,OPTION".split(","))
 newLineMakerElements=set("BR,P".split(","))
 newLineElements=set("FORM,TITLE,HR,LI,TD,H1,H2,H3,H4,H5,H6,BR,P,A,IMG,SOUND,BGSOUND".split(","))
 [newLineElements.add(i) for i in formElements if i!="OPTION"]
 ignoreElements=set("OPTION,NOSCRIPT,SCRIPT,STYLE".split(","))

 def getNextNonChildNode(self,n,inList=None):
  l=inList
  if (0,n) in l:
   return l.index((0,n))
  i=l.index(n)
  snum=n.num
  while i+1<len(l):
   i+=1
   if type(l[i])==tuple:
    continue
   if l[i].num<=snum:
    return i
  return None

 ws=[chr(i) for i in xrange(1,255)]
#string.whitespace+string.printable
 def getElementText(self,n):
  t=n.nodeName
  t=t if t else 'unnamedNode'
#  if self.ignoreElements.intersection(self.parentNodeNames(n)): return 0,None
  if t=="#text":
   return 0,n.nodeValue.replace("\n"," ").replace("\r"," ").replace("  "," ")
  elif t=="HR":
   return 0,"-"*self.maxy
  elif t=="LI":
   return 1,"* "
  elif t=="IMG":
   if n.alt:
    return 0,"[img] "+n.alt
   elif n.src and n.src.split(":",1)[0]!="data":
    return 0,"[img] "+n.src
#   elif n.hasChildNodes() and n.nodeValue!="":
#    return "[img] "
   else:
    return 0,"[img] unknown"
  elif t=="FRAME" or t=="IFRAME":
   return 0,"[frame] "+n.src
  elif t=="A":
   x=self.getElementsByTagName(n,"img")
   if x:
    x=x[0]
    x._flags_skip=1
    _,t=self.getElementText(x)
    if t.startswith("[img] "): t=t[6:]
    t="{["+t+"]}"
    return 0,t
   elif n.textContent!="":
#[i for i in self.nodes_flat if i.parentNode==n] and n.textContent!="":
    return 1,"{} "
   elif n.name:
    return 1,''
   elif n.href:
    return 1,"{%s}" % (n.href,)
   else:
    return 1,"{} "
  elif t in self.formElements:
   if t=="INPUT" and n.type and n.type.lower()=="hidden":
    return 1,None
   if str(n.type).lower()=="checkbox":
    v="x" if n.checked else " "
   elif n.value:
    v=n.value
    if str(n.type).lower()=="password":
     v="*"*len(v)
   else:
    v=""
   if n.title:
    return 0,"[%s] %s" % (n.title,v,)
   elif n.type and n.type.lower() in ("submit","image"):
    return 0,"[submit] %s" % (v,)
   elif n.lable:
    return 0,"[%s] %s" % (n.lable,v,)
   elif n.name:
    return 0,"[%s] %s" % (n.name,v,)
   else:
    return 0,"[unknown form element] %s" % (str(v),)
  elif t[0]!="#":
   return 0,n.nodeValue
  else:
   return 0,None

 def getElementsByTagName(self,root,tag=""):
  tag=tag.upper()
  idx=self.nodes_flat.index(root)
  end=self.getNextNonChildNode(root,self.nodes_flat)
  l=self.nodes_flat[idx:end]
  return [i for i in l if i.tagName==tag]

 def parentNodes(self,p):
  ret=[]
  while p.parentNode!=None:
   p=p.parentNode
   ret.append(p)
  return ret

 def parentNodeNames(self,e):
  e=e.parentNode
  l=[]
  while e!=None:
   try:
    l.append(e.nodeName)
   except:
    break
   e=e.parentNode
  return l

 def getLineText(self,y=None,x=0,length=None):
  y=self.screenPos if y==None else y
  x=self.screenPosX if x==None else x
  length=self.maxy if length==None else length
  return self.screen.instr(y,x,length)

 def getLineNumber(self,absoluteY=0):
  ret=(absoluteY+1)-((self.maxy+1)*self.getScreenNumber(absoluteY)+1)
  log("getLineNumber:absoluteY=%d,line=%d" % (absoluteY,ret,))
  return ret
  l=0
  counter=absoluteY
  subtract=0
  while counter>self.maxy:
   counter-=self.maxy
   subtract+=1
  counter-=subtract
  log("getLineNumber:y=%d,return=%d" % (absoluteY,counter,))
  return counter

 def getScreenNumber(self,absoluteY=0):
  l=-1
  counter=absoluteY
  while counter>=0:
   counter-=(self.maxy+1)
   l+=1
  log("getScreenNumber:y=%d,return=%d" % (absoluteY,l,))
  return l

#returns position in single line-based, zero-based index of a screen, given a screenNumber (current by default) and a lineNumber (0 by default)
#e.g. 2 screens, screen 0 (first screen) has 4 lines, 0-3 inclusive. screen 2, or sn=1, has 4 lines, 0-3 inclusive. line 2 on that second screen is 0,0 0,1 0,2 0,3 1,0 1,1 or 5 (6, because of the zero base)
 def getScreenAbsolutePosition(self,screenNum=None,y=0):
  while y>self.maxy+1:
   y-=(self.maxy+1)
  if screenNum==None: screenNum=self.screenNum
  pos=0
  sn=0
  while sn<screenNum:
   pos+=self.maxy+1
   sn+=1
  pos+=y
  log("getScreenAbsolutePosition:screenNum=%s,y=%s,pos=%s" % (str(screenNum),str(y),str(pos),))
  return pos

  sn=-1
  ln=-1
  lines=self.maxy
  i,j,l=0,0,0
  while i<screenNum:
   l+=self.maxy
   i+=1
  if screenNum>0:
# and y==0:
   l+=screenNum
  j=0
  while j<y:
   l+=1
   j+=1
  return l

 def findNextPositionLocation(self,l):
  for i in l:
   a=self._display.get(i,[])
   if a:
    return a[0][1:3]

 def previousNonIgnoredElement(self,nodes,idx):
  while idx>0 and self.ignoreElements.intersection(self.parentNodeNames(nodes[idx])):
   idx-=1
  return nodes[idx]

 def textOnSameLine(self,nodes,node=None):
  """determine if any actual text is on the current line, excluding text used for formatting or identification"""
#locate node in master list
  x=nodes.index(node) if node!=None else self.nidx-1
  text=0
  while x>0:
#navigate backward through the list
   n=nodes[x]
#skip tuples, because they will not ever have true text
   if type(n)==tuple: x-=1; continue
   d=self._display[n]
#get list of all text strings from this element on the line we are looking for
   l=[j for j in d if j[1]==self.y]
#if nothing in l, then we've moved backward to before our looked-for line, without finding text, so return 0
   if not l: return 0
#get lsit of all non-formatting text
   t=[j for j in l if j[0]==0]
#if nothing in this list, we move to the previous node
   if not t: x-=1; continue
#we've found text by elimination of all non-text and non-looked-for lines
   return 1
  return 0
#   if "".join([i[3] for i in t]).strip(): text=1; return text
#   x-=1
#  return text
# len([j for j in nodes[:self.nidx] if type(j)!=tuple and self.y in [k[0] for k in j._display] and j._nodeText]):
  
 def getAcc(self,root):
  ret=[]
  lv=0
  self.js.tmp=root
  res=self.js.ref.eval('repl.accView(tmp)')[0]
  log("res:",res)
  ii=-1
  jm=self.js.ref.map
  jr=self.js.ref.rMap
  for i in res:
   ii+=1
   vars={"text":i[-1],"num":i[1],"role":i[2],"states":i[3]}
   id=i[0]
   jc=mozCom.JSClass(root=self.js,name=str(ii),id=id,vars=vars)
   jm[id]=jc
   jr[(id,ii)]=jc
   ret.append(jc)
  return ret

 def iterNodes(self,root):
  self.js.tmp=root
  lc=[]
  res=self.js.ref.eval("repl.getDocJson(tmp)")[0]
  ii=-1
  jm=self.js.ref.map
  jr=self.js.ref.rMap
  for o in res:
   ii+=1
   if o[0] in jm:
    t=jm[o[0]]
    t.ref.vars.update(zip(["num","nodeName","nodeValue","nodeType","parentNode"],[o[i] for i in range(1,6)]))
    if t.ref.vars['parentNode']: t.ref.vars['parentNode']=jm[t.ref.vars['parentNode']]
    t.ref.vars.update([(o[i],o[i+1]) for i in range(6,len(o),2)])
    lc.append(t)
   else:
    id,num,nn,v,t,pn=o[:6]
    nn=nn.upper() if nn[0]!="#" else nn
    v={"num":num,"nodeName":nn,"tagName":nn,"nodeValue":v,"nodeTypeInvalid":t,"parentNode":jm.get(pn,None),"_flags_skip":0}
    v.update([(o[j],o[j+1]) for j in xrange(6,len(o),2) if o[j] not in v])
    jc=mozCom.JSClass(root=self.js,name=str(ii),id=id,vars=v)
    jm[id]=jc
    jr[(id,ii)]=jc
    lc.append(jc)
  return lc

 def makeClosings(self,nodes):
  l=[]
  open=[]
  idx=-1
  for i in nodes:
   idx+=1
   if idx and i.num<=nodes[idx-1].num:
    rng=(nodes[idx-1].num-i.num)+1
    clos=[open.pop(-1) for j in xrange(rng)]
    [l.append((0,j)) for j in clos]
   open.append(i)
   l.append(i)
  log("remainderOpen:",open)
  [l.append((0,j)) for j in open[::-1]]
  return l

 def _makeClosings(self,nodes):
#  log("makeclosings")
  openNodes=[]
  ol={}
  nid=-1
  lenNodes=len(nodes)
  while nid+1<lenNodes:
   lenNodes=len(nodes)
   nid+=1
   n=nodes[nid]
   if type(n)!=tuple and n not in ol:
    openNodes.append((n,self.parentNodes(n)))
    ol[n]=1
    if len(openNodes)>1:
     last=openNodes[-2]
     lastOpeningParents=last[1]
     currentOpeningParents=openNodes[-1][1]
 #    if i in lastOpeningParents:
     count=len(lastOpeningParents)-len(currentOpeningParents)
#     log("count:",count,"lastParents",[i.nodeName for i in lastOpeningParents],"currentParents",[i.nodeName for i in currentOpeningParents],"in",n.nodeName,"last",last[0].nodeName)
     if count>=0 and n.parentNode in lastOpeningParents and not (count==0 and last[0].nodeName==openNodes[-1][0].nodeName=='#text'):
      closings=lastOpeningParents[:count]
#      if count==0: 
      closings.insert(0,last[0])
      closings=[i for i in closings if i.nodeName!="#text"]
#      log("closings",[i.nodeName for i in closings])
      if closings:
       [nodes.insert(nid,(0,i)) for i in closings[::-1]]
       nid-=1
      continue
  _c=nodes[nid]
  c=_c if type(_c)!=tuple else _c[1]
  parents=self.parentNodes(c)
#if not tuple
  if c==_c: parents.insert(0,c)
  [nodes.append((0,i)) for i in parents if i.nodeName!="#text"]
  return nodes

 def paintScreen(self,dirty=None):
#  log("paintScreen")
  self.nidx=-1
  w=self.maxx
  self.y,self.x=0,0
#  log("nodes from doc:"+str(self.dom.document))
  self.dom.document.ref.vars['_flags_skip']=0
  for k in "nodeName,tagName,nodeValue".split(","):
   try:
    self.dom.document.ref.vars[k]=self.dom.document[k]
   except:
    self.dom.document.ref.vars[k]=None
  self.dom.document.ref.vars['parentNode']=None
  try:
   nodes=self.iterNodes(self.dom.document)
   nodes=self.makeClosings(nodes)
   self.nodes=nodes
   self.nodes_flat=[i for i in nodes if type(i)!=tuple]
  except:
   generate_error_report()
#  log("got all nodes,",len(nodes),repr([i for i in nodes]))
  last=None
  self.newLineCount=0
  self._display={}
  self.ys={}
  if dirty!=None:
   nodes=nodes[nodes.index(dirty):]
   self.y,self.x=self.findNextPositionLocation(nodes)
   last=nodes[0].previousSibling
#if a node in nodes is an end marker, it will be a tuple. otherwise, it will be a node
#set all lists for each node in nodes to an empty list, as we are basically clearing all previous positions
  [self._display.__setitem__(j,[]) for j in self.nodes_flat]
  lenNodes=len(nodes)
  nid=-1
  while nid+1<lenNodes:
   self.nidx+=1
   nid+=1
   n=nodes[nid]
#we're at the end of an element
   if type(n)==tuple:
    n,t=n[1],n[1].nodeName if n[1].nodeName else None
    if t in self.newLineElements and t !="A":
#if we need to separate the end of this element from the next, e.g. this is the end of an h1 element, and we have to put a new line, then do so
#skip links, because we can put text after them, and keep from using up excessive vertical pages
     self.y+=1; self.x=0
     currentI=self.nidx
     while currentI+1<lenNodes and type(nodes[currentI])==tuple:
#while we're still in the nodes list, and we are encountering end elements, e.g. </h1></div>, etc
      currentI+=1
#~~
      if type(nodes[currentI])!=tuple:
#if the element after the one we are currently on is not an end element, then add an index to it's _display property, and exit this loop (while loop will break because of finding this node)
       self._display[nodes[currentI]].append((1,self.y,self.x,""))
    continue
#one-time skip of an element
   if n._flags_skip:
    n._flags_skip=0; continue
#maybe make the below an else statement with the tuple check above?
   self._display[n].append((1,self.y,self.x,''))
   i=n.nodeName
#skip script,style,noscript, etc
   if i in self.ignoreElements:
    tnid=self.getNextNonChildNode(n,nodes)
    if tnid!=None:
     nid=tnid-1
     self.nidx=nid
     continue
#if this starting element requires a new line
#it's not a new line type itself, e.g. paragraph or line break
#it's indeed a start element
#basically, if there are nodes with text on our same line, and as above, we're on an element needing a new line, then we supply one. This means that we won't put a new line in unless there is already text on this line, so we won't be inserting multiple blank lines for ending elements and starting new ones.
#for all nodes whose starting position is on the same line as the current node, before this node in the nodes list, and whose text is not blank or whitespace
#   log("elem:",i,type(n),self.textOnSameLine(nodes))
#i not in ("BR","P") and \
   if i in self.newLineElements and \
type(n)!=tuple and \
self.textOnSameLine(nodes):
    self.y+=1; self.x=0; self._display[n].append((1,self.y,self.x,''))
#add second blank line for paragraphs
    if i=="P": self.y+=1; self.x=0; self._display[n].append((1,self.y,self.x,''))
   formatOnly,text=self.getElementText(n)
   if text==None: text=''
   if type(text)==int: text=str(text)
   text=unidecode.unidecode(text)
   text=re.sub(r"^\s+|\s+$",' ',text)
#if text.strip():
   if text.lstrip():
    self.newLineCount=0
#    text=text.replace("\t"," ").replace("\r"," ").replace("\n"," ").replace("  "," ")
    if self.nidx>0:
     lastNode=nodes[self.nidx-1]
#     if type(lastNode)!=tuple and lastNode.nodeName not in ("BR","P"):
#      text=text.lstrip()
    lenT=len(text)
    if (self.x+lenT)<w:
     self._display[n].append((formatOnly,self.y,self.x,text))
     if text: self.ys[self.y]=1
     self.x+=lenT
    elif self.x+lenT>w and lenT<w:
     self.y,self.x=self.y+1,lenT
     self._display[n].append((formatOnly,self.y,0,text))
     if text: self.ys[self.y]=1
    else:
     for t in self.wrapToFit(text, self.maxx, self.x):
      self._display[n].append((formatOnly,self.y,self.x,t))
      if t: self.ys[self.y]=1
      oldY,oldX=self.y,self.x+lenT
      self.y,self.x=self.y+1,0
     if oldX<w: self.y,self.x=oldY,oldX
  self.numLines=self.y
  self.xn=nodes
  return
  try:
   fh=utils.open("logs/screenTextRefresh.txt","wb")
   fh.write(str(self.dom.document))
   fh.close()
  except:
   generate_error_report()

 def writeScreenCoordsToFile(self):
  return
  fh=utils.open("logs/screen.log","wb")
  fh.write(str(self._display))
#+"\n$$$\n")
#   for j in i._display:
#    fh.write(str(j)+"\n")
  fh.write("\n")
  fh.close()

 def gotoBookmark(self):
  url=self.showBookmarks()
  if url==None:
   return self.setStatus("Canceled. No bookmark selected.")
  self.dom.location.href=url
  return self.setStatus("Opening:"+str(url))


 def showBookmarks(self):
  inhs=self.js.Components.interfaces.nsINavHistoryService
  historyService=self.js.Components.classes["@mozilla.org/browser/nav-history-service;1"].getService(inhs)
  hOps=historyService.getNewQueryOptions()
  hQuery=historyService.getNewQuery()
  inbs=self.js.Components.interfaces.nsINavBookmarksService
  bookmarksService=self.js.Components.classes["@mozilla.org/browser/nav-bookmarks-service;1"].getService(inbs)
  bsFolder=bookmarksService.placesRoot
  hQuery.setFolders([bsFolder], 1)
  result=historyService.executeQuery(hQuery,hOps)
  rootNode=result.root
  return self.gTree([("/",rootNode)],js=self.js,treeview="bookmarkTree")
#  return rootNode

 def showScreen(self,screenNum=None,y=None,absoluteY=None,x=None,force=0):
#  if self.dom.document._display==self.dom.document.childNodes[0]._display: log("displays still the same")
#  [log(i[-3]) for i in inspect.stack()]
  self.writeScreenCoordsToFile()
  _absoluteY=absoluteY
  _screenNum=screenNum
  if absoluteY==None:
   screenNum=self.screenNum if screenNum==None else screenNum
   y=self.screen.getyx()[0] if y==None else y
  else:
   absoluteY=absoluteY
   screenNum=self.getScreenNumber(absoluteY)
   y=self.getLineNumber(absoluteY)
  absoluteY=self.getScreenAbsolutePosition(screenNum=screenNum,y=0)
  x=self.screen.getyx()[1] if x==None else x
  log("showScreen:",absoluteY,screenNum,y,x)
  if _screenNum==self.screenNum and force==0:
   self.screenPos,self.screenPosX=y,x
   log("showScreen:just refreshing and moving. _screenNum=%s, screenNum=%s, y=%s, x=%s" % (str(_screenNum),str(self.screenNum),str(y),str(x),))
   self.screen.move(self.screenPos,self.screenPosX)
   self.screen.refresh()
   self.onFocus()
   return
  self.screen.clear()
  for n in self.nodes_flat: #self.iterNodes(self.dom.document):
#   log("sscr.node:"+n.nodeName)
   for _,nY,nX,t in self._display[n][1:]:
#    log("SSCR:screenNum=%s,nY=%s,nX=%s,t=%s" % (str(screenNum),str(nY),str(nX),str(t),))
    if nY<absoluteY:
     continue
    if nY>absoluteY+self.maxy:
     break
#    log("draw",nY-absoluteY,nX,t)
    self.screen.addstr(nY-absoluteY,nX,t)
  self.screenPos,self.screenPosX=y,x
  self.screenNum=screenNum
  self.screen.move(y,x)
  self.screen.refresh()
  self.onFocus()
  self.pagePosition()
  return None

 def closePage(self):
  try:
   self.js.gBrowser.removeCurrentTab()
  except:
   pass

 def searchPage(self,direction="forward"):
  focus=self.getFocusedElement()
  if direction not in ["previous","next"] or self.searchString=="":
   self.searchString=self.prompt('Search String:',self.entry)
  nodes=self.nodes_flat #self.iterNodes(self.dom.document)
  nodesLength=len(nodes)
  focusIndexO=nodes.index(focus)
  if direction=="backward" or direction=="previous":
   index=-1
   function="rfind"
   nodes=nodes[::-1]
   focusIndex=nodes.index(focus)
   nodes=nodes[focusIndex+1:]+nodes[:focusIndex+1]
  if direction=="forward" or direction=="next":
   index=None
   function="find"
   focusIndex=nodes.index(focus)
   nodes=nodes[focusIndex+1:]+nodes[:focusIndex+1]
   log("searching %d nodes, old size %d, location of current node is %d, old loc was %d" % (len(nodes),nodesLength,focusIndex,focusIndexO,))
  for n in nodes:
   for _,nY,nX,t in self._display[n][1::index]:
    if config.caseSensitiveSearch=="true":
     l=getattr(t,function)(self.searchString)
    else:
     l=getattr(t.lower(),function)(self.searchString.lower())
    if l!=-1:
     log("found element %s at %d,%d" % (str(n),nY,nX,))
     return self.showScreen(absoluteY=nY,x=nX+l)
  self.setStatus("Search String {0} not found.".format(self.searchString))

 def isOnLayoutElement(self,n,sn=None,y=None,x=None):
  """Determine if provided position tripple is located on a coordinate considered to be accessible spacing.
When spacing is added to an element, an extra coord is appended to the beginning of the element.
"""
  sn=self.screenNum if sn==None else sn
  y=self.screenPos if y==None else y
  x=self.screenPosX if x==None else x
  pos=self.getScreenAbsolutePosition(sn,y)
  dd=self._display[n]
  if len(dd)>0 and pos==dd[0][1] and (len(dd)==1 or (len(dd)>1 and dd[0][1]!=dd[1][1])):
   return 1
  return 0

 def getFocusedElement(self,sn=None,y=None,x=None):
  """Given an optional (screenNumber, y, x) tripple, search the tree for the first element whose text is not null, and whose position is consistent with the provided tripple.
No section of the physical screen array should be unattached from an element.
Some sections may have more than one element attached, as each element is attached to a coord on the screen array as it is encountered.
E.g. we find a body element, which goes at 1,0 (we assume title is at 0,0).
Then we find a div element. That div is also at 1,0, and that 1,0 is saved in the div's _display parameter.
Then we find text, "The cow gives brown milk. It's confused."
That text also is marked at 1,0, and extends to 1,len(text).
The next element will be placed at 1,len(text)+1.
If said next text requires a line break, That line break will be attached to that text element.
"""
  sn=self.screenNum if sn==None else sn
  y=self.screenPos if y==None else y
  x=self.screenPosX if x==None else x
  pos=self.getScreenAbsolutePosition(sn,y)
  nodes=self.nodes_flat #self.iterNodes(self.dom.document)
  l=[]
  lenNodes=len(nodes)
  i=lenNodes
  while i-1>0:
   i-=1
   n=nodes[i]
#   log("getDataObject:"+"pos:"+str(pos)+","+str(n.nodeName)+","+str(n._display))
   if self._display[n]==[] or len(self._display[n])==1: l.append(n); continue
   if self._display[n][0][1]<=pos<=self._display[n][-1][1]+1:
    log("searching for pos %d, %d<=%d<=%d" % (pos,self._display[n][0][1],pos,self._display[n][-1][1],))
    for frm,nY,nX,t in self._display[n]:
#     log("displayInNode:pos="+str(pos)+",ny="+str(nY)+",x="+str(x)+",nX="+str(nX)+",nx+len(t)="+str(nX+len(t)+1))
     if (t!='' or (t=='' and frm==0)) and nY==pos and (nX<=x<=nX+len(t)+1): # or t.strip()==''):
#      log("getFocusedElement:returning "+n.nodeName+","+str(n),nY,nX,pos,y,x)
      return n
   if self._display[n][0][1] < pos:
    if len(l)>0:
     return l[-1]
  i=len(nodes)
  while i-1>0:
   i-=1
   n=nodes[i]
   if len(self._display[n])>0 and self._display[n][-1][1]==pos and self._display[n][-1][2]==x:
    return n

 def findElement(self,tag="",attrs={},direction="forward"):
  """given a list of tags and an optional dictionary of attributes, search the dom tree for the requested tag(s).
Pull all nodes as a list. Move through the list, skipping nodes whose position (physical or tree-logical) would preclude them from being candidates.
Return the first matching node.
"""
  if type(tag)==str: tag=[tag]
  tag=[i.upper() for i in tag]
  currentNode=self.getFocusedElement()
  nodes=self.nodes_flat #self.iterNodes(self.dom.document)
  y,x,sn=self.screenPos,self.screenPosX,self.screenNum
  absoluteY=self.getScreenAbsolutePosition(screenNum=sn,y=y)
  idx=nodes.index(currentNode)
  lenNodes=len(nodes)
  if direction=="forward":
   idx-=1
   while idx+1<lenNodes:
    idx+=1
    i=nodes[idx]
    if i.nodeName not in tag:
     continue
    try:
     d=self._display[i][1]
    except:
      continue
    nY,nX=d[1:3]
    if (nY>absoluteY):
# or (nY==absoluteY and nX>x):
     log("findElement:"+str(y)+","+str(x)+":"+str(self._display[i][1])+","+str(i))
     return i
  if direction=="backward":
   while idx>0:
    idx-=1
    i=nodes[idx]
    if i.nodeName not in tag:
     continue
    try:
     d=self._display[i][1]
    except:
      continue
    nY,nX=d[1:3]
    if (nY<absoluteY): # or (nY==absoluteY and nX<x and currentNode.parentNode.parentNode!=i):
     log("findElement:"+str(y)+","+str(x)+":"+str(self._display[i][1])+","+str(i))
     return i 

