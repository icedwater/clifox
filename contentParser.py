import re
import utils
log=utils.log
class parser(object):
#skip only this top-level element
 SKIP_THIS=-2
#skip to next element of same or higher level (ignores all children)
 SKIP_CHILDREN=-1
 spaces=re.compile("[\n\r\t ]+")

 def __init__(self,nodes,maxx):
  """initialize parser
supply a list of document elements to be rendered (e.g. from iterNodes)
"""
  self.maxx=maxx
  self.lst=nodes
  self.funcCache={}
  self.endFuncCache={}
  self.skip=self.SKIP_THIS
  self.inPre=0

 def wrapText(self, text, width=None, indent=None,pre=0):
  """wraps text, respecting spacing and line breaks whenever possible
"""
  width=self.maxx if width==None else width
  start,end=0,0
#if we're starting to the right of 0, then we have that amount fewer spaces to place text, so remove that amount from @end
  if indent!=None:
   end=width-indent
  else:
   end=width
#  log("beforeWhile:","end:",end,"textLength:",textLength)
#if the text will all fit on the current line, then return this text
  if len(text)<end:
   return [text]
  lines=[]
  while text:
#pre means that the text is preformatted
   if pre>0:
#search for a new line, so we can split the text appropriately
    where=text.find("\n")
#    log("text:",len(text),repr(text),where)
    if where>-1 and where<end:
     t,text=text[:where],text[where+1:]
     lines.append(t)
     end=width
     continue
   if len(text)<end:
    lines.append(text)
    break
#search for spaces from the end of the largest string that can be placed on the remainder of the current line
   where=text[:end].rfind(" ")
   if where>-1:
    t,text=text[:where],text[where+1:]
    lines.append(t)
   else:
    t,text=text[:end],text[end:]
    lines.append(t)
   end=width
  return lines
 
 def itemFunc(self,item):
  """returns the function for handling an element, or self.unknown"""
  if item.nodeName in self.funcCache:
   return self.funcCache[item.nodeName]
  x=getattr(self,item.nodeName.lower().replace("#",""),self.unknown)
  self.funcCache[item.nodeName]=x
  return x

 def endItemFunc(self,item):
  """returns the function for ending an element or self.endUnknown
This could be used, for example, to require new lines after headings."""
  try:
   return self.endFuncCache[item.nodeName]
  except:
   n=item.nodeName
   x=getattr(self,"end"+n[0].upper()+n[1:].lower().replace("#",""),self.endUnknown)
   self.endFuncCache[item.nodeName]=x
   return x

 def parse(self,start=0,end=-1):
  """parse the supplied node list and return the result
result is returned as {line:[[columnStart,lineNodeText,node],...]}
columnStart shows where the text starts on each line.
Text is wrapped, and ends for each line at columnStart+len(lineNodeText).
"""
  self.labels=[]
#dict([(i.control.ref.id,i.textContent) for i in self.lst if i.nodeName=="LABEL"])
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
#    log("idx:",idx,"open:",len(open))
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
   if self.inPre>0:
    if self.x==0:
     text=text.lstrip()
   else:
    if self.x==0 or "".join([i[1] for i in self.ret.get(self.y,[])]).endswith(" "):
     text=text.lstrip()
#   else:
    text=self.spaces.sub(" ",text)
   new=self.wrapText(text,self.maxx,self.x,self.inPre)
   if type(new)!=list:
    new=[new]
   while new:
    l=new.pop(0)
    if not self.ret.get(self.y,None):
     self.ret[self.y]=[]
    l=l.strip() if self.x==0 else l
    self.ret[self.y].append((self.x,l,self.lst[idx]))
    self.x+=len(l)
    if new:
     log("newLine from wrap")
     self.y+=1; self.x=0
  return self.ret

 def getChildCount(self,idx):
  """return the number of children below the supplied index"""
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

 def insertAndParse(self,nodes):
  """untested
insert and parse a chunk of new nodes.
assume nodes[0] is a node currently in self.lst
"""
  try:
   idx=self.index(nodes[0])
  except Exception,e:
   raise Exception("given node is not in index")
  old=self.getChildCount(idx)
  [self.lst.pop(idx) for _ in range(old+1)]
  [self.lst.insert(idx,i) for i in nodes[::-1]]
  self.parse()

 def getChildren(self,i):
  """returns all children below the supplied index
"""
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

 """This list holds the names of any elements that can be placed before other elements on a single line, regardless of the other elements types.
Currently, only the LI, list item, tag is used here.
This tag is so common and small that it can be placed before many other elements, such as links and buttons, without impacting the flow of a webpage.
"""
 sameLinePreformatted=["LI"]
 def needNewLine(self,y=None,x=None):
  """find if there are elements on the current line that have text and where such text is not generated purely for element type
for instance, this function would return false if one was scanning a line with a list item and a link, because the list item would show a "* ", which would mean that the link would not require a new line.
"""
  x=self.x if x==None else x
  if x==0:
   return 0
  y=self.y if y==None else y
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
  """check if there is need for a line break because of existing text on the current line."""
  if self.needNewLine():
   self.y+=1
   self.x=0

 def fnl(self,idx,force=0):
  """insert a new line regardless of other elements on the current line.
For instance, this would be used for a br element, where a line break is mandatory.
"""
  if self.x!=0 or force==1:
   self.y+=1
   self.x=0
