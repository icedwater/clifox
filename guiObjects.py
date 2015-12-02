#holds basic GUI structures for use in curses (treeview, listbox, checkbox, ETC)
#the __init__ and loop methods are the methods for use with the main program, so test by "import GuiObjects; test=GuiObjects.object(); print test.loop()"
import curses,time,os,os.path,string,sys
from utils import log

class GuiObject(object):
 done=0
 def beepIfNeeded(self):
  if self.base.config.beeps:
   curses.beep()

 def setStatus(self,*a,**kw):
  return self.base.setStatus(*a,**kw)

class Dialog(GuiObject):
 """control holder
down and up arrows move through controls
enter selects default button or displays error if not one
"""
 @property
 def controlIndex(self):
  return self._controlIndex
 @controlIndex.setter
 def controlIndex(self,i):
  self._controlIndex=i
  self.controls[self._controlIndex].onFocus()
  return i

 def __init__(self,screen=None,base=None,y=0,x=0,controls=[]):
  self.base=base
  self.screen=screen
  self.y,self.x=y,x
  self._controls=controls
  self.controls=[]
  self.initialDraw()
  self.draw()

 def initialDraw(self):
  for i in xrange(0,len(self._controls)):
   co=self._controls[i]
   c=co[0](screen=self.screen,base=self.base,y=i,**co[1])
   self.controls.append(c)
  self.controlIndex=0

 def draw(self):
  for i in self.controls:
   i.draw()

 def handleKey(self,c):
  ret=1
  if c==curses.KEY_DOWN:
   if self.controlIndex>=len(self.controls):
    self.beepIfNeeded()
    self.setStatus("No more controls in this dialog. Please up arrow to the first control.")
    self.controlIndex=len(self.controls)-1
   else:
    self.controlIndex+=1
  elif c==curses.KEY_UP:
   if self.controlIndex<=0:
    self.beepIfNeeded()
    self.setStatus("This is the first control in this dialog.")
    self.controlIndex=0
   else:
    self.controlIndex-=1
  else:
   ret=self.controls[self.controlIndex].handleKey(c)
  return ret

class Button(GuiObject):
 def __init__(self,screen=None,base=None,y=1,x=0,prompt="Button"):
  self.base=base
  self.screen=screen
  self.y,self.x=y,x
  self.prompt=prompt
  self.selected=0
  self.draw()

 def draw(self):
  s="[*%s]" % (self.prompt,)
  self.screen.addstr(self.y,self.x,s)
  self.screen.refresh()

 def handleKey(self,k):
  if k==10:
   self.done=1
   self.selected=1
   return 1
  return None

class Checkbox(GuiObject):
 """checkbox, whose value can be 1 or 0
screen: curses screen object
base:base object
y,x: coordinates for the top left point of this object on screen
prompt: the text shown as the label for this control, set to None if the inPage setting is to be used with text from the current line
"""
 def __init__(self,screen=None,base=None,y=1,x=0,prompt="no prompt",default=0):
  self.screen=screen
  self.base=base
  self.y,self.x=y,x
  self.prompt=prompt
  self.default=default
  self.draw()

 def draw(self):
  if self.checked>0:
   t="[+] "
  else:
   t="[-] "
  s="%s %s" % (t,self.prompt if self.prompt else "")
  self.screen.addstr(self.y,self.x,s)
  self.screen.refresh()

 def keyHandler(self,c):
  if c==32:
   self.checked=0 if self.checked==1 else 1
   self.draw()
   return 1
  return 0

