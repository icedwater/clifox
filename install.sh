#!/bin/bash
root=$(pwd)
echo "warning. this install will remove all saved firefox settings from your profile. This includes all thunderbird messages, firefox favorites, etc. You have ten seconds to cancel this install."
sleep 10
if [ ! -f "./clifox" ]
then
echo "You are not in the root of your source tree. Please change to the top-level directory, containing the clifox binary and the firefox and mozrepl directorys."
exit 0
fi
if [ -d ~/.mozilla/firefox ]
then
rm -Rf ~/.mozilla/firefox
fi
if [ ! -f "./ff/firefox/firefox" ]
then
mkdir ff
cd ff
path="ftp://ftp.mozilla.org/pub/firefox/releases/latest/linux-x86_64/en-US/"
wget --no-remove-listing "$path"
fn=`cat ./.listing | tr '\r' '\n' | rev | cut -d ' ' -f 1 | rev | grep -i bz2`
fullfn="$path$fn"
rm ./*
wget "$fullfn"
bunzip2 *.bz2
tar -xf *.tar
cd ..
fi
ff="./ff/firefox"
if [ ! -f "$ff/firefox" ]
then
echo "firefox binary not found in $ff."
exit 0
fi
echo "creating default profile by running firefox"
timeout 10 xvfb-run "$ff/firefox"
echo "gathering profile paths"
profid=$(ls -1 ~/.mozilla/firefox | grep -i default | head -n1)
profdir=~/.mozilla/firefox/$profid
echo "profile directory:$profdir"
mkdir -p "$profdir/extensions"
echo "overriding prefs.js file"
rm "$profdir/prefs.js"
ln -s "`pwd`/firefox/prefs.js" "$profdir/prefs.js"
echo "linking mozrepl extension from this source path"
ln -s "`pwd`/mozrepl" "$profdir/extensions/mozrepl"
echo "modifying extentions.ini"
python -c "fh=open('$profdir/extensions.ini','rb');fc=fh.read();fh.close();p=fc.find('\n')+1;fc=fc[:p]+'Extension0=$profdir/extensions/mozrepl\n'+fc[p:];fh=open('$profdir/extensions.ini','wb');fh.write(fc);fh.flush();fh.close()"
cp $profdir/extensions.ini $profdir/extensions2.ini
timeout 5 xvfb-run $ff/firefox
cp $profdir/extensions2.ini $profdir/extensions.ini 
touch $profdir/extensions.ini
echo "copying clifox config."
if [ ! -d ~/.clifox ]
then
mkdir ~/.clifox
fi
if [ ! -x ~/.clifox/clifox.conf ]
then
cp "$root/conf/clifox.conf" ~/.clifox/
fi
echo "running firefox. mozrepl should display a message to this console with its listening status."
xvfb-run $ff/firefox

