#!/usr/bin/python
import urllib,os,sys
print "Adobe Flash Installer"
print """This script is considered beta.
Please press enter to continue.
Please review this script in your text editor before continuing.
"""
try:
 raw_input("Press enter to continue, or control-c to exit.")
 print
except:
 print
 sys.exit(0)
adobe_url="http://get.adobe.com/flashplayer/completion/?installer=Flash_Player_11.2_for_other_Linux_(.tar.gz)_%d-bit"
rel=os.uname()[-1]
rel=64 if "64" in rel else 32
print "You are running %d-bit linux." % (rel,)
os.system("mkdir flash_install")
os.chdir("flash_install")
fc=urllib.urlopen(adobe_url % (rel,)).read()
url=fc[fc.find("location.href"):].split("'",1)[1].split("'",1)[0]
print "Retrieving \"%s\"" % (url,)
os.system('wget -q -c -Oflash.tar.gz "%s"' % (url,))
print "extracting flash.tar.gz"
os.system("mkdir flash")
os.chdir("flash")
os.system("tar -xzf ../flash.tar.gz")
print "removing unneeded files"
os.system("rm ./*.txt")
print "creating plugins directory"
os.system("mkdir ~/.mozilla/plugins")
print "copying shared library to ~/.mozilla.plugins"
os.system("mv *.so ~/.mozilla/plugins")
cmd="sudo cp -R ./usr/* /usr/"
print("""Now, the command:
"""+cmd+"""
will be run. You can exit this wizard and run the command yourself by pressing C-C.
Files to repeat this installation can be found in
`./flash_install/`""")
os.system(cmd)
os.chdir("../../")

