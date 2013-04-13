import os
def Filename(fn="",root=None):
 if not root:
  root=os.path.expanduser("~/.clifox/")
 return root+fn

logfh=open(Filename("clifox.log"),"wb")
def log(*l):
 global logfh
 l=tuple([str(i) for i in l])
 s=("%s,"*len(l))[:-1]+"\n"
# print s,l
 logfh.write(s % l)
 logfh.flush()

class zeroDict(dict):
 def __getattr__(self,x):
  try:
   return self[x]
  except KeyError:
   return 0

 def __setattr__(self,x,y):
  return self.__setitem__(x,y)

class attrDict(dict):
 def __getattr__(self,key):
  try:
   return self[key]
  except KeyError,e:
   raise AttributeError,e
 def __setattr__(self,key,val):
  z=self[key]=val
  return z
 def __delattr__(self,key):
  try:
   del self[key]
  except KeyError,e:
   raise AttributeError,e
 def __repr__(self):
  return "<AttrDict "+dict.__repr__(self)+">"

if __name__=='__main__':
 if not os.path.exists(Filename()):
  os.makedirs(Filename(""))
