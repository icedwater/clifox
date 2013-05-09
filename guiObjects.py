#holds basic GUI structures for use in curses (treeview, listbox, checkbox, ETC)
#the __init__ and loop methods are the methods for use with the main program, so test by "import guiObjects; test=guiObjects.object(); print test.loop()"
import curses,time,os,os.path,string,sys
from utils import log

class Checkbox(object):
 def __init__(self,**kw):
  self.title="untitled"
  self.checked=0
  [setattr(self,k,v) for k,v in kw.items()]
  self.screen.clear()
  self.screen.addstr(0,0,self.title)
  self.draw()

 def draw(self):
  self.screen.move(1,0)
  if self.checked>0:
   t="[x] "
  else:
   t="[ ] "
  s=t+self.values[0][:self.maxx]
  self.screen.addstr(1,0,s)
  self.screen.refresh()

 def loop(self):
  while 1:
   c=self.screen.getch()
   if c==-1:
    time.sleep(0.001)
    continue
   log("chkbox:key:",c)
   if c==32:
    self.checked=0 if self.checked==1 else 1
    log("chkbox:draw")
    self.draw()
   if c==curses.KEY_BACKSPACE:
    return self.checked
   if c==ord("\n"):
    return self.checked

class Editbox(object):
 """Editing widget using the interior of a window object.
  Supports the following Emacs-like key bindings:
 Ctrl-A   Go to left edge of window.
 Ctrl-B   Cursor left, wrapping to previous line if appropriate.
 Ctrl-D   Delete character under cursor.
 Ctrl-E   Go to right edge (stripspaces off) or end of line (stripspaces on).
 Ctrl-F   Cursor right, wrapping to next line when appropriate.
 Ctrl-G   Terminate, returning the window contents.
 Ctrl-H   Delete character backward.
 Ctrl-J   Terminate if the window is 1 line, otherwise insert newline.
 Ctrl-K   If line is blank, delete it, otherwise clear to end of line.
 Ctrl-L   Refresh screen.
 Ctrl-N   Cursor down; move down one line.
 Ctrl-O   Insert a blank line at cursor location.
 Ctrl-P   Cursor up; move up one line.
 Move operations do nothing if the cursor is at an edge where the movement is not possible.  The following synonyms are supported where possible:
 KEY_LEFT = Ctrl-B, KEY_RIGHT = Ctrl-F, KEY_UP = Ctrl-P, KEY_DOWN = Ctrl-N, KEY_BACKSPACE = Ctrl-h
 """
 def __init__(self, **kw):
  self.default="Edit Field"
  [setattr(self,k,v) for k,v in kw.items()]
  self.win=self.screen
  self.loop=self.edit
  callback=validate=None
  (self.maxy, self.maxx) = self.win.getmaxyx()
  self.maxy -= 2
  self.maxx -= 1
  self.stripspaces = 1
  self.lastcmd = None
  self.validate = validate
  self.callback = callback
  self.text = [[] for y in xrange(self.maxy+1)]
  self.win.keypad(1)

 def text_insert(self, y, x, ch):
  if len(self.text[y]) > x:
   self.text[y].insert(x, ch)
  else: # <= x
   self.text[y] += [curses.ascii.SP] * (x - len(self.text[y]))
   self.text[y].append(ch)

 def text_delete(self, y, x):
  if y < 0 or x < 0 or y >= len(self.text) or x >= len(self.text[y]): return
  del self.text[y][x]
 
 def text_delete_line(self,y,x=0):
  del self.text[y][x:]

 def text_insert_line(y):
  self.text.insert(y, [])

 def _end_of_line(self, y):
  "Go to the location of the first blank on the given line."
  last = self.maxx
  while 1:
   if curses.ascii.ascii(self.win.inch(y, last)) != curses.ascii.SP:
    last = min(self.maxx, last+1)
    break
   elif last == 0:
    break
   last = last - 1
  return last

 def do_command(self, ch):
  "Process a single editing command."
  (y, x) = self.win.getyx()
  self.lastcmd = ch
  if curses.ascii.isprint(ch):
   if y < self.maxy or x < self.maxx:
    # The try-catch ignores the error we trigger from some curses
    # versions by trying to write into the lowest-rightmost spot
    # in the window.
    try:
     self.text_insert(y, x, ch)
     self.win.addstr(y, 0, ''.join([chr(curses.ascii.ascii(ch)) for ch in self.text[y]]))
     self.win.move(y, x+1)
    except curses.error:
     pass
  elif ch == curses.ascii.SOH:         # ^a
   self.win.move(y, 0)
  elif ch in (curses.ascii.STX,curses.KEY_LEFT, curses.ascii.BS, curses.KEY_BACKSPACE,127):
   if x > 0:
    self.win.move(y, x-1)
   elif y == 0:
    pass
   elif self.stripspaces:
    self.win.move(y-1, self._end_of_line(y-1))
   else:
    self.win.move(y-1, self.maxx)
   if ch in (curses.ascii.BS, curses.KEY_BACKSPACE,127):
    self.win.delch()
    y, x = self.win.getyx()
    self.text_delete(y, x)
  elif ch == curses.ascii.EOT:         # ^d
   self.win.delch()
   self.text_delete(y, x)
  elif ch == curses.ascii.ENQ:         # ^e
   if self.stripspaces:
    self.win.move(y, self._end_of_line(y))
   else:
    self.win.move(y, self.maxx)
  elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):    # ^f
   ln=self._end_of_line(y)
   if x < self.maxx and x<ln and self.stripspaces:
    self.win.move(y, x+1)
   elif y == self.maxy:
    pass
   else:
    self.win.move(y+1, 0)
  elif ch == curses.ascii.BEL:         # ^g
   return True
  elif ch in (curses.ascii.NL, curses.ascii.CR):    # ^j ^m
   if self.maxy == 0:
    return True
   elif y < self.maxy:
    self.win.move(y+1, 0)
  elif ch == curses.ascii.VT:       # ^k
   if x == 0 and self._end_of_line(y) == 0:
    self.win.deleteln()
    self.text_delete_line(y)
   else:
    # first undo the effect of self._end_of_line
    self.win.move(y, x)
    self.win.clrtoeol()
    self.text_delete_line(y, x)
  elif ch == curses.ascii.FF:       # ^l
   self.win.refresh()
  elif ch in (curses.ascii.SO, curses.KEY_DOWN):   # ^n
   if y < self.maxy:
    self.win.move(y+1, x)
    if x > self._end_of_line(y+1):
     self.win.move(y+1, self._end_of_line(y+1))
  elif ch == curses.ascii.SI:       # ^o
   self.win.insertln()
   self.text_insert_line(y)
  elif ch in (curses.ascii.DLE, curses.KEY_UP):    # ^p
   if y > 0:
    self.win.move(y-1, x)
    if x > self._end_of_line(y-1):
     self.win.move(y-1, self._end_of_line(y-1))
  return False

 def gather(self):
  tmp = [''] * len(self.text)
  # convert each line to curses.ascii and join to a single string
  for y in xrange(len(self.text)):
   tmp[y] = ''.join([chr(curses.ascii.ascii(ch)) for ch in self.text[y]])
   if self.stripspaces:
    tmp[y] = tmp[y].rstrip()
  return '\n'.join(tmp).strip()

 def clear(self):
  self.text = [[] for y in xrange(self.maxy+1)]
  for y in xrange(self.maxy+1):
   self.win.move(y, 0)
   self.win.clrtoeol()
  self.win.move(0, 0)
 
 def draw(self):
  for y in xrange(len(self.text)):
   if len(self.text[y]) > 0:
    self.win.addstr(y, 0, ''.join([chr(curses.ascii.ascii(ch)) for ch in self.text[y]]))
   else:
    self.win.move(y, 0)
   self.win.clrtoeol()

 def edit(self):
  self.win.clear()
  text=list(self.default)
  "Edit in the widget window and collect the results."
  while 1:
   if text!=None and len(text)>0:
    ch=ord(text.pop(0))
    if len(text)==0:
     text=-1
   else:
    ch = self.win.getch()
    if ch==-1:
     time.sleep(0.02)
     continue
   o_ch = ch
   if self.validate:
    ch = self.validate(ch)
   if ch:
    if self.do_command(ch):
     break
   if self.callback:
    if self.callback(o_ch):
     break
   if text==-1:
    self.win.move(0,0)
    self.win.refresh()
    text=None
  return self.gather()

 def edit_one(self, ch=None):
  """Edit one character in the widget window. If done (exit or enter pressed on
     single line textbox), return True"""
  status = False
  if ch == None: ch = self.win.getch()
  o_ch = ch
  if self.validate: 
   ch = self.validate(ch)
  if ch: 
   if self.do_command(ch):
     return True 
  if self.callback:
   status = self.callback(o_ch)
  return status