#  if self.y not in self.ret:
#   self.ret[self.y]=[]
#  self.ret[self.y].append((self.x,'',self.lst[idx]))

 def div(self,idx):
  self.nl(idx)
  return ''

 def pre(self,idx):
  self.inPre+=1
  return ''

 def endPre(self,idx):
  self.inPre-=1
  return ''

 def h1(self,idx):
  self.nl(idx)
  return ''
 h2=h1
 h3=h1
 h4=h1
 h5=h1
 h6=h1

 def endH1(self,idx):
  if self.x!=0:
   self.fnl(idx)
  return ''
 endH2=endH1
 endH3=endH1
 endH4=endH1
 endH5=endH1
 endH6=endH1

 def li(self,idx):
  self.nl(idx)
  return '* '

 def unknown(self,idx):
  return ''

 def textarea(self,idx):
  self.fnl(idx)
  self.skip=self.SKIP_CHILDREN
  n=self.lst[idx]
  nm=self.getInputName(idx)
  v=n.innerHTML
  c=v if v else ''
  if nm: c="["+nm+"] "+c
  return c

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
  c=v if v else ''
  if nm: c="["+nm+"] "+c
  return c

 def endSelect(self,idx):
  self.fnl(idx)
  return ''

 def form(self,idx):
  self.fnl(idx)
  return ''

 def endForm(self,idx):
  self.fnl(idx)
  return ''

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
  c=value
  if nm: c="["+nm+"] "+c
  return c

 def endInput(self,idx):
  self.fnl(idx)
  return ''

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

 def inputImage(self,idx):
  i=self.lst[idx]
  t=i.alt
  if not t:
   t=i.title
  if not t:
   t=i.src.rsplit("/",1)[-1]
  return "[*"+t+"]"

 def inputCheckbox(self,idx):
  c="x" if self.lst[idx].checked else " "
  return "["+c+"]"

 def inputRadio(self,idx):
  c="+" if self.lst[idx].checked else "-"
  return "["+c+"]"

 def getInputName(self,idx):
  if self.lst[idx].type.lower() in ("submit","button","image"):
   return ''
  n=self.lst[idx]
  if n.title:
   t=n.title
  elif n.ref.id in self.labels:
   t=self.labels[n.ref.id]
  else:
   t=n.name
  if not t:
   t="unlabeled"
  return t

 def a(self,idx,fromImg=0):
  if self.lst[idx].name:
#   self.skip=self.SKIP_CHILDREN
   return ''
  self.nl(idx)
  n=self.lst[idx]
  children=self.getChildren(idx)
  imgs=[i for i in children if i.nodeName=="IMG"]
  if not imgs:
   if n.textContent:
    return "{} "
   if not n.textContent and n.title:
    return "{} "+n.title
   if not n.textContent:
    return "{"+n.href+"} "
  else:
   try:
    iidx=children.index(imgs[0])
    t="{"+self.img(iidx+idx+1).strip()+"}"
    self.skip=self.SKIP_CHILDREN
    return t
   except:
    pass
  return ''

 def endA(self,idx):
#  self.fnl(idx)
  return ''

 def endImg(self,idx):
  self.fnl(idx)

 def img(self,idx,embedded=0):
  if not embedded: self.nl(idx)
  i=self.lst[idx]
#  log("img:",idx,i.nodeName,i.outerHTML)
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
  t="[*"+t+"] "
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
   if t: return blank
  return blank

 def hr(self,idx):
  return '-'*40

 def br(self,idx):
  if self.getBlankLines(idx)<2:
   self.fnl(idx)
  return ''

 def p(self,idx):
  if self.getBlankLines(idx)<2:
   self.fnl(idx)
   self.fnl(idx)
  return ''

 def tr(self,idx):
  self.nl(idx)
  return ''

 def td(self,idx):
  self.nl(idx)
  return ''
