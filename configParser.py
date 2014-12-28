import os,os.path,utils,curses
config=utils.attrDict()

def defaultConfig():
 config=utils.attrDict()
#replace with parser for name.x.y.z=value, resolvable with config.name.x.y.z
#set dom to parse js
 config.logging=1
 config.homepage="http://www.bmcginty.hopto.org/form.html"
 config.pagePosition="percentage"
 config.caseSensitiveSearch="false"
 config.showInstantPage=0
 config.dbg=0
 config.mainWindowKeys={
ord("`"):"self.nextWindow()",
ord("q"):"self.quit()",
ord("\n"):"self.execute()",
curses.KEY_DOWN:"self.nextLine()",
curses.KEY_UP:"self.prevLine()",
curses.KEY_RIGHT:"self.nextChar()",
curses.KEY_LEFT:"self.prevChar()"
}
 return config

if os.path.exists('/etc/wb.conf'): execfile('/etc/wb.conf')
if os.path.exists('./wb.conf'): execfile('./wb.conf')
if os.path.exists(os.path.expanduser('~/.wb/wb.conf')):
 execfile(os.path.expanduser('~/.wb/wb.conf'))
if not os.path.exists(os.path.expanduser('~/.clifox/')):
 os.mkdir(os.path.expanduser('~/.clifox'))
if os.path.exists(os.path.expanduser('~/.clifox/clifox.conf')):
 execfile(os.path.expanduser('~/.clifox/clifox.conf'))
dc=defaultConfig()
for k in dc:
 if k not in config:
  config[k]=dc[k]