class Readline(GuiObject):
 """
prompt for user input, with bindings to that of the default readline implimentation
prompt: prompt displayed before the users text
history: a list of strings which constitutes the previously entered set of strings given to the caller of this function during previous calls
text: the default text, entered as if the user had typed it directly
echo: acts as a mask for passwords (set to ' ' in order to not echo any visible character for passwords)
length: the maximum length for this text entry (element.attr=maxlength is the corresponding html attribute)
delimiter: the delimiter between prompt and text
readonly: whether to accept new text
"""
 def __init__(self,screen=None, base=None, y=0, x=0, history=[], prompt=u"input", default=u"", echo=None, maxLength=-1, delimiter=u": ", readonly=0):
  self.value=default
  self.done=0
  self.base=base
  self.screen=screen
  self.y,self.x=y,x
  self.history=history
  self.historyPos=len(self.history) if self.history else 0
  self.prompt=prompt
  self.delimiter=delimiter
  self.echo=echo
  self.readonly=readonly
  self.maxLength=maxLength
#prompt and delimiter
  self.s=u"%s%s" % (self.prompt,self.delimiter,) if self.prompt else ""
#position in the currently-being-editted text
  self.ptr=0
#start of text entry "on-screen", should be greater than self.ptr unless there is absolutely no prompt, (in other words, a completely blank line)
#if there's a prompt, startX should be right after the prompt and the delimiter
#if not, startX is going to be wherever self.x is, as that's where our text is going to appear
  self.startX=len(self.s) if self.s else self.x
#put ptr at the end of the current bit of text
  self.currentLine=self.value
  self.ptr=len(self.currentLine)
  self.insertMode=True
  self.lastDraw=None
  self.draw()

 def externalEdit(self):
  if self.base.config.editor:
   e=self.base.config.editor
  elif os.environment.get("EDITOR"):
   e=os.environment.get("EDITOR")
  else:
   return None
  tempfile="/tmp/squigglitz"
  open(tempfile,"wb").write(self.currentLine)
  cmd="%s %s" % (e,tempfile)
  os.system(cmd)
  fh=open(tempfile,"rb")
  self.currentLine=fh.read()
  fh.close()
  os.remove(tempfile)
  return self.currentLine
 
 def getunicode(self, c):
   tc = u' '
   buf = ''
   done = False
   nc = chr(c)
#   log("getunicode: in while nc=%d" % (ord(nc),))
   buf+=nc
   if ord(nc) in (194, 195):
    nc = chr(self.screen.getch())
#    log("getunicode: inside if test, nc%d" % (ord(nc),))
    buf+=nc
#   log("getunicode: in while have buf=%s" % (buf,))
   try:
    tc = buf.decode()
    done = True
   except:
    pass
#   log("getunicode: tc=%s, buf=%s, nc=%d buflen=%d buf[0]=%d" % (tc, buf, ord(nc), len(buf), ord(buf[0])))
   return tc

 def draw(self):
  d=self.ptr,self.currentLine
  log("rl:"+repr(d))
  if self.lastDraw and d==self.lastDraw:
   return
  loc=self.x
  t=self.s
  self.screen.move(self.y,self.x)
  self.screen.clrtoeol()
  if self.s:
   self.screen.addstr(self.y,self.x,self.s)
  t=self.currentLine
  cnt=0
  if self.echo:
   t=str(self.echo)[:1]*len(t)
  self.screen.addstr(self.y,self.startX,"".join(t))
  self.screen.move(self.y,self.startX+self.ptr)
  self.screen.refresh()