class Listbox(object):
 def __init__(self,**kw):
  self.title="untitled"
  [setattr(self,k,v) for k,v in kw.items()]
  if hasattr(self,"values") and type(self.values[0])==str:
   self.values=[(self.values.index(i),i) for i in self.values]
  self.keys=[]
  self.keysWaitTime=0.4
  self.pos=1
  self.start=1
  self.end=self.maxy
  self.entry=self.maxy+1
  self.status=self.maxy+2
  self.displaySize=self.end
  self.offset=0
  self.setTitle(self.title)
#  self.setStatus(self.status)
  self.makeNewList()
#  log("list:",self.l)
  self.setDefault()
  self.draw()

 def setTitle(self,title="untitled"):
  pos=self.screen.getyx()
  self.screen.move(0,0)
  self.screen.clrtoeol()
  self.screen.addstr("%s" % (title))
  self.screen.move(pos[0],pos[1])

 def setStatus(self,status=""):
  pos=self.screen.getyx()
  self.screen.move(self.status,0)
  self.screen.clrtoeol()
  self.screen.addstr(self.status,0,status[:self.maxx])
  self.screen.move(pos[0],pos[1])

 def makeNewList(self):
  self.l=[]
  for i in range(0,len(self.values)+self.displaySize,self.displaySize):
   self.l.append(self.values[i:i+self.displaySize])
  if len(self.l[-1])==0:
   self.l=self.l[:-1]

 def draw(self,offset=None,move=None):
  if offset!=None:
   self.offset=offset
  if move!=None:
   self.pos=move
  items=self.l[self.offset]
  j=0
  for i in range(self.start,len(items)+1):
   self.screen.move(i,0)
   self.screen.clrtoeol()
   self.screen.addstr(i,0,items[j][-1])
   j+=1
  self.screen.move(self.pos,0)
  self.screen.refresh()

 def setDefault(self):
  if not hasattr(self,"default"):
   return
  k=-1
  for i in xrange(len(self.l)+1):
   for j in xrange(len(self.l[i])+1):
    k+=1
    if k==self.default:
     self.offset=i
     self.pos=j+1
     return

 def search(self,key):
  t=time.time()
  if key in string.printable and (len(self.keys)>0 and t-self.keys[-1][0]<self.keysWaitTime):
   self.keys.append((t,key))
  else:
   self.keys=[(t,key)]
  keys="".join([i[1] for i in self.keys])
  keys=keys.lower()
  for i in self.l:
   for j in i:
    if j[-1].lower().startswith(keys):
     offset,pos=self.l.index(i),i.index(j)+1
     return self.draw(offset=offset,move=pos)

 def loop(self):
  while 1:
   c=self.screen.getch()
   if c!=-1:
    if c==curses.KEY_UP:
     self.prevLine()
    elif c==curses.KEY_DOWN:
     self.nextLine()
    elif c==ord('\n'):
     return self.returnItem()
    else:
     if c>=0 and c<128:
      self.search(chr(c))
   else:
    time.sleep(0.02)

 def returnItem(self):
  y,x=self.screen.getyx()
  return self.l[self.offset][y-self.start]

 def nextLine(self):
  np=self.pos+1
  #log("nextLine","pos",self.pos,"np",np,"len(self.l)",len(self.l),"offset",self.offset)
  if np>len(self.l[self.offset]):
   if len(self.l)>self.offset+1:
    self.pos=self.start
    self.offset+=1
   else:
    return -1
  else:
   self.pos+=1
  self.draw()
 def prevLine(self):
  np=self.pos-1
  if np<self.start:
   if self.offset>0:
    self.pos=min(self.end,len(self.l[np]))
    self.offset-=1
   else:
    return -1
  else:
   self.pos-=1
  self.draw()

