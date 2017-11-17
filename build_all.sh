#!/usr/bin/env bash

BUILD_OS=${1:-w} # w = windows, m = mac, l = linux

for b in master neva explorer350
do
	git checkout $b
	git pull
	if [ "$BUILD_OS" = "l" ]; then
		./package.sh debian 32
		./package.sh debian 64
		./package.sh archive 32
		./package.sh archive 64
	elif [ "$BUILD_OS" = "w" ];	then
		./package.sh win32
	elif [ "$BUILD_OS" = "m" ];	then
		./package.sh darwin
	fi
done

exit 0