#  log("Readline:draw: wrote %d (%s) at %d,%d and moved to %d,%d" % (len(t),t,self.y,self.startX,self.y,self.startX+self.ptr))
  self.lastDraw=self.ptr,self.currentLine

 def handleKey(self,c):
   if c==-1:
    return None
   if c == 3:  # ^C
    self.setStatus("Input aborted!")
    self.currentLine=u''
   elif c == 10:  # ^J newline
    if self.history!=None and self.currentLine:
     self.history.append(self.currentLine)
    self.done=1
   elif c in (1, 262):  # ^A, Home key
    self.ptr=0
   elif c in (5, 360):  # ^E, End key
    self.ptr=len(self.currentLine)
   elif c in (2, 260):  # ^B, left arrow
    if self.ptr>0:
     self.ptr-=1
    else:
     self.beepIfNeeded()
   elif c in (6, 261):  # ^f, right arrow
    if self.ptr<len(self.currentLine):
     self.ptr+=1
    else:
     self.beepIfNeeded()
     self.ptr=len(self.currentLine)
   elif c == 259:  # Up arrow
    if not self.history or self.historyPos==0: #history will return non-zero if it has content
     self.beepIfNeeded()
     msg="No history to move up through." if not self.history else "No previous history to move up through."
     self.setStatus(msg)
    elif self.history and self.historyPos>0:
     self.tempLine=self.currentLine
     self.historyPos-=1
     self.currentLine=self.history[self.historyPos]
     self.ptr=len(self.currentLine)
    else:
     self.setStatus("Something odd occured, readLine, up arrow")
   elif c == 258:  # Down arrow
#if there is no history, or we're off the end of the history list (therefore using tempLine), show an error
    if not self.history or self.historyPos>=len(self.history):
     self.beepIfNeeded()
     msg="No history to move down through." if not self.history else "No more history to move down through."
     self.setStatus(msg)
#otherwise, we've got more history, or tempLine left to view
    elif self.history:
#go ahead and move down
     self.historyPos+=1
#if we're now off the end of the history, pull up tempLine
#maybe user thought they'd typed something and they hadn't, so they can get back to their pre-history command
     if self.historyPos==len(self.history):
      self.currentLine=self.tempLine
#normal history item
     else:
      self.currentLine=self.history[self.historyPos]
#move to the end of this line, history or tempLine
     self.ptr=len(self.currentLine)
    else:
     self.setStatus("Something odd occured, readLine, down arrow")
   elif c == 18:  # ^R Reverse search for Brandon
    self.beepIfNeeded()
    self.setStatus("reverse search not yet implimented")
   elif c in (8, 263):  # ^H, backSpace
    if self.ptr>0:
     self.currentLine=u"%s%s" % (self.currentLine[:self.ptr-1],self.currentLine[self.ptr:])
     self.ptr-=1
    else:
     self.beepIfNeeded()
   elif c in (4, 330):  # ^D, delete
    if self.ptr<len(self.currentLine):
     self.currentLine=u"%s%s" % (self.currentLine[:self.ptr],self.currentLine[self.ptr+1:])
    else:
     self.beepIfNeeded()
   elif c == 331:  # insert
    self.insertMode=False if self.insertMode==True else False
    self.setStatus("insert mode "+"on" if self.insertMode else "off")
   elif c == 21:  # ^U
    self.ptr=0
    self.currentLine=u''
   elif c == 11:  # ^K
    self.currentLine=self.currentLine[:self.ptr]
   elif c == curses.KEY_F2: # value 266 calling all editors
    if self.externalEdit() == None:
     self.setStatus("No system editor found")
    else:
     if self.history!=None and self.currentLine:
      self.history.append(self.currentLine)
     self.done=True
   else:
    if self.readonly:
     self.beepIfNeeded()
     self.setStatus("This is a read only line. Text can not be modified.")
    else:
     uchar=self.getunicode(c)
     if not self.insertMode:
      self.currentLine[self.ptr]=uchar
     else:
      self.currentLine=u"%s%s%s" % (self.currentLine[:self.ptr],uchar,self.currentLine[self.ptr:])
      self.ptr+=1
      if self.maxLength>0 and self.ptr >= self.maxLength:
       if self.history!=None and self.currentLine:
        self.history.append(self.currentLine)
       self.done=True
       self.setStatus("Maximum field length reached.")
   log("Readline:handle: currentLine=%s, c=%s, ptr=%d, maxLength=%d" % (self.currentLine,c,self.ptr,self.maxLength,))
      #handled keystroke
   self.draw()
   return 1

class naEditbox(object):
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
 def __init__(self, screen=None, base=None, y=1, x=0,default="edit field"):
  self.base=base
  self.value=default
  self.win=screen
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
  """Go to the location of the first blank on the given line."""
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

