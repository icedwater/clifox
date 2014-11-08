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
  self.initialDraw()

 def initialDraw(self):
  for i in xrange(0,len(self._controls)):
   co=controls[i]
   c=co[0](screen=self.screen,base=self.base,y=i,**co[1])
   self.controls.append(c)
  self.controlIndex=0

 def draw(self):
  for i in self.controls:
   i.draw()

 def handleKey(self,c):
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
   return self.controls[self.controlIndex].handleKey(c)

class Checkbox(GuiObject):
 """checkbox, whose value can be 1 or 0
screen: curses screen object
base:base object
y,x: coordinates for the top left point of this object on screen
prompt: the text shown as the label for this control, set to None if the inPage setting is to be used with text from the current line
"""
 def __init__(self,screen=None,base=None,y=1,x=0,prompt="no prompt",checked=0,):
  self.screen=screen
  self.base=base
  self.y,self.x=y,x
  self.prompt=prompt
  self.draw()

 def draw(self):
  if self.checked>0:
   t="[x] "
  else:
   t="[ ] "
  s="%s %s" % (self.prompt if self.prompt else "",t,)
  self.screen.addstr(self.y,self.x,s)
  self.screen.refresh()

 def keyHandler(self,c):
  log("chkbox:key:",c)
  if c==32:
   self.checked=0 if self.checked==1 else 1
   log("chkbox:draw")
   self.draw()
   return 1
  return 0

class Readline(GuiObject):
 """
prompt for user input, with bindings to that of the default readline implimentation
history: a list of strings which constitutes the previously entered set of strings given to the caller of this function during previous calls
text: the default text, entered as if the user had typed it directly
echo: acts as a mask for passwords (set to ' ' in order to not echo any visible character for passwords)
length: the maximum length for this text entry (element.attr=maxlength is the corresponding html attribute)
delimiter: the delimiter between prompt and text
"""
 def __init__(self,screen=None, base=None, y=1, x=0, history=[], prompt="input",text="",echo=None,length=None,delimiter=":"):
  self.done=0
  self.base=base
  self.screen=screen
  self.y,self.x=y,x
  self.history=history
  self.historyPos=len(self.history) if self.history else 0
  self.text=text
  self.prompt=prompt
  self.delimiter=delimiter
  self.echo=echo
  self.length=length
#prompt and delimiter
  self.s="%s%s" % (self.prompt,self.delimiter,) if self.prompt else ""
#position in the currently-being-editted text
  self.ptr=0
#start of text entry "on-screen", should be greater than self.ptr unless there is absolutely no prompt, (in othe words, a completely blank line)
#if there's a prompt, startX should be right after the prompt and the delimiter
#if not, startX is going to be wherever self.x is, as that's where our text is going to appear
  self.startX=len(self.s) if self.s else self.x
#length between end of prompt, e.g. position of first letter of text, and end of line
#this is how many spaces we actually have to place text on the line
  self.fieldLength=self.screen.getmaxyx()[1]-self.startX
#put ptr at the end of the current bit of text
  self.currentLine=list(self.text)
  self.ptr=len(self.currentLine)
  self.insertMode=True
  self.lastDraw=None
  self.draw()

 def draw(self):
  d=self.ptr,self.currentLine
  if self.lastDraw and d==self.lastDraw:
   return
  self.screen.move(self.y,self.x)
  self.screen.clrtoeol()
  if self.s:
   self.screen.addstr(self.y,self.x,self.s)
  t=self.currentLine
  whereInT=0
