#!/usr/bin/env bash

# This script is to package the Cura package for Windows/Linux and Mac OS X
# This script should run under Linux and Mac OS X, as well as Windows with Cygwin.

#############################
# CONFIGURATION
#############################
export RELEASE_VERSION=2.2.3
export BUILD_VERSION=${RELEASE_VERSION}

##Select the build target
##Available options:
##- windows
##- darwin
##- debian
##- archive

# Second parameter : Select the architecture
# Third parameter (boolean) : must build cura engine ? -> 0 or 1

case "$1" in
	darwin)
		SCRIPTS_DIR=darwin
		OS=Darwin
		BUILD_TARGET=$1
		BUILD_ENGINE=${3:-1}
		CXX=g++
		case "$2" in
		x86)
			BUILD_ARCHITECTURE=x86_64
			;;
		arm64)
			BUILD_ARCHITECTURE=arm64
			;;
		*)
			echo "You need to specify a build architecture."
			echo "Available options:"
			echo "- x86"
			echo "- arm64"
			echo "Command:"
			echo "$0 {target} {architecture}"
			exit 0
			;;
		esac
		;;
	windows)
		SCRIPTS_DIR=windows
		OS=Windows_NT
		BUILD_TARGET=$1
		BUILD_ENGINE=${3:-1}
		case "$2" in
		32)
			BUILD_ARCHITECTURE=x86
			CXX="g++ -m$2"
			;;
		64)
			BUILD_ARCHITECTURE=x64
			CXX="g++ -m$2"
			;;
		*)
			echo "You need to specify a build architecture."
			echo "Available options:"
			echo "- 32"
			echo "- 64"
			echo "Command:"
			echo "$0 {target} {architecture}"
			exit 0
			;;
		esac
		;;
	archive|debian)
		SCRIPTS_DIR=linux
		OS=Linux
		LINUX_TARGET_NAME="curabydago"
		BUILD_ENGINE=${3:-1}
		case "$2" in
		32)
			BUILD_ARCHITECTURE=i386
			BUILD_TARGET=$1_${BUILD_ARCHITECTURE}
			CXX="g++ -m$2"
			;;
		64)
			BUILD_ARCHITECTURE=amd64
			BUILD_TARGET=$1_${BUILD_ARCHITECTURE}
			CXX="g++ -m$2"
			;;
		*)
			echo "You need to specify a build architecture."
			echo "Available options:"
			echo "- 32"
			echo "- 64"
			echo "Command:"
			echo "$0 {target} {architecture}"
			exit 0
			;;
		esac
		;;
	*)
		echo "You need to specify a build target."
		echo "Available options:"
		echo "- windows"
		echo "- darwin"
		echo "- debian"
		echo "- archive"
		echo "Command:"
		echo "$0 {target} {architecture}"
		exit 0
		;;
esac

##Which version name are we appending to the final archive
export BUILD_NAME="CuraByDagoma"

##CuraEngine github repository
CURA_ENGINE_REPO="https://github.com/dagoma3d/CuraEngine.git"

## CuraEngine version to build, default branch
## Four more info, please check https://github.com/dagoma3d/CuraEngine
CURA_ENGINE_VERSION=dagoma

# Change working directory to the directory the script is in
# http://stackoverflow.com/a/246128
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
# double quotes to prevent problems caused by spaces in folder names

#For building under MacOS we need gnutar instead of tar
if [ -z `$(which gnutar 2> /dev/null)` ]; then
	TAR=tar
else
	TAR=gnutar
fi

#############################
# Support functions
#############################
function checkTool
{
	if [ -z "`which $1`" ]; then
		echo "The $1 command must be somewhere in your \$PATH."
		echo "Fix your \$PATH or install $2"
		exit 1
	fi
}

function downloadURL
# some antivirus (avast for example) could block the downloading process
{
	filename=`basename "$1"`
	echo "Checking for $filename"
	if [ ! -f "$filename" ]; then
		echo "Downloading $1"
		curl -L -O "$1"
		if [ $? != 0 ]; then
			echo "Failed to download $1"
			exit 1
		fi
	fi
}

function extract
{
	echo "Extracting $*"
	echo "7z x -y $*" >> log.txt
	7z x -y $* >> log.txt
	if [ $? != 0 ]; then
		echo "Failed to extract $*"
		exit 1
	fi
}

