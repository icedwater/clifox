#!/bin/bash
if [ ! -f "./clifox" ]
then
echo "You are not in the root of your source tree. Please change to the top-level directory, containing the clifox binary and the firefox and mozrepl directorys."
exit 0
fi
echo "enter directory holding your firefox binarys. This directory should contain firefox and firefox-bin."
echo -n "FFBin:"
read ff
if [ ! -f "$ff/firefox" ]
then
echo "firefox binary not found in $ff."
exit 0
fi
echo "creating default profile by running firefox"
timeout 10 xvfb-run "$ff/firefox"
echo "athering profile paths"
profid=$(ls -1 ~/.mozilla/firefox | grep -i default | head -n1)
profdir=~/.mozilla/firefox/$profid
echo "profile directory:$profdir"
mkdir -p "$profdir/extensions"
echo "overriding prefs.js file"
rm "$profdir/prefs.js"
ln -s "`pwd`/firefox/prefs.js" "$profdir/prefs.js"
echo "linking mozrepl extension from this source path"
ln -s "`pwd`/mozrepl" "$profdir/extensions/mozrepl"
python -c "fc=open('$profdir/extensions.ini','rb').read();p=fc.find('\n')+1;fc=fc[:p]+'Extension0=$profdir/extensions/mozrepl\n'+fc[p:];open('$profdir/extensions.ini','wb').write(fc)"
echo "running firefox. mozrepl should display a message to this console with its listening status."
xvfb-run $ff/firefox

