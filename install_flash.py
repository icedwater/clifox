#!/usr/bin/python
import urllib,os,sys,json
#osBits is 32 or 64
logName="./ff.installFlash.log"
logEmail="clifox.installFlash@bmcginty.us"
adobeWsUrl="http://get.adobe.com/flashplayer/webservices/json/?platform_type=&platform_dist=&platform_arch=&exclude_version=&browser_arch=&browser_type=&browser_vers=&browser_dist=&eventname=flashplayerotherversions"
def error(e=None,fc=""):
 print """Oops. Adobe's download service appears to have changed.
I'm writing a log to:
%(logName)s
Please email this log to:
$(logEmail)s
It contains the output from uname, which lists your system type, operating system version, and hostname.
It also contains the output from the adobe flash download service.
""" % globals()
 try:
  fh=open(logName,"wb")
 except:
  print "Log file could not be opened. Please make sure your current directory is writable. Exitting."
  sys.exit(2)
 uname=os.uname()
 fh.write("%s\n%s\n%s" % (str(e) if e else "no exception", str(uname) if uname else "no uname given", str(fc) if fc else "no output from ws given",))
 fh.close()
 sys.exit(1)

def main():
 print "Adobe Flash Installer"
 print """This script is considered beta.
Please review this script in your text editor before continuing.
Please press enter to continue.
"""
 try:
  raw_input("Press enter to continue, or control-c to exit.")
  print
 except:
  print
  sys.exit(0)
 osBits=os.uname()[-1]
 osBits="64" if "64" in osBits else "32"
 fh=urllib.urlopen(adobeWsUrl)
 fc=fh.read()
 fh.close()
 fc=fc.decode('iso-8859-2')
 x=json.loads(fc)
 try:
  good=[i for i in x if i['platform']=="Linux"]
  good=[i for i in good if ".tar.gz" in i["download_url"]]
  good=[i for i in good if "-"+osBits in i['installer_architecture']]
 except Exception,e:
  error(e=e,fc=fc)
  sys.exit(1)
 if not good or len(good)>1:
  error(fc=fc)
  sys.exit(1)
 url=good[0]['download_url']
 print "You are running a %s bit system." % (osBits,)
 os.system("mkdir flash_install")
 os.chdir("flash_install")
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

if __name__=='__main__':
 main()