function replaceVars
{
	sed -i "s/<BUILD_VERSION>/${BUILD_VERSION}/g;s/<BUILD_ARCHITECTURE>/${BUILD_ARCHITECTURE}/g" $1
}

# Mandatory tools
checkTool git "git: http://git-scm.com/"
checkTool curl "curl: http://curl.haxx.se/"

if [ $BUILD_ENGINE != "0" ]; then
	# Checkout CuraEngine
	if [ ! -d "CuraEngine" ]; then
		git clone ${CURA_ENGINE_REPO}
		if [ $? != 0 ]; then echo "Failed to clone CuraEngine"; exit 1; fi
	fi

	# Build CuraEngine
	#cd CuraEngine
	#git checkout ${CURA_ENGINE_VERSION}
	#cd ..
	cd CuraEngine
	git checkout dagoma
	git pull
	cd ..
	make -C CuraEngine clean
	make -C CuraEngine VERSION=${CURA_ENGINE_VERSION} OS=${OS} ARCH=${BUILD_ARCHITECTURE} CXX="${CXX}"
	if [ $? != 0 ]; then echo "Failed to build CuraEngine"; exit 1; fi
fi

#############################
# Darwin
#############################
if [[ $BUILD_TARGET == darwin ]]; then
	#mkvirtualenv Cura

	rm -rf scripts/darwin/build
	rm -rf scripts/darwin/dist

	#python build_app.py py2app --packages=wx
	#python build_app.py py2app
	python setup.py py2app
	rc=$?
	if [[ $rc != 0 ]]; then
		echo "Cannot build app."
		exit 1
	fi

	#Add cura version file (should read the version from the bundle with pyobjc, but will figure that out later)
	echo $BUILD_NAME > scripts/darwin/dist/${BUILD_NAME}.app/Contents/Resources/version
	touch scripts/darwin/dist/${BUILD_NAME}.app/Contents/Resources/new

	#Copy CuraEngine
	#cp CuraEngine/build/CuraEngine scripts/darwin/dist/${BUILD_NAME}.app/Contents/Resources/CuraEngine

	cd scripts/darwin

	# Archive app
	cd dist
	gnutar cfp - ${BUILD_NAME}.app | gzip --best -c > ../../../${BUILD_NAME}.tar.gz
	cd ..

	# Create sparse image for distribution
	hdiutil detach /Volumes/${BUILD_NAME}/ || true
	rm -rf ${BUILD_NAME}.dmg.sparseimage
	echo 'convert'
	hdiutil convert DmgTemplateCompressed.dmg -format UDSP -o ${BUILD_NAME}.dmg
	echo 'resize'
	hdiutil resize -size 500m ${BUILD_NAME}.dmg.sparseimage
	echo 'attach'
	hdiutil attach ${BUILD_NAME}.dmg.sparseimage
	echo 'cp'
	cp -a dist/${BUILD_NAME}.app /Volumes/${BUILD_NAME}/
	echo 'detach'
	hdiutil detach /Volumes/${BUILD_NAME}
	echo 'convert'
	hdiutil convert ${BUILD_NAME}.dmg.sparseimage -format UDZO -imagekey zlib-level=9 -ov -o ../../${BUILD_NAME}_${BUILD_ARCHITECTURE}.dmg

	cd ../..
	zip ${BUILD_NAME}_${BUILD_ARCHITECTURE}.dmg.zip ${BUILD_NAME}_${BUILD_ARCHITECTURE}.dmg

	if [ ! -d "packages" ]; then
		mkdir packages
	fi
	mv -f ${BUILD_NAME}_${BUILD_ARCHITECTURE}.dmg ./packages/

	if [ ! -d "dist" ]; then
		mkdir dist
	fi
	mv -f ${BUILD_NAME}_${BUILD_ARCHITECTURE}.dmg.zip ./dist/

	exit
fi

