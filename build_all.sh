#!/usr/bin/env bash

BUILD_OS=${1:-w} # w = windows, m = mac, l = linux

git pull
if [ "$BUILD_OS" = "l" ]; then
	./package.sh debian 32 1
	./package.sh debian 64 1
	./package.sh archive 32 1
	./package.sh archive 64 1
elif [ "$BUILD_OS" = "w" ]; then
	./package.sh windows 32 1
	./package.sh windows 64 1
elif [ "$BUILD_OS" = "m86" ]; then
	./package.sh darwin x86 1
elif [ "$BUILD_OS" = "m64" ]; then
	./package.sh darwin arm64 1
fi

exit 0
