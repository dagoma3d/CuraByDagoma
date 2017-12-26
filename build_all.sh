#!/usr/bin/env bash

BUILD_OS=${1:-w} # w = windows, m = mac, l = linux

git pull
for b in discoeasy200 explorer350 neva
do
	if [ "$BUILD_OS" = "l" ]; then
		./package.sh $b debian 32
		./package.sh $b debian 64
		./package.sh $b archive 32
		./package.sh $b archive 64
	elif [ "$BUILD_OS" = "w" ];	then
		./package.sh $b win32
	elif [ "$BUILD_OS" = "m" ];	then
		./package.sh $b darwin
	fi
done

exit 0
