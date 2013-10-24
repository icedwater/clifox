#!/bin/bash
root=$(pwd)
arch=$(uname -m)
ffpath="./ff/firefox"
read -t10 -p "warning. this install will remove all saved firefox settings from your profile. This includes all thunderbird messages, firefox favorites, etc. You have ten seconds to cancel this install.
continue (c-c to abort):"
if [ ! -f "./clifox" ]
then
echo "You are not in the root of your source tree. Please change to the top-level directory, containing the clifox binary and the firefox and mozrepl directorys."
exit 0
fi
if [ -d ~/.mozilla/firefox ]
then
rm -Rf ~/.mozilla/firefox
fi
if [[ $1 == "beta" ]]
then
mkdir -p ff/nightly
cd ff/nightly
if [ ! -f "firefox.nightly.tar.bz2" ]
then
path=$(wget -q -O- "http://nightly.mozilla.org/" | python -c 'import sys,re;print "\n".join(re.findall(r"\"(.*://.*bz2)\"",sys.stdin.read()))' | grep -i $(uname -m))
wget -q -O "firefox.nightly.tar.bz2" "$path"
fi
bzcat firefox.nightly.tar.bz2 | tar -xf -
ffpath="./ff/nightly/firefox"
cd ../..
else
if [ ! -f "$ffpath/firefox" ]
then
mkdir ff
cd ff
tf=$(ls -1 *.tar | grep -i tar)
if [ $? != 0 ]
then
path="ftp://ftp.mozilla.org/pub/firefox/releases/latest/linux-$arch/en-US/"
wget --no-remove-listing "$path"
fn=`cat ./.listing | tr '\r' '\n' | rev | cut -d ' ' -f 1 | rev | grep -i bz2`
rm "./.listing"
fullfn="$path$fn"
rm ./*
wget "$fullfn"
bunzip2 *.bz2
fi
tar -xf *.tar
if [ $? != 0 ]
then
rm *.tar
echo "error untarring firefox. deleting current firefox installation archives. You can attempt to rerun install.sh to redownload and retry."
exit 1
fi
cd ..
fi
fi
if [ ! -f "$ffpath/firefox" ]
then
echo "firefox binary not found in $ffpath.
Perhaps your architecture, $arch, is not supported."
exit 1
fi
echo "creating default profile by running firefox"
ret=$(timeout 10 xvfb-run "$ffpath/firefox")
retcode=$?
if [ $retcode != 124 ]
then
echo "An error occured. You might be already running a copy of xvfb, or you might have a stale X11 .lock file in your /tmp directory.
If you want to be sure, kill all processes with xvfb in the name, and clear your /tmp directory.
You can also run this installer with the environment variable NUM, set to a number lower than the current number.
Displayed text was:
$ret"
exit 1
fi
echo "gathering profile paths"
profid=$(ls -1 ~/.mozilla/firefox | grep -i default | head -n1)
profdir=~/.mozilla/firefox/$profid
echo "profile directory:$profdir"
mkdir -p "$profdir/extensions"
echo "overriding user.js file"
if [ -f "$profdir/user.js" ]
then
rm "$profdir/user.js"
fi
ln -s "`pwd`/firefox/user.js" "$profdir/user.js"
echo "linking mozrepl extension from this source path"
ln -s "`pwd`/mozrepl" "$profdir/extensions/mozrepl"
if [ -f "$profdir/prefs.js" ]
then
echo "removing prefs.js"
rm "$profdir/prefs.js"
fi
echo "modifying extentions.ini"
if [ ! -f "$profdir/extensions.ini" ]
then
echo "" > $profdir/extensions.ini
else
python -c "fh=open('$profdir/extensions.ini','rb');fc=fh.read();fh.close();p=fc.find('\n')+1;fc=fc[:p]+'Extension0=$profdir/extensions/mozrepl\n'+fc[p:];fh=open('$profdir/extensions.ini','wb');fh.write(fc);fh.flush();fh.close()"
fi
ret=$(timeout 5 xvfb-run $ffpath/firefox)
retcode=$?
if [ $retcode != 124 ]
then
echo "An error occured.
Firefox could not be run after the modification to extensions.ini.
Displayed text was:
$ret"
exit 1
fi
#mv $profdir/extensions2.ini $profdir/extensions.ini 
#touch $profdir/extensions.ini
echo "copying clifox config."
if [ ! -d ~/.clifox ]
then
mkdir ~/.clifox
fi
if [ ! -x ~/.clifox/clifox.conf ]
then
cp "$root/conf/clifox.conf" ~/.clifox/
fi
echo "running firefox. mozrepl should display a message to this console with its listening status.
You can leave firefox running in the background, or c-c this copy and run it in another terminal."
xvfb-run $ffpath/firefox