#while there's more text to display
#and the position of the cursor is after the next chunk of text that will be skipped
#if our display is five characters long
#our text is abcdefghij
#our cursor is at position 8, or "i"
#we should skipp past abcde
#show fghij
  tempPtr=self.ptr
  log("len(t)",len(t),"fieldLength",self.fieldLength,"ptr",self.ptr,"whereInT+fieldLength",whereInT+self.fieldLength)
  while 1:
   cont=(len(t)>self.fieldLength and self.ptr>(whereInT+self.fieldLength))
   if not cont:
    break
   t=t[self.fieldLength:]
   whereInT+=self.fieldLength
   tempPtr-=self.fieldLength
  t=t[:self.fieldLength]
  if self.echo:
   t=str(self.echo)[:1]*len(t)
  self.screen.addstr(self.y,self.startX,"".join(t))
  self.screen.move(self.y,self.startX+tempPtr)
  self.screen.refresh()
  log("wrote %d (%s) at %d,%d and moved to %d,%d" % (len(t),t,self.y,self.startX,self.y,tempPtr,))
  self.lastDraw=self.ptr,self.currentLine

 def handleKey(self,c):
  if 1:
   if curses.ascii.isprint(c):
    t=chr(c)
    if not self.insertMode:
     self.currentLine[self.ptr]=t
    else:
     self.currentLine.insert(self.ptr,t)
     self.ptr+=1
   elif c == 3:  # ^C
    self.setStatus("Input aborted!")
    self.currentLine=[]
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
     if self.historyPos==len(self.history):
      self.tempLine=self.currentLine
     self.historyPos-=1
     self.currentLine=list(self.history[self.historyPos])
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
      self.currentLine=list(self.history[self.historyPos])
#move to the end of this line, history or tempLine
     self.ptr=len(self.currentLine)
    else:
     self.setStatus("Something odd occured, readLine, down arrow")
   elif c == 18:  # ^R Reverse search for Brandon
    self.beepIfNeeded()
    self.setStatus("reverse search not yet implimented")
   elif c in (8, 263):  # ^H, backSpace
    if self.ptr>0:
     self.currentLine.pop(self.ptr-1)
     self.ptr-=1
    else:
     self.beepIfNeeded()
   elif c in (4, 330):  # ^D, delete
    if self.ptr<len(self.currentLine):
     self.currentLine.pop(self.ptr)
    else:
     self.beepIfNeeded()
   elif c == 331:  # insert
    self.insertMode=False if self.insertMode==True else False
    self.setStatus("insert mode "+"on" if self.insertMode else "off")
   elif c == 21:  # ^U
    self.ptr=0
    self.currentLine=[]
   elif c == 11:  # ^K
    self.currentLine=self.currentLine[:self.ptr]
   else:
    return None
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
 def __init__(self, screen=None, base=None, y=1, x=0,text="edit field"):
  self.base=base
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
 def __init__(self,screen=None,base=None,y=0,x=0,height=10,title=None,values=[],keysWaitTime=0.4):
  self.screen=screen
  self.base=base
  self.y,self.x=y,x
  self.title=title
  if values and type(values[0]) not in (tuple,list):
   self.values=zip(xrange(len(values)),values)
  else:
   self.values=values
  self.keys=[]
  self.keysWaitTime=keysWaitTime
  self.where=0
  self.height=height
  self.draw()

 def draw(self):
  show=self.values[self.where:self.where+self.height]
  for idx,itm in zip(xrange(self.y,self.y+self.height),show):
   self.screen.move(idx,0)
   self.screen.clrtoeol()
   self.screen.addstr(idx,0,str(itm[1]))
  self.screen.move(self.y,0)
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
  for i in self.values:
   j+=1
   if str(i[1]).lower().startswith(keys):
    self.where=j

 def handleKey(self,c):
  if curses.ascii.isprint(c):
   self.search(chr(c))
  elif c==curses.KEY_UP:
   if self.where<=0:
    self.beepIfNeeded()
    self.setStatus("Top of list.")
    self.where=0
   else:
    self.where-=1
  elif c==curses.KEY_DOWN:
   if self.where>=len(self.values):
    self.beepIfNeeded()
    self.setStatus("Bottom of list.")
    self.where=len(self.values)-1
   else:
    self.where+=1
  elif c==10:
   self.done=1
   self.selected=self.values.index(self.values[self.where])
  else:
   return None
  self.draw()
  return 1

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
