#!/bin/sh

for plt in Darwin Linux CYGWIN_NT ARM
do
  rm -f *.$plt
done

if [ ! -f "go.mod" ]
then
  go mod init edirect
fi
if [ ! -f "go.sum" ]
then
  go mod tidy
fi

mods="darwin amd64 Darwin linux amd64 Linux windows 386 CYGWIN_NT linux arm ARM"

echo "$mods" |
xargs -n 3 sh -c 'env GOOS="$0" GOARCH="$1" go build -o xtract."$2" xtract.go common.go'

echo "$mods" |
xargs -n 3 sh -c 'env GOOS="$0" GOARCH="$1" go build -o rchive."$2" rchive.go common.go'
