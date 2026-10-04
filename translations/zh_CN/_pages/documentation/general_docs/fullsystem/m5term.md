---
layout: documentation
title: "m5 term"
doc: gem5 文档
parent: fullsystem
permalink: /documentation/general_docs/fullsystem/m5term
---
# m5 term
m5term 程序让用户可以连接到全系统（full-system）gem5 提供的被模拟控制台接口。只需进入 util/term 目录并构建 m5term：
```
% cd gem5/util/term
% make
gcc  -o m5term term.c
% make install
sudo install -o root -m 555 m5term /usr/local/bin
```
m5term 的用法是：
```
./m5term <host> <port>
```
	<host> 是运行 gem5 的宿主机

	<port> 是要连接的控制台端口。gem5 默认
	使用端口 3456，但如果该端口被占用，它会尝试下一个
	更大的端口，直到找到可用的。

	如果一次模拟中运行多个系统，
	每个系统都会有一个控制台。（例如，第一个系统的
	控制台在 3456，第二个在 3457）

	m5term 使用 '~' 作为转义字符。如果你输入
	转义字符后跟一个 '.'，m5term 程序
	将退出。

m5term 可以用来与模拟器交互操作，不过用户往往需要设置各种终端参数才能让它正常工作

下面是一个略作精简的 m5term 实际运行示例：

	% m5term localhost 3456
	==== m5 slave console: Console 0 ====
	M5 console
	Got Configuration 127
	memsize 8000000 pages 4000
	First free page after ROM 0xFFFFFC0000018000
	HWRPB 0xFFFFFC0000018000 l1pt 0xFFFFFC0000040000 l2pt 0xFFFFFC0000042000 l3pt_rpb 0xFFFFFC0000044000 l3pt_kernel 0xFFFFFC0000048000 l2reserv 0xFFFFFC0000046000
	CPU Clock at 2000 MHz IntrClockFrequency=1024
	Booting with 1 processor(s)
	...
	...
	VFS: Mounted root (ext2 filesystem) readonly.
	Freeing unused kernel memory: 480k freed
	init started:  BusyBox v1.00-rc2 (2004.11.18-16:22+0000) multi-call binary

	PTXdist-0.7.0 (2004-11-18T11:23:40-0500)

	mounting filesystems...
	EXT2-fs warning: checktime reached, running e2fsck is recommended
	loading script...
	Script from M5 readfile is empty, starting bash shell...
	# ls
	benchmarks  etc         lib         mnt         sbin        usr
	bin         floppy      lost+found  modules     sys         var
	dev         home        man         proc        tmp         z
	#