#############################
# Debian
#############################
if [[ $BUILD_TARGET == debian* ]]; then
	mkdir -p scripts/linux/${BUILD_TARGET}
	sudo chown $USER:$USER scripts/linux/${BUILD_TARGET} -R
	rm -rf scripts/linux/${BUILD_TARGET}/usr/share
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}
	cp -a Cura scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/
	cp -a resources scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/
	cp -a plugins scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/
	cp -a CuraEngine/build/CuraEngine scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/
	cp scripts/linux/utils/cura.py scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/
	replaceVars scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/cura.py
	echo $BUILD_NAME > scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/Cura/version
	rm -rf scripts/linux/${BUILD_TARGET}/usr/share/applications
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/share/applications
	cp scripts/linux/utils/curabydago.desktop scripts/linux/${BUILD_TARGET}/usr/share/applications/${LINUX_TARGET_NAME}.desktop
	replaceVars scripts/linux/${BUILD_TARGET}/usr/share/applications/${LINUX_TARGET_NAME}.desktop
	rm -rf scripts/linux/${BUILD_TARGET}/usr/bin
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/bin
	cp scripts/linux/utils/debian/curabydago scripts/linux/${BUILD_TARGET}/usr/bin/${LINUX_TARGET_NAME}
	replaceVars scripts/linux/${BUILD_TARGET}/usr/bin/${LINUX_TARGET_NAME}
	cp -a scripts/linux/utils/debian/DEBIAN scripts/linux/${BUILD_TARGET}/
	replaceVars scripts/linux/${BUILD_TARGET}/DEBIAN/control
	replaceVars scripts/linux/${BUILD_TARGET}/DEBIAN/postinst
	sudo chown root:root scripts/linux/${BUILD_TARGET} -R
	sudo chmod 755 scripts/linux/${BUILD_TARGET}/usr -R
	sudo chmod 755 scripts/linux/${BUILD_TARGET}/DEBIAN -R
	cd scripts/linux
	sudo dpkg-deb --build ${BUILD_TARGET} $(dirname ${BUILD_NAME})/${BUILD_NAME}_${BUILD_ARCHITECTURE}.deb
	sudo chown $USER:$USER ${BUILD_TARGET} -R
	cp ./utils/debian/README.md .
	replaceVars README.md
	zip ${BUILD_NAME}_${BUILD_ARCHITECTURE}.deb.zip ${BUILD_NAME}_${BUILD_ARCHITECTURE}.deb README.md
	rm README.md

	cd ../..
	if [ ! -d "packages" ]; then
		mkdir packages
	fi
	mv -f scripts/linux/${BUILD_NAME}_${BUILD_ARCHITECTURE}.deb ./packages/

	if [ ! -d "dist" ]; then
		mkdir dist
	fi
	mv -f scripts/linux/${BUILD_NAME}_${BUILD_ARCHITECTURE}.deb.zip ./dist/

	exit
fi

#############################
# Archive .tar.gz
#############################
if [[ $BUILD_TARGET == archive* ]]; then
	mkdir -p scripts/linux/${BUILD_TARGET}
	rm -rf scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}
	mkdir -p scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}
	cp -a Cura scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/
	cp -a resources scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/
	cp -a plugins scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/
	cp -a CuraEngine/build/CuraEngine scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/
	cp scripts/linux/utils/cura.py scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/
	replaceVars scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/cura.py
	echo $BUILD_NAME > scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/Cura/version
	cp scripts/linux/utils/curabydago.desktop scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}.desktop
	replaceVars scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}.desktop
	cp scripts/linux/utils/archive/README.md scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/README.md
	replaceVars scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/README.md
	cd scripts/linux/${BUILD_TARGET}
	tar -czvf ${BUILD_NAME}_${BUILD_ARCHITECTURE}.tar.gz ${BUILD_NAME}-${BUILD_TARGET}
	mv ${BUILD_NAME}_${BUILD_ARCHITECTURE}.tar.gz ../
	cd ..
	zip ${BUILD_NAME}_${BUILD_ARCHITECTURE}.tar.gz.zip ${BUILD_NAME}_${BUILD_ARCHITECTURE}.tar.gz

	cd ../..
	if [ ! -d "packages" ]; then
		mkdir packages
	fi
	mv -f scripts/linux/${BUILD_NAME}_${BUILD_ARCHITECTURE}.tar.gz ./packages/

	if [ ! -d "dist" ]; then
		mkdir dist
	fi
	mv -f scripts/linux/${BUILD_NAME}_${BUILD_ARCHITECTURE}.tar.gz.zip ./dist/

	exit
fi

