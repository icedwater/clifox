import re
import utils
log=utils.log
class parser(object):
#skip only this top-level element
 SKIP_THIS=-2
#skip to next element of same or higher level (ignores all children)
 SKIP_CHILDREN=-1
 spaces=re.compile("[\n\r\t ]+")

 def __init__(self,nodes,maxx=160):
  self.maxx=maxx
  self.lst=nodes
  self.funcCache={}
  self.endFuncCache={}
  self.skip=self.SKIP_THIS

 def wrapText(self, text, width=None, indent=None):
  width=self.maxx if width==None else width
#  log("wrapToFit:",text,width,indent)
  start,end=0,0
  lines=[]
  textLength=len(text)
  if indent!=None:
   end=width-indent
  else:
   end=width
  if textLength<end:
   lines.append(text)
   return lines
  while end<textLength:
   if text[end]==' ':
    lines.append(text[start:end])
    start=end+1
    end=start+width
   if end==start:
    lines.append(text[start:start+width])
    start=start+width
    end=start+width
   end-=1
  lines.append(text[start:])
  return lines
 
 def itemFunc(self,item):
  if item.nodeName in self.funcCache:
   return self.funcCache[item.nodeName]
  x=getattr(self,item.nodeName.lower().replace("#",""),self.unknown)
  log("item:",x)
  self.funcCache[item.nodeName]=x
  return x

 def endItemFunc(self,item):
  try:
   return self.funcCache[item.nodeName]
  except:
   n=item.nodeName
   x=getattr(self,"end"+n[0].upper()+n[1:].lower().replace("#",""),self.endUnknown)
   self.endFuncCache[item.nodeName]=x
   return x

 def parse(self,start=0,end=-1):
  self.labels=dict([(i.control,i.textContent) for i in self.lst if i.nodeName=="LABEL"])
  end=len(self.lst) if end==-1 else end
  self.ret={}
  open=[]
  skip=-1
  idx=-1
  self.y=0
  self.x=0
  for i in self.lst:
   idx+=1
#when skip is posative, we decrement skip by 1 and continue this comments pattern until skip is 0
#our goal is to skip a certain number of children
#we have heading,link,text; link says skip children; skip=1; skip=1 to skip=0; continue; we've passed the text leaf 
   if idx and self.lst[idx].num<=self.lst[idx-1].num:
    log("idx:",idx,"open:",len(open))
    rng=(self.lst[idx-1].num-self.lst[idx].num)+1
    close=[open.pop(-1) for iRng in xrange(rng)]
    [self.endItemFunc(self.lst[oC])(oC) for oC in close]
   open.append(idx)
   if skip>0:
    skip-=1
    continue
   itemFunc=self.itemFunc(i)
#text,move,type
   text=itemFunc(idx)
   move=self.skip
   if move==self.SKIP_CHILDREN:
    skip=self.getChildCount(idx)
    self.skip=self.SKIP_THIS
   if self.x==0 or "".join([i[1] for i in self.ret.get(self.y,[])]).endswith(" "):
    text=text.lstrip()
#   else:
   text=self.spaces.sub(" ",text)
   new=self.wrapText(text,self.maxx,self.x)
   if type(new)!=list:
    new=[new]
   while new:
    l=new.pop(0)
    if not self.ret.get(self.y,None):
     self.ret[self.y]=[]
    self.ret[self.y].append((self.x,l,self.lst[idx]))
    self.x+=len(l)
    if new: self.y+=1; self.x=0
  return self.ret

 def getChildCount(self,idx):
  num=self.lst[idx].num
  count=0
  idx+=1
  ll=len(self.lst)
  while idx<ll:
   if self.lst[idx].num>num:
    count+=1
    idx+=1
    continue
   else:
    break
  return count

 def insertAndParse(self,where,new):
  for i in self.lst:
   if i[2]<where:
    continue
   if i[1]>where:
    break
   if i[1]==where:
    [self.lst.insert(i[1],j) for j in new[::-1]]
    self.parse(i[1],len(new))

 def getChildren(self,i):
  if type(i)!=int:
   i=self.lst.index(i)
  start=i
  startNum=self.lst[start].num
  i+=1
  ret=[]
  while i<len(self.lst) and self.lst[i].num>startNum:
   ret.append(self.lst[i])
   i+=1
  return ret

 sameLinePreformatted=["LI"]
 def needNewLine(self,y=None,x=None):
  """find if there are elements on the current line that have text and where such text is not generated purely for element type
for instance, this function would return false if one was scanning a line with a list item and a link, because the list item would show a "* ", which would mean that the link would not require a blank line.
"""
  y=self.y if y==None else y
  x=self.x if x==None else x
  if x==0:
   return 0
  elems=self.ret.get(y,[])
  if not elems:
   return 0
  elems=[i for i in elems if i[0]<x]
  tl=0
  for i in elems[::-1]:
   t=i[1].strip()
   if t and i[2].nodeName in self.sameLinePreformatted:
    return 0
   if t:
    return 1
  return 0