class FileBrowser(Listbox):
 def __init__(self,**kw):
  self.offset=0
  self.pos=1
  kw['title']=""
  self._dir=""
  self.dir_history={}
  self.dir=kw.get("dir",os.environ.get("HOME","/"))
  self.title=self.dir
  Listbox.__init__(self,**kw)

 def makeNewList(self):
  self.l=[]
  self.lastScreen=0
  files=[("d" if os.path.isdir(os.path.join(self.dir,i)) else "f",os.path.join(self.dir,i),i) for i in sorted(os.listdir(self.dir))]
  if self.dir not in self.dir_history:
    self.dir_history[self.dir]=[0,1]
  self.offset,self.pos=self.dir_history[self.dir]
  for i in range(0,len(files)+1,self.displaySize):
   self.l.append(files[i:i+self.displaySize])
   self.lastScreen+=1
  self.lastScreen-=1
#  log("makeNewList",self.dir,"the history",self.dir_history)

 def draw(self,offset=None,move=None):
  refreshFlag=1
#  log("draw",self.dir,"the history",self.dir_history)
  if offset!=None or move!=None:
   if offset!=None and offset!=self.offset:
    self.offset=offset
   else:
    refreshFlag=0
   if move!=None:
    self.pos=move
  self.dir_history[self.dir]=[self.offset,self.pos]
