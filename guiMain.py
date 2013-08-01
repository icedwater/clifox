import os,curses,mozCom,utils,re,unidecode
from utils import log,generate_error_report
import configParser
config=configParser.config
import contentParser
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
  try:
   nodes=self.iterNodes(self.dom.document)
   self.parser=contentParser.htmlParser(nodes,self.maxx)
   self._display=self.parser.parse()
   self.numLines=max(self._display.keys())
  except Exception,e:
   utils.generate_error_report()
   self.setStatus(str(e))

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
  x=self.screenPosX if x==None else x
  if absoluteY==None:
   y=self.screenPos if y==None else y
   screenNum=self.screenNum if screenNum==None else screenNum
   absoluteY=self.getScreenAbsolutePosition(screenNum=screenNum,y=y)
  else:
   absoluteY=absoluteY
   screenNum=self.getScreenNumber(absoluteY)
   y=self.getLineNumber(absoluteY)
  self.writeScreenCoordsToFile()
  log("showScreen:","absoluteY:",absoluteY,"x:",x,"screen:",screenNum,"y:",y)
  if screenNum==self.screenNum and force==0:
   self.screenPos,self.screenPosX=y,x
   log("showScreen:just refreshing and moving.")
   self.screen.move(self.screenPos,self.screenPosX)
   self.screen.refresh()
   self.onFocus()
   return
  absoluteY-=y
  self.screen.clear()
  low,high=absoluteY,absoluteY+self.maxy
  yW=0
  while low<=high:
   elems=self._display.get(low,[])
   for xW,text,n in elems:
    try:
     self.screen.addstr(yW,xW,text)
    except:
     log("error:",yW,xW,text)
   yW+=1
   low+=1
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
  pos=self.getScreenAbsolutePosition(self.screenNum,self.screenPos)
  focus=self.getFocusedElement()
  if direction not in ["previous","next"] or self.searchString=="":
   self.searchString=self.prompt('Search String:',self.entry)
  if direction in ("forward","next"):
   direction=1
  else:
   direction=-1
  ss=self.searchString
  elem=None
  d=self._display
  lines=d.keys()
  if direction==1:
   lines=[i for i in lines if i>pos]+[i for i in lines if i<pos]+[i for i in lines if i==pos]
   func="find"
  else:
   lines=[i for i in lines if i<pos][::-1]+[i for i in lines if i>pos][::-1]+[i for i in lines if i==pos]
   direction=-1
   func="rfind"
  for y in lines:
   for i in d[y][::direction]:
    if config.caseSensitiveSearch:
     pos=getattr(i[1].lower(),func)(ss)
    else:
     pos=getattr(i[1],func)(ss)
    if pos!=-1:
     elem=(y,i[0],pos)
     break
   if elem:
    break
  if elem:
   return self.showScreen(absoluteY=elem[0],x=elem[1]+elem[2])
  return self.setStatus("Search string \"%s\" not found." % (self.searchString,))

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
  elems=self._display.get(pos,[])
  elems2=[i for i in elems if x>=i[0]]
  if elems2:
   return elems2[-1][-1]
  if elems:
   return elems[-1][-1]

 def getElementPosition(self,n):
  for yW in self._display:
   x=[i for i in self._display[yW] if i[2]==n]
   if x:
    return yW,x[0][0],x[0][2]

 def findElement(self,tag="",attrs={},direction="forward"):
  """given a list of tags and an optional dictionary of attributes, search the dom tree for the requested tag(s).
Pull all nodes as a list. Move through the list, skipping nodes whose position (physical or tree-logical) would preclude them from being candidates.
Return the first matching node.
"""
  if type(tag)==str: tag=[tag]
  tag=[i.upper() for i in tag]
  currentNode=self.getFocusedElement()
#  nodes=self.nodes_flat #self.iterNodes(self.dom.document)
  y,x,sn=self.screenPos,self.screenPosX,self.screenNum
  absoluteY=self.getScreenAbsolutePosition(screenNum=sn,y=y)
  if direction=="forward":
   for yW in xrange(absoluteY,max(self._display.keys())+1):
    if yW not in self._display: continue
    for xW,text,elem in self._display[yW]:
     if yW==absoluteY and xW<=x: continue
     if elem.nodeName in tag:
      return yW,xW,elem
  else:
   for yW in xrange(absoluteY-1,0,-1):
    if yW not in self._display: continue
    for xW,text,elem in self._display[yW][::-1]:
     if elem.nodeName in tag:
      return yW,xW,elem