class htmlParser(parser):
 def nl(self,idx):
  if self.needNewLine():
   self.y+=1
   self.x=0

 def fnl(self,idx):
  self.y+=1
  self.x=0
  if self.y not in self.ret:
   self.ret[self.y]=[]
  self.ret[self.y].append((self.x,'',self.lst[idx]))

 def div(self,idx):
  return ''

 def h1(self,idx):
  self.nl(idx)
  return ''
 h2=h1
 h3=h1
 h4=h1
 h5=h1
 h6=h1

 def li(self,idx):
  self.nl(idx)
  return '* '

 def unknown(self,idx):
  return ''

 def text(self,idx):
  return self.lst[idx].nodeValue

 def option(self,idx):
  self.skip=self.SKIP_CHILDREN
  return ''

 def select(self,idx):
  self.fnl(idx)
  n=self.lst[idx]
  nm=self.getInputName(idx)
  if n.selectedIndex>=0:
   try:
    v=n.options[n.selectedIndex].textContent
   except:
    v=n.options[0].textContent
  else:
   v=n.options[0].textContent
  c=v
  if nm: c="["+nm+"] "+c
  return c

 def input(self,idx):
  nm=self.getInputName(idx)
  if nm==None:
   return
  self.fnl(idx)
  nt=self.lst[idx].type
  nt=nt[0].upper()+nt[1:].lower()
  value=getattr(self,"input"+nt,self.inputUnknown)(idx)
  if self.lst[idx].disabled:
   nm="disabled "+nm
  return "[%s] %s" % (nm,value,)

 def inputHidden(self,idx):
  return None

 def unknownInput(self,idx):
  return self.lst[idx].value

 def inputText(self,idx):
  return self.lst[idx].value

 def inputUnknown(self,idx):
  return self.inputText(idx)

 def inputPassword(self,idx):
  return "*"*len(self.lst[idx].value)

 def inputSubmit(self,idx):
  return self.inputButton(idx)

 def inputButton(self,idx):
  return "[*"+self.lst[idx].value+"]"

 def inputCheckbox(self,idx):
  c="x" if self.lst[idx].checked else " "
  return "["+c+"]"

 def inputRadio(self,idx):
  c="+" if self.lst[idx].checked else "-"
  return "["+c+"]"

 def getInputName(self,idx):
  if self.lst[idx].type in ("submit","button"):
   return ''
  n=self.lst[idx]
  if n.title:
   t=n.title
  elif n in self.labels:
   t=self.labels[n]
  else:
   t=n.name
  return t

 def a(self,idx,fromImg=0):
  self.nl(idx)
  n=self.lst[idx]
  imgs=[i for i in self.getChildren(idx) if i.nodeName=="IMG"]
  if not imgs:
   if n.textContent:
    return "{} "
   if not n.textContent and n.title:
    return "{} "+n.title
   if not n.textContent:
    return "{"+n.href+"} "
  else:
   try:
    return "{"+self.img(self.getChildren(imgs[0]),1).strip()+"}"
    self.skip=self.SKIP_CHILDREN
   except:
    pass
  return ''

 def endA(self,idx):
  self.fnl(idx)
  return ''

 def img(self,idx,embedded=0):
  if not embedded: self.nl(idx)
  i=self.lst[idx]
  if i.alt:
   t=i.alt
  elif i.title:
   t=i.title
  else:
   if i.src.split(":",1)[0].lower()=='data':
    t="unknown"
   else:
    t=i.src.rstrip("/").rsplit("/",1)[-1]
  return "[%s] " % (t,)

 def endUnknown(self,idx):
  return ''

 def button(self,idx):
  self.fnl(idx)
  n=self.lst[idx]
  t=n.value
  if not t:
   t=n.title
  if not t:
   t=n.textContent
  if not t:
   t="submit"
  self.skip=self.SKIP_CHILDREN
  t="["+t+"] "
  return t

 def getBlankLines(self,idx,maxCheck=2):
  blank=0
  y=self.y
  while y>0:
   if blank>maxCheck:
    break
   y-=1
   t="".join([i[1].strip() for i in self.ret.get(y,[])])
   if not t: blank+=1
  return blank

 def hr(self,idx):
  return '-'*40

 def br(self,idx):
  self.nl(idx)
  if self.getBlankLines(idx)<=2:
   self.fnl(idx)
  return ''

 def p(self,idx):
  self.nl(idx)
  if self.getBlankLines(idx)<=1:
   self.fnl(idx)
  return ''

 def tr(self,idx):
  self.nl(idx)
  return ''

 def td(self,idx):
  self.nl(idx)
  return ''
