#!/usr/bin/env bash

# This script is to package the Cura package for Windows/Linux and Mac OS X
# This script should run under Linux and Mac OS X, as well as Windows with Cygwin.

#############################
# CONFIGURATION
#############################
export BUILD_VERSION=1.0.7

##Select the printer name
##Available options:
##- discoeasy200
##- explorer350
##- neva
case "$1" in
	discoeasy200)
		export MACHINE_NAME="Easy200"
		MACHINE_NAME_LOWERCASE="easy200"
		;;
	explorer350)
		export MACHINE_NAME="Explorer350"
		MACHINE_NAME_LOWERCASE="explorer350"
		;;
	neva)
		export MACHINE_NAME="Neva"
		MACHINE_NAME_LOWERCASE="neva"
		;;
	*)
		echo "You need to specify a printer name."
		echo "Available options:"
		echo "- discoeasy200"
		echo "- explorer350"
		echo "- neva"
		echo "Command:"
		echo "$0 {printer_name} {target} {architecture}"
		exit 0
		;;
esac

##Select the build target
##Available options:
##- win32
##- darwin
##- debian
##- archive
case "$2" in
	darwin)
		SCRIPTS_DIR=darwin
		OS=Darwin
		BUILD_TARGET=$2
		CXX=g++
		;;
	win32)
		SCRIPTS_DIR=win32
		OS=Windows_NT
		BUILD_TARGET=$2
		CXX=g++
		export LDFLAGS=--static
		;;
	archive|debian)
		SCRIPTS_DIR=linux
		OS=Linux
		LINUX_TARGET_NAME="curabydago-"${MACHINE_NAME_LOWERCASE}
		case "$3" in
		32)
			BUILD_TARGET=$2_i386
			CXX="g++ -m$3"
			;;
		64)
			BUILD_TARGET=$2_amd64
			CXX="g++ -m$3"
			;;
		*)
			echo "You need to specify a build architecture."
			echo "Available options:"
			echo "- 32"
			echo "- 64"
			echo "Command:"
			echo "$0 {printer_name} {target} {architecture}"
			exit 0
			;;
		esac
		;;
	*)
		echo "You need to specify a build target."
		echo "Available options:"
		echo "- win32"
		echo "- darwin"
		echo "- debian"
		echo "- archive"
		echo "Command:"
		echo "$0 {printer_name} {target} {architecture}"
		exit 0
		;;
esac

# Remove config files and add them according to the printer name.
echo "Copying specific ${MACHINE_NAME} resources..."
cp -a ./configuration/${MACHINE_NAME_LOWERCASE}/resources .
echo "Copying specific ${MACHINE_NAME} plugins..."
rm -rf ./plugins
cp -a ./configuration/${MACHINE_NAME_LOWERCASE}/plugins .
echo "Copying specific ${MACHINE_NAME} scripts..."
rm -rf ./scripts/${SCRIPTS_DIR}
cp -a ./configuration/${MACHINE_NAME_LOWERCASE}/scripts/${SCRIPTS_DIR} ./scripts/

##Which version name are we appending to the final archive
export BUILD_NAME="Cura-by-Dagoma-"${MACHINE_NAME}
BUILD_NAME_INSTALL="Cura_by_Dagoma_"${MACHINE_NAME}

##CuraEngine github repository
CURA_ENGINE_REPO="https://github.com/Ultimaker/CuraEngine"

## CuraEngine version to build
## Four more info, please check https://github.com/daid/LegacyCura/blob/SteamEngine/package.sh
CURA_ENGINE_VERSION=legacy

# Change working directory to the directory the script is in
# http://stackoverflow.com/a/246128
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPT_DIR

#For building under MacOS we need gnutar instead of tar
if [ -z `which gnutar` ]; then
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

# Mandatory tools
checkTool git "git: http://git-scm.com/"
checkTool curl "curl: http://curl.haxx.se/"

# Checkout CuraEngine
if [ ! -d "CuraEngine" ]; then
	git clone ${CURA_ENGINE_REPO}
	if [ $? != 0 ]; then echo "Failed to clone CuraEngine"; exit 1; fi
fi

