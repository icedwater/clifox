.phoney: dev dev2
dev:
	@echo "setting up development environment"
	@echo "the addon sdk for extension development will be downloaded, and symlinked into your \"$${HOME}/bin\" directory"
	@if [ ! -d "devEnvironment" ]; then mkdir devEnvironment; fi
	@make --no-print-directory -f ../Makefile -C devEnvironment dev2
dev2:
	@if [ ! -f "addonsdk.tgz" ];\
	then echo "downloading addon sdk";\
	wget -c -Oaddonsdk.tgz "https://ftp.mozilla.org/pub/mozilla.org/labs/jetpack/jetpack-sdk-latest.tar.gz";\
	fi
	@if [ ! -d "addonsdk" ];\
	then echo "extracting addonsdk.tgz";\
	tar -xzf "addonsdk.tgz";\
	newname="$$(ls -1 | grep -vi tgz | head -n1)";\
	echo "renaming $${newname} to addonsdk";\
	mv "$${newname}" "addonsdk";\
	fi
#	@rm addonsdk.tgz
	@if [ -e "$${HOME}/bin" ];\
	then if [ -e "$$HOME/bin/cfx" ];\
	then echo "removing current cfx symlink";\
	rm "$$HOME/bin/cfx";\
	fi;\
	echo "symlinking cfx to $$HOME/bin";\
	ln -s "`pwd`/addonsdk/bin/cfx" "$${HOME}/bin/cfx";\
	else echo "$${HOME}/bin directory does not exist. Please place \"`pwd`/addonsdk/bin\" into your path";\
	fi