class Listbox(GuiObject):
 """Listbox
render a listbox to the screen in `title \n separator \n items` format
y,x: y and x coordinates where to draw this window on the screen
height: maximum height of this window on the screen, including title and separator
base: base clifox object for accessing settings and other clifox state
default: the index of the currently selected item
title: the title of this select box (might be taken from the element on the webpage)
keysWaitTime: maximum amount of time the system will consider a consecutive set of key-presses as a single search
items: a list of options in string form, or a list of (id,option) tuples
"""
 def __init__(self,screen=None, base=None, y=0, x=0, height=10, title=None, items=[], keysWaitTime=0.4, default=0):
  self.screen=screen
  self.base=base
  self.y,self.x=y,x
  self.title=title
#if we've got a list of strings or a list of non-list objects, turn them into itemIndex,item
#so ["a","b","c"] would become [[0,"a"],[1,"b"],[2,"c"]]
  if items and type(items[0]) not in (tuple,list):
   self.items=zip(xrange(len(items)),items)
  else:
   self.items=items
  self.keys=[]
  self.keysWaitTime=keysWaitTime
  self.height=height
  self.selectedIndex=default
  self.lastDraw=None
  self.draw()

 def draw(self):
  title=self.title
  windowY=self.y
  listHeight=self.height-2
  start=self.selectedIndex//listHeight
  startL=(start*listHeight)
#if startL%lsitHiehgt==0 then we can clear the screen
  endL=(start*listHeight)+listHeight
  sw=windowY+2
  if self.lastDraw!=(startL,endL):
   show=self.items[startL:endL]
   self.screen.move(windowY,0)
   self.screen.clrtoeol()
   self.screen.addstr(windowY,0,title)
   sep='-'*len(title)
   self.screen.move(windowY+1,0)
   self.screen.clrtoeol()
   self.screen.addstr(windowY+1,0,sep)
   for idx,itm in enumerate(show):
    self.screen.move(idx+sw,0)
    self.screen.clrtoeol()
    self.screen.addstr(idx+sw,0,str(itm[1]))
  self.lastDraw=(startL,endL)
  self.screen.move(sw+(self.selectedIndex-startL),0)
#  self.setStatus("%d:%d:%d" % (startL,endL,sw+self.selectedIndex-startL))
  self.screen.refresh()

 def search(self,key):
  t=time.time()
  if key in string.printable and (self.keys and t-self.keys[-1][0]<self.keysWaitTime):
   self.keys.append((t,key))
  else:
   self.keys=[(t,key)]
  keys="".join([i[1] for i in self.keys])
  keys=keys.lower()
  j=-1
  for i in self.items:
   j+=1
   if str(i[1]).lower().startswith(keys):
    self.selectedIndex=j
    break

 def handleKey(self,c):
  if c==-1:
   return None
  if curses.ascii.isprint(c):
   self.search(chr(c))
  elif c==curses.KEY_UP:
   if self.selectedIndex==0:
#we don't want to wrap around to the top
    pass #self.selectedIndex=len(self.items)-1
    self.beepIfNeeded()
   else:
    self.selectedIndex-=1
  elif c==curses.KEY_DOWN:
   if self.selectedIndex==len(self.items)-1:
    pass #self.selectedIndex=0
    self.beepIfNeeded()
   else:
    self.selectedIndex+=1
  elif c in (10, 261): # newline or right arrow
   self.done=1
   return self.selectedIndex
  elif c==260: # left arrow quietly back out
   self.done=1
   return self.selectedIndex
  self.draw()

class FileBrowser(Listbox):
 def __init__(self,screen=None,base=None,y=0,x=0,default="./",title="Browse"):
  self.offset=0
  self.pos=1
  self._dir=""
  self.dir_history={}
  if default:
   self.dir=default if default else os.environ.get("HOME","/")
  self.title=title if title else self.dir
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