# Build CuraEngine
cd CuraEngine
git checkout ${CURA_ENGINE_VERSION}
cd ..
make -C CuraEngine clean
make -C CuraEngine VERSION=${CURA_ENGINE_VERSION} OS=${OS} CXX="${CXX}"
if [ $? != 0 ]; then echo "Failed to build CuraEngine"; exit 1; fi

#############################
# Darwin
#############################
if [[ $BUILD_TARGET == darwin ]]; then
	#mkvirtualenv Cura

	rm -rf scripts/darwin/build
	rm -rf scripts/darwin/dist

	python build_app.py py2app
	rc=$?
	if [[ $rc != 0 ]]; then
		echo "Cannot build app."
		exit 1
	fi

	#Add cura version file (should read the version from the bundle with pyobjc, but will figure that out later)
	echo $BUILD_NAME > scripts/darwin/dist/${BUILD_NAME}.app/Contents/Resources/version

	#Copy CuraEngine
	cp CuraEngine/build/CuraEngine scripts/darwin/dist/${BUILD_NAME}.app/Contents/Resources/CuraEngine

	cd scripts/darwin

	# Install QuickLook plugin
	mkdir -p dist/${BUILD_NAME}.app/Contents/Library/QuickLook
	cp -a STLQuickLook.qlgenerator dist/${BUILD_NAME}.app/Contents/Library/QuickLook/

	# Archive app
	cd dist
	gnutar cfp - ${BUILD_NAME}.app | gzip --best -c > ../../../${BUILD_NAME_INSTALL}.tar.gz
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
	#mv dist/${BUILD_NAME}.app dist/${BUILD_NAME}.app
	cp -a dist/${BUILD_NAME}.app /Volumes/${BUILD_NAME}/Cura
	cp -a ../../resources/images/.background.png /Volumes/${BUILD_NAME}/Cura
	echo 'detach'
	hdiutil detach /Volumes/${BUILD_NAME}
	echo 'convert'
	hdiutil convert ${BUILD_NAME}.dmg.sparseimage -format UDZO -imagekey zlib-level=9 -ov -o ../../${BUILD_NAME_INSTALL}.dmg

	cd ../..
	zip ${BUILD_NAME_INSTALL}.dmg.zip ${BUILD_NAME_INSTALL}.dmg

	if [ ! -d "packages" ]; then
		mkdir packages
	fi
	mv -f ${BUILD_NAME_INSTALL}.dmg ./packages/

	if [ ! -d "dist" ]; then
		mkdir dist
	fi
	mv -f ${BUILD_NAME_INSTALL}.dmg.zip ./dist/

	exit
fi

#############################
# Debian
#############################
if [[ $BUILD_TARGET == debian* ]]; then
	sudo chown $USER:$USER scripts/linux/${BUILD_TARGET} -R
	rm -rf scripts/linux/${BUILD_TARGET}/usr/share
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}
	cp -a Cura scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/
	cp -a resources scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/
	cp -a plugins scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/
	cp -a CuraEngine/build/CuraEngine scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/
	cp scripts/linux/utils/cura.py scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/
	echo $BUILD_NAME > scripts/linux/${BUILD_TARGET}/usr/share/${LINUX_TARGET_NAME}/Cura/version
	rm -rf scripts/linux/${BUILD_TARGET}/usr/share/applications
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/share/applications
	cp scripts/linux/utils/curabydago.desktop scripts/linux/${BUILD_TARGET}/usr/share/applications/${LINUX_TARGET_NAME}.desktop
	rm -rf scripts/linux/${BUILD_TARGET}/usr/share/icons
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/share/icons/curabydago
	cp scripts/linux/utils/curabydago.ico scripts/linux/${BUILD_TARGET}/usr/share/icons/curabydago/${LINUX_TARGET_NAME}.ico
	rm -rf scripts/linux/${BUILD_TARGET}/usr/bin
	mkdir -p scripts/linux/${BUILD_TARGET}/usr/bin
	cp scripts/linux/utils/curabydago scripts/linux/${BUILD_TARGET}/usr/bin/${LINUX_TARGET_NAME}
	sudo chown root:root scripts/linux/${BUILD_TARGET} -R
	sudo chmod 755 scripts/linux/${BUILD_TARGET}/usr -R
	sudo chmod 755 scripts/linux/${BUILD_TARGET}/DEBIAN -R
	cd scripts/linux
	sudo dpkg-deb --build ${BUILD_TARGET} $(dirname ${BUILD_NAME})/${BUILD_NAME}-${BUILD_TARGET}.deb
	sudo chown $USER:$USER ${BUILD_TARGET} -R
	cp ./utils/README.md .
	zip ${BUILD_NAME}-${BUILD_TARGET}.zip ${BUILD_NAME}-${BUILD_TARGET}.deb README.md
	rm README.md

	cd ../..
	if [ ! -d "packages" ]; then
		mkdir packages
	fi
	mv -f scripts/linux/${BUILD_NAME}-${BUILD_TARGET}.deb ./packages/

	if [ ! -d "dist" ]; then
		mkdir dist
	fi
	mv -f scripts/linux/${BUILD_NAME}-${BUILD_TARGET}.zip ./dist/

	exit