#############################
# Download all needed files.
#############################
if [[ $BUILD_TARGET == windows ]]; then
	##Which versions of external programs to use
	WIN_PORTABLE_PY_VERSION=3.2.5.1
	#Check if we have 7zip, needed to extract and packup a bunch of packages for windows.
	checkTool 7z "7zip: http://www.7-zip.org/"
	checkTool mingw32-make "mingw: http://www.mingw.org/"

	downloadURL http://www.uwe-sieber.de/files/ejectmedia.zip

	#############################
	# Build the packages
	#############################
	rm -rf ${BUILD_NAME}
	mkdir -p ${BUILD_NAME}
	rm -f log.txt

	#Add winPython
	if [ $BUILD_ARCHITECTURE == "x86" ]; then
		cp -r python-3.9.10 ${BUILD_NAME}/python3
	else
		cp -r python-3.9.10.amd64 ${BUILD_NAME}/python3
	fi
	echo "Step winPython Finished"

	#For windows extract ejectmedia python to include it.
	extract ejectmedia.zip Win32
	mkdir -p ${BUILD_NAME}/Cura/
	mv Win32/EjectMedia.exe ${BUILD_NAME}/Cura/
	rm -rf Win32
	echo "Step ejectmedia Finished"

	#Add Cura
	mkdir -p ${BUILD_NAME}/Cura ${BUILD_NAME}/resources ${BUILD_NAME}/plugins
	cp -a Cura/* ${BUILD_NAME}/Cura
	cp -a resources/* ${BUILD_NAME}/resources
	cp -a plugins/* ${BUILD_NAME}/plugins
	#Add cura version file
	echo $BUILD_NAME > ${BUILD_NAME}/Cura/version
	echo "Step add cura Finished"

	#package the result
	cp -a scripts/${BUILD_TARGET}/*.bat $BUILD_NAME/
	cp CuraEngine/build/CuraEngine.exe $BUILD_NAME
	# The following lines are used if CuraEngine is not compiled as static executable.
	#cp C:\mingw64\i686-7.2.0-release-posix-sjlj-rt_v5-rev0\mingw32\bin\libgcc_s_sjlj-1.dll $BUILD_NAME
	#cp C:\mingw64\i686-7.2.0-release-posix-sjlj-rt_v5-rev0\mingw32\bin\libwinpthread-1.dll $BUILD_NAME
	#cp C:\mingw64\i686-7.2.0-release-posix-sjlj-rt_v5-rev0\mingw32\bin\libstdc++-6.dll $BUILD_NAME
	echo "Step add scripts and executables Finished"

	if [ -f '/c/Program Files (x86)/NSIS/makensis.exe' ]; then
		rm -rf scripts/windows/dist
		mv "`pwd`/${BUILD_NAME}" scripts/windows/dist
		echo ${BUILD_NAME}
		'/c/Program Files (x86)/NSIS/makensis.exe' -DBUILD_NAME=${BUILD_NAME} -DBUILD_VERSION=${BUILD_VERSION} -DBUILD_ARCHITECTURE=${BUILD_ARCHITECTURE} 'scripts/windows/installer.nsi' >> log.txt
		if [ $? != 0 ]; then echo "Failed to package NSIS installer"; exit 1; fi
		mv scripts/windows/${BUILD_NAME}.exe ./
		if [ $? != 0 ]; then echo "Can't Move Frome scripts/windows/...exe"; fi
		mv ./${BUILD_NAME}.exe ./${BUILD_NAME}_${BUILD_ARCHITECTURE}.exe
		if [ $? != 0 ]; then echo "Can't Move Frome ./ to ./${BUILD_NAME}.exe"; exit 1; fi

		7z a -y ${BUILD_NAME}_${BUILD_ARCHITECTURE}.exe.zip ${BUILD_NAME}_${BUILD_ARCHITECTURE}.exe

		if [ ! -d "packages" ]; then
			mkdir packages
		fi
		mv -f ${BUILD_NAME}_${BUILD_ARCHITECTURE}.exe ./packages/

		if [ ! -d "dist" ]; then
			mkdir dist
		fi
		mv -f ${BUILD_NAME}_${BUILD_ARCHITECTURE}.exe.zip ./dist/
		echo 'Good Job, All Works Well !!! :)'
	else
		echo "No makensis"
	fi

	exit
fi
