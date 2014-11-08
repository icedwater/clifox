import Queue,sys
import mozCom
hostname="localhost"
a=mozCom.initCliFox(hostname=hostname if len(sys.argv)<2 else sys.argv[1],q=Queue.Queue())
#print a
root,q=a
#print root.ref.eval("z=clifox.listAllTabs()[0];zz=clifox.selectTab(z);zz.toString()")
#print root.clifox.selectTab,root.z,root.zz
#print root.clifox.map['j3'].value.toString()
#print root.ref.eval('clifox.map["j4"].name')
#print root.clifox.selectTab(root.z)
#print root.ref.eval("clifox.map.toString();for(i in clifox.map){i;};")
print root.ref.eval(sys.argv[2])
sys.exit(0)
l=[i for i in root.clifox.listAllTabs()]
print l[0],l[0]['$clifox'],l[0].ref.id
print root.ref.root.ref.map.keys()
sys.exit(0)
for i in xrange(5):
 print dir(root)
 print root.clifox
 #print dir(root)
 print "dir",dir(root.clifox)
 print "functionToString",root.clifox.mapNewId.toString()
 print "function",root.clifox.mapNewId
 print "mapNewIdPropper",root.clifox.mapNewId()
 print "mapNewIdEvalPropper",root.ref.eval("clifox.mapNewId()");