#  log("draw 2",self.dir,"the history",self.dir_history)
  if refreshFlag==0:
   self.screen.move(self.pos,0)
   self.screen.refresh()
   return 1
  l=self.l[self.offset]
  idx=0
  self.screen.clear()
  self.setTitle(self.dir)
  for type,fullfn,fn in l:
   idx+=1
   fn=fn.rstrip("/").rsplit("/",1)[-1]
   if type=="d":
    fn+="/"
   self.screen.addstr(idx,0,fn[:self.maxx])
  self.screen.move(self.pos,0)
  self.showScreenPosition()
  self.screen.refresh()

 def showScreenPosition(self):
  pos=self.screen.getyx()
  self.screen.move(self.entry,0)
  self.screen.clrtoeol()
  self.screen.addstr("screen %d of %d" % (self.offset,self.lastScreen))
  self.screen.move(pos[0],pos[1])

 def pageDown(self):
  if self.offset+1 <= self.lastScreen:
   self.offset+=1
   self.pos=self.start
   self.draw()

 def pageUp(self):
  if self.offset-1 >= 0:
   self.offset-=1
   self.pos=self.start
   self.draw()

 def returnItem(self):
  return self.l[self.offset][self.screen.getyx()[0]-1]

 def expand(self):
  ret=self.returnItem()
  if ret[0]=="d":
   self.dir=ret[1].rstrip("/")+"/"
   self.makeNewList()
   self.draw()
  else:
   self.setStatus("%s is not a directory." % (ret[1],))

 def collapse(self):
  self.dir=self.dir.rstrip("/").rsplit("/",1)[0]+"/"
  self.makeNewList()
  self.draw()

 def bottomOfDirectory(self):
  self.draw(self.lastScreen,len(self.l[self.lastScreen]))

 def keyHandler(self):
  while 1:
   c=self.screen.getch()
   if c!=-1:
    if c==curses.KEY_UP:
     self.prevLine()
    elif c==curses.KEY_DOWN:
     self.nextLine()
    elif c==curses.KEY_RIGHT:
     self.expand()
    elif c==curses.KEY_LEFT:
     self.collapse()
    elif c==curses.KEY_NPAGE:
     self.pageDown()
    elif c==curses.KEY_PPAGE:
     self.pageUp()
    elif c==curses.KEY_HOME:
     self.draw(0,1)
    elif c==curses.KEY_END:
     self.bottomOfDirectory()
    elif c==27: # escape key
     return
    elif c==ord('\n'):
     if self.returnItem()[0]!="d":
      return self.returnItem()[-2]
     else:
      self.expand()
    else:
     if 0<c<128:
      self.search(chr(c))
   else:
    time.sleep(0.02)

 def nextLine(self):
  super(FileBrowser,self).nextLine()
  self.dir_history[self.dir.rstrip("/")+"/"]=(self.offset,self.pos)

 def prevLine(self):
  super(FileBrowser,self).prevLine()
  self.dir_history[self.dir.rstrip("/")+"/"]=(self.offset,self.pos)
