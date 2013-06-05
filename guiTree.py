import os,os.path,sys,curses,time
#treeview for ncurses
#subclass as shown below in the fileTreeview impl.

class treeview(object):
 space=" "*200
#uncomment the below open statement and comment the below return statement to enable logging again
# log=open("/tmp/tree","wb")
 def l(self,*a):
  return
#  [self.log.write(str(i)+"\n") for i in a]
#  self.log.flush()

 def __init__(self,nodes):
  self.screen=None
  self.list=[]
  self.nodes=nodes
  self.paths=[]
  self.levels={}
  self.states={}
  self.curIndex=0
  self.cur=self.nodes[0]
  self.level=0
  [self.list.insert(0,i) for i in self.nodes[::-1]]
  [self.states.__setitem__(i,0) for i in self.nodes]
  [self.levels.__setitem__(i,0) for i in self.list]
  self.l("cur:",self.cur)

 def down(self):
  self.l("down:","curIndex:",self.curIndex)
  if self.curIndex+1>=len(self.list):
   return 1
  self.curIndex+=1
  self.cur=self.list[self.curIndex]
  self.level=self.levels[self.cur]
  self.show()
#  self.screen.move(self.screen.getyx()[0]+1,0)

 def up(self):
  self.l("up:","curIndex:",self.curIndex)
  if self.curIndex<=0:
   return 1
  self.curIndex-=1
  self.cur=self.list[self.curIndex]
  self.level=self.levels[self.cur]
  self.show()

 def markCollapsed(self,root):
  i=self.list.index(root)+1
  level=self.levels[root]+1
  while i<len(self.list):
   self.l("markCollapsed:","i:",i,"listI:",self.list[i],"level:",self.levels[self.list[i]])
   if self.levels.get(self.list[i],level)<level:
    break
   self.collapseFunc(self.list[i])
   self.states[self.list[i]]=0
   i+=1
  return i

 def collapse(self):
  self.l("collapse:","cur:",self.cur,"canCollapse:",self.canCollapse(self.cur),"state:",self.states[self.cur])
  if self.canCollapse(self.cur) and self.states.get(self.cur,1)==1:
   newIndex=self.markCollapsed(self.cur)
   rem=[self.list.pop(self.curIndex+1) for i in xrange(self.curIndex+1,newIndex)]
   rem.insert(0,self.cur)
   self.collapseFunc(rem)
   self.states[self.cur]=0
   self.l("collapsed:"+str(self.cur)+" list:"+str(self.list))
   self.show()

 def expand(self):
  self.l("expand:","curIndex:",self.curIndex,"cur:",self.cur,"canExpand:",self.canExpand(self.cur),"state:",self.states[self.cur])
  if self.canExpand(self.cur) and self.states.get(self.cur,0)==0:
   new=self.expandFunc(self.cur)
   self.states[self.cur]=1
   [self.list.insert(self.curIndex+1,i) for i in new[::-1]]
   [self.states.__setitem__(i,0) for i in new]
   [self.levels.__setitem__(i,self.level+1) for i in new]
   self.show()

 def show(self):
  where=self.curIndex
  half=self.maxy/2
  if half%2==0: half-=1
  start=0 if self.curIndex<half else self.curIndex-half
  end=start+self.maxy
#  self.screen.addstr(0,0,str(self.list)[:self.maxx])
  line=1
  mt=1
  for i in xrange(start,min(len(self.list),end)):
   item=self.list[i]
   txt=item[0]
   lvl=self.levels[item]
   txt=" "*lvl+txt[:self.maxx-lvl]
   self.screen.move(line,0)
   self.screen.clrtoeol()
   self.screen.chgat(line,0,-1,curses.A_NORMAL)
   self.screen.addstr(line,0,txt)
   if i==self.curIndex: mt=line
   line+=1
  while line<self.maxy:
   self.screen.move(line,0)
   self.screen.chgat(line,0,-1,curses.A_NORMAL)
   self.screen.clrtoeol()
   line+=1
  self.screen.move(mt,0)
  self.screen.chgat(mt,0,-1,curses.A_REVERSE)
  self.screen.touchwin()
  self.screen.refresh()

 def __call__(self, screen):
  self.screen = screen
  curses.def_shell_mode()
  self.screen.nodelay(1)
  self.screen.keypad(1)
  curses.raw(1)
  curses.noecho()
  self.maxy,self.maxx=self.screen.getmaxyx()
  self.screen.addstr(self.maxy-1,0,"-"*(self.maxx-2))
  self.maxy-=2
  self.maxx-=1
  self.show()
  while 1:
   time.sleep(0.001)
   k=self.screen.getch()
#we're using nodelay, so -1 means no keystroke.
   if k==-1:
    continue
#each time a key is pressed, it should be shown here.
#write spaces to top line of window for clear line
   if k==ord('q'):
    sys.exit()
   if k==curses.KEY_LEFT:
    self.collapse()
   if k==curses.KEY_RIGHT:
    self.expand()
   if k==curses.KEY_UP:
    self.up()
   if k==curses.KEY_DOWN:
    self.down()
   if k in (curses.KEY_ENTER,10):
    pass #return self.cur
#   self.show()
   continue

class fileTreeview(treeview):
 def canExpand(self,i):
  return os.path.isdir(i[1])

 def canCollapse(self,x):
  return os.path.isdir(x[1])
#self.canCollapse(x)

 def expandFunc(self,x):
  return [(i.rsplit("/",1)[-1]+"/" if self.canExpand(('',i)) else i.rsplit("/",1)[-1],x[1].rstrip("/")+"/"+i) for i in os.listdir(x[1])]

 def collapseFunc(self,i):
  return

class nodeTreeview(treeview):
 def canExpand(self,x):
  return 1 if dir(x[1]) else 0

 def canCollapse(self,x):
  return self.canExpand(x)

 def expandFunc(self,x):
  ret=[]
  obj=x[1]
  for i in dir(obj):
   try:
    ret.append(("%s=%s" % (i,str(getattr(obj,i,"null")),),getattr(obj,i)))
   except:
    ret.append(("%s=error" % (i,)))
  ret.sort()
  return ret

 def collapseFunc(self,x):
  pass

if __name__=='__main__':
 #text,obj
 import curses
 t=fileTreeview([("/","/")])
 curses.wrapper(t)