fi

#############################
# Archive .tar.gz
#############################
if [[ $BUILD_TARGET == archive* ]]; then
	rm -rf scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}
	mkdir -p scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}
	cp -a Cura scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/
	cp -a resources scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/
	cp -a plugins scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/
	cp -a CuraEngine/build/CuraEngine scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/
	cp scripts/linux/utils/cura.py scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/
	echo $BUILD_NAME > scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}/Cura/version
	cp scripts/linux/utils/curabydago_generic.desktop scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}.desktop
	cp scripts/linux/utils/curabydago.ico scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/${LINUX_TARGET_NAME}.ico
	cp scripts/linux/${BUILD_TARGET}/README.md scripts/linux/${BUILD_TARGET}/${BUILD_NAME}-${BUILD_TARGET}/README.md
	cd scripts/linux/${BUILD_TARGET}
	tar -czvf ${BUILD_NAME}-${BUILD_TARGET}.tar.gz ${BUILD_NAME}-${BUILD_TARGET}
	mv ${BUILD_NAME}-${BUILD_TARGET}.tar.gz ../
	cd ..
	zip ${BUILD_NAME}-${BUILD_TARGET}.tar.gz.zip ${BUILD_NAME}-${BUILD_TARGET}.tar.gz

	cd ../..
	if [ ! -d "packages" ]; then
		mkdir packages
	fi
	mv -f scripts/linux/${BUILD_NAME}-${BUILD_TARGET}.tar.gz ./packages/

	if [ ! -d "dist" ]; then
		mkdir dist
	fi
	mv -f scripts/linux/${BUILD_NAME}-${BUILD_TARGET}.tar.gz.zip ./dist/

	exit
fi

