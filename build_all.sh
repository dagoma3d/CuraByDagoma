#!/usr/bin/env bash

BUILD_OS=${1:-w} # w = windows, m = mac, l = linux

for b in master neva explorer350
do
	git checkout $b
	git pull
	if [ "$BUILD_OS" = "l" ]
	then
		./packages.sh debian_i386
		./packages.sh debian_amd64
		./packages.sh archive_i386
		./packages.sh archive_amd64
	elif [ "$BUILD_OS" = "w" ]
	then
		./package.sh win32 1
	elif [ "$BUILD_OS" = "m" ]
	then
		./package.sh darwin
	fi
done

exit 0