#############################
# Download all needed files.
#############################
if [[ $BUILD_TARGET == win32 ]]; then
	##Which versions of external programs to use
	WIN_PORTABLE_PY_VERSION=2.7.6.1
	#Check if we have 7zip, needed to extract and packup a bunch of packages for windows.
	checkTool 7z "7zip: http://www.7-zip.org/"
	checkTool mingw32-make "mingw: http://www.mingw.org/"
	#Get portable python for windows and extract it. (Linux and Mac need to install python themselfs)
	downloadURL http://ftp.nluug.nl/languages/python/portablepython/v2.7/PortablePython_${WIN_PORTABLE_PY_VERSION}.exe
	downloadURL http://sourceforge.net/projects/pyopengl/files/PyOpenGL/3.0.1/PyOpenGL-3.0.1.win32.exe
	downloadURL http://videocapture.sourceforge.net/VideoCapture-0.9-5.zip
	downloadURL http://sourceforge.net/projects/comtypes/files/comtypes/0.6.2/comtypes-0.6.2.win32.exe
	downloadURL http://www.uwe-sieber.de/files/ejectmedia.zip

	#############################
	# Build the packages
	#############################
	rm -rf ${BUILD_NAME}
	mkdir -p ${BUILD_NAME}
	rm -f log.txt

	#For windows extract portable python to include it.
	extract PortablePython_${WIN_PORTABLE_PY_VERSION}.exe \$_OUTDIR/App
	extract PortablePython_${WIN_PORTABLE_PY_VERSION}.exe \$_OUTDIR/Lib/site-packages
	extract PortablePython_${WIN_PORTABLE_PY_VERSION}.exe \$_OUTDIR/numpy
	extract PortablePython_${WIN_PORTABLE_PY_VERSION}.exe \$_OUTDIR/serial
	extract PyOpenGL-3.0.1.win32.exe PURELIB
	extract VideoCapture-0.9-5.zip VideoCapture-0.9-5/Python27/DLLs/vidcap.pyd
	extract comtypes-0.6.2.win32.exe
	extract ejectmedia.zip Win32
	echo "Step extract Finished"

	mkdir -p ${BUILD_NAME}/python
	mkdir -p ${BUILD_NAME}/Cura/
	mv \$_OUTDIR/App/* ${BUILD_NAME}/python
	mv \$_OUTDIR/Lib/site-packages/wx* ${BUILD_NAME}/python/Lib/site-packages/
	mv \$_OUTDIR/serial ${BUILD_NAME}/python/Lib
	mv PURELIB/OpenGL ${BUILD_NAME}/python/Lib
	mv PURELIB/comtypes ${BUILD_NAME}/python/Lib
	mv \$_OUTDIR/numpy ${BUILD_NAME}/python/Lib
	mv VideoCapture-0.9-5/Python27/DLLs/vidcap.pyd ${BUILD_NAME}/python/DLLs
	mv Win32/EjectMedia.exe ${BUILD_NAME}/Cura/
	echo "Step mv Finished"

	rm -rf \$_OUTDIR
	rm -rf Win32
	rm -rf PURELIB
	rm -rf VideoCapture-0.9-5
	echo "Step rm Finished"

	#Clean up portable python a bit, to keep the package size down.
	rm -rf ${BUILD_NAME}/python/PyCharm
	rm -rf ${BUILD_NAME}/python/PyScripter.*
	rm -rf ${BUILD_NAME}/python/Doc
	rm -rf ${BUILD_NAME}/python/locale
	rm -rf ${BUILD_NAME}/python/tcl
	rm -rf ${BUILD_NAME}/python/Lib/distutils
	rm -rf ${BUILD_NAME}/python/Lib/test
	rm -rf ${BUILD_NAME}/python/Lib/site-packages/wx-3.0-msw/docs
	rm -rf ${BUILD_NAME}/python/Lib/site-packages/wx-3.0-msw/wx/locale
	rm -rf ${BUILD_NAME}/python/Lib/site-packages/wx-3.0-msw/wx/tools
	#Remove the gle files because they require MSVCR71.dll, which is not included. We also don't need gle, so it's safe to remove it.
	rm -rf ${BUILD_NAME}/python/Lib/OpenGL/DLLS/gle*
	echo "Step clean Finished"

	#add Cura
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
		rm -rf scripts/win32/dist
		mv `pwd`/${BUILD_NAME} scripts/win32/dist
		echo ${BUILD_NAME}
		'/c/Program Files (x86)/NSIS/makensis.exe' -DVERSION=${BUILD_NAME} 'scripts/win32/installer.nsi' >> log.txt
		if [ $? != 0 ]; then echo "Failed to package NSIS installer"; exit 1; fi
		mv scripts/win32/${BUILD_NAME}.exe ./
		if [ $? != 0 ]; then echo "Can't Move Frome scripts/win32/...exe"; fi
		mv ./${BUILD_NAME}.exe ./${BUILD_NAME_INSTALL}.exe
		if [ $? != 0 ]; then echo "Can't Move Frome ./ to ./${BUILD_NAME_INSTALL}.exe"; exit 1; fi

		7z a -y ${BUILD_NAME_INSTALL}.exe.zip ${BUILD_NAME_INSTALL}.exe

		if [ ! -d "packages" ]; then
			mkdir packages
		fi
		mv -f ${BUILD_NAME_INSTALL}.exe ./packages/

		if [ ! -d "dist" ]; then
			mkdir dist
		fi
		mv -f ${BUILD_NAME_INSTALL}.exe.zip ./dist/
		echo 'Good Job, All Works Well !!! :)'
	else
		echo "No makensis"
	fi

	exit
fi
