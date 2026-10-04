---
layout: documentation
title: 创建磁盘镜像
doc: gem5 文档
parent: fullsystem
permalink: documentation/general_docs/fullsystem/disks
---

# 为全系统（full-system）模式创建磁盘镜像

在全系统（full-system）模式下，gem5 依赖一个安装了操作系统的磁盘镜像来运行模拟。
gem5 中的磁盘设备从磁盘镜像获取其初始内容。
磁盘镜像文件保存磁盘上的所有字节，就如同你在真实设备上看到的那样。
其他一些系统也使用格式更复杂的磁盘镜像，它们提供压缩、加密等能力。gem5 目前只支持原始（raw）镜像，因此如果你的镜像是其他格式之一，必须先把它转换为原始镜像才能在模拟中使用。
通常会有一些工具可以在不同格式之间转换。

创建可用于 gem5 的磁盘镜像有多种方式。
以下是四种构建磁盘镜像的方法：

- 使用 gem5 工具创建磁盘镜像
- 使用 gem5 工具与 chroot 创建磁盘镜像
- 使用 QEMU 创建磁盘镜像
- 使用 Packer 创建磁盘镜像

这些方法彼此独立。
接下来，我们逐一讨论这些方法。

## 1) 使用 gem5 工具创建磁盘镜像

```md
Disclaimer: This is from the old website and some of the stuff in this method can be out-dated.

```
因为磁盘镜像表示磁盘本身上的所有字节，所以它包含的不只是文件系统。
对于大多数系统上的硬盘，镜像以分区表开头。
表中的每个分区（通常只有一个）也在镜像中。
如果你想操作整个磁盘，就使用整个镜像；但如果你只想处理某一个分区和/或其中的文件系统，就需要专门选中镜像的那一部分。
losetup 命令（下文讨论）有一个 -o 选项，可以指定镜像中的起始位置。

<iframe width="560" height="315" src="https://www.youtube.com/embed/Oh3NK12fnbg" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe><div class='thumbcaption'>一段在 Ubuntu 12.04 64 位下用 qemu 处理镜像文件的 YouTube 视频。视频分辨率可设置为 1080</div>


### 创建空镜像

你可以用 gem5 提供的 ./util/gem5img.py 脚本构建磁盘镜像。
了解一下镜像是如何构建的是个好主意，以防出错或你需要以特殊方式操作。
不过在本方法中，我们使用 gem5img.py 脚本来完成构建和格式化镜像的过程。
如果你想理解它内部在做什么，请看下文。
运行 gem5img.py 可能需要你输入 sudo 密码。
*你不应该以 root 用户运行自己不理解的命令！你应该查看 util/gem5img.py 文件，确保它不会对你的电脑做任何恶意操作！*

你可以用 gem5img.py 的 "init" 选项创建空镜像，用 "new"、"partition" 或 "format" 分别完成 init 的各个部分，用 "mount" 或 "umount" 挂载或卸载已有镜像。

### 挂载镜像

要把文件系统挂载到镜像文件上，首先找到一个回环（loopback）设备，并以合适的偏移把它附加到你的镜像上，具体将在[格式化](#formatting)一节进一步描述。

```sh
mount -o loop,offset=32256 foo.img
```

<iframe width="560" height="315" src="https://www.youtube.com/embed/OXH1oxQbuHA" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe><div class='thumbcaption'>一段在 Ubuntu 12.04 64 位下用 mount 添加文件的 YouTube 视频。视频分辨率可设置为 1080</div>

### 卸载

要卸载镜像，像平常一样使用 umount 命令。

```sh
umount
```

### 镜像内容

现在你既能创建镜像文件、又能挂载它的文件系统了，接下来就会想真正往里面放一些文件。
你可以自由使用任何文件，但 gem5 开发者发现 Gentoo stage3 tarball 是很好的起点。
它们本质上是一个几乎可启动、且相当精简的 Linux 安装，并且可用于多种体系结构。

如果你选择使用 Gentoo tarball，先把它解压到你已挂载的镜像中。
/etc/fstab 文件中会有 root、boot 和 swap 设备的占位条目。
你应适当更新该文件，删除不会使用的任何条目（例如 boot 分区）。
接下来，你需要修改 inittab 文件，使其使用 m5 实用程序（在别处介绍）读入宿主机提供的 init 脚本并运行它。
如果放任正常的 init 脚本运行，你关注的工作负载（workload）可能需要更长时间才能开始，例如你将无法注入自己的 init 脚本以动态控制启动哪些基准测试（benchmark），而且你必须通过模拟终端与模拟交互，这会引入非确定性。

#### 修改

默认情况下，gem5 不会把对磁盘的修改写回底层镜像文件。
你所做的任何改动都会保存在中间的 COW 层中，并在模拟结束时丢弃。
如果你想修改底层磁盘，可以关闭 COW 层。

#### 内核与引导加载程序

此外，一般而言 gem5 会跳过引导过程的引导加载程序部分，自行把内核加载到被模拟内存中。这意味着无需把 grub 之类的引导加载程序安装到磁盘镜像上，也不必把要启动的内核放到镜像上。
内核单独提供，可以在不修改磁盘镜像的情况下轻松更换。

### 用回环设备操作镜像

#### 回环设备

Linux 支持回环设备，即由文件支持的设备。
把其中一个附加到你的磁盘镜像后，你就可以对它使用通常运行在真实磁盘设备上的标准 Linux 命令。
你可以用带 "loop" 选项的 mount 命令建立回环设备并把它挂载到某处。
遗憾的是你无法指定镜像中的偏移，因此那只对文件系统镜像有用，而对所需的磁盘镜像无用。
不过，你可以使用更低层的 losetup 命令自行建立回环设备并提供正确的偏移。
完成之后，你就可以像对磁盘分区那样对它使用 mount 命令、格式化它等。
如果你不提供偏移，回环设备会指向整个镜像，你就可以用自己喜欢的程序在其上建立分区。

### 处理镜像文件

要从零创建一个空镜像，你需要创建该文件本身、对它分区，并用文件系统格式化（其中一个）分区。

####  创建实际文件

首先，决定你希望镜像有多大。
把它做得足够大以容纳你已知需要的所有内容，并留出一些余量，是个好主意。
如果之后发现它太小，你就得创建一个更大的新镜像并把所有内容搬过去。
如果做得太大，你会不必要地占用实际磁盘空间，并使镜像更难处理。
确定大小后，你就要真正创建该文件。
基本上，你只需创建一个特定大小、内容全为零的文件。
一种做法是用 dd 命令把适当数量的字节从 /dev/zero 复制到新文件中。
或者，你也可以创建该文件、在其中定位到最后一个字节，并写入一个零字节。
你跳过的所有空间都会成为该文件的一部分，并被定义为读作零，但由于你并未在那里显式写入任何数据，大多数文件系统都足够聪明，不会真的把它存到磁盘上。
这样你就能创建一个很大的镜像，却在物理磁盘上只占用很少空间。
一旦你之后开始写入该文件，情况就会改变；而且如果不小心，复制该文件可能会把它扩展到完整大小。

#### 分区

首先，用带 -f 选项的 losetup 命令找到一个可用的回环设备。

```sh
losetup -f
```

接下来，用 losetup 把该设备附加到你的镜像上。
如果可用设备是 /dev/loop0 而你的镜像是 foo.img，你可以使用这样的命令。

```sh
losetup /dev/loop0 foo.img
```

/dev/loop0（或你正在使用的其他设备）现在将指向你的整个镜像文件。
用你喜欢的任何分区程序在它上面建立一个（或多个）分区。
为简单起见，最好只创建一个占用整个镜像的分区。
我们说它占用整个镜像，但实际上它占用除文件开头分区表本身之外的所有空间，之后还可能为 DOS/引导加载程序兼容性浪费一些空间。

从现在起我们要处理新建的分区而不是整个磁盘，因此先用 losetup 的 -d 选项释放该回环设备

```sh
losetup -d /dev/loop0
```

#### 格式化 {#formatting}

首先，像上面的分区步骤那样，用 losetup 的 -f 选项找到一个可用的回环设备。

```sh
losetup -f
```

我们会再次把镜像附加到该设备上，不过这次只想指向将要放入文件系统的那个分区。
对于 PC 和 Alpha 系统，该分区通常从一个磁道开始，一个磁道是 63 个扇区，每个扇区 512 字节，即 63 * 512 = 32256 字节。
你的正确取值可能不同，取决于镜像的几何结构与布局。
无论如何，你应当用 -o 选项设置回环设备，使其代表你关注的分区。

```sh
losetup -o 32256 /dev/loop0 foo.img
```

接下来，使用合适的格式化命令（通常是 mke2fs）为该分区建立文件系统。

```sh
mke2fs /dev/loop0
```

现在你已经成功创建了一个空镜像文件。
如果你打算继续使用它（很可能如此，因为它还是空的），可以让回环设备保持附加；也可以用 losetup -d 清理它。

```sh
losetup -d /dev/loop0
```

别忘了用 losetup -d 命令清理附加到镜像上的回环设备。

```sh
losetup -d /dev/loop0
```

## 2) 使用 gem5 工具与 chroot 创建磁盘镜像

本节的讨论假设你已经检出了一份 gem5，并能在全系统（full-system）模式下构建和运行 gem5。
本节讨论中我们使用 x86 指令集架构（ISA），这大体上也适用于其他指令集架构。

### 创建空白磁盘镜像

第一步是创建空白磁盘镜像（通常是 .img 文件）。
这与我们在第一种方法中所做的类似。
我们可以使用 gem5 开发者提供的 gem5img.py 脚本。
要创建默认以 ext2 格式化的空白磁盘镜像，只需运行：

```
> util/gem5img.py init ubuntu-14.04.img 4096
```

该命令创建一个名为 "ubuntu-14.04.img"、大小为 4096 MB 的新镜像。
如果你没有创建回环设备的权限，该命令可能要求你输入 sudo 密码。
*你不应该以 root 用户运行自己不理解的命令！你应该查看 util/gem5img.py 文件，确保它不会对你的电脑做任何恶意操作！*

本节中我们会大量使用 util/gem5img.py，因此你或许想更深入地了解它。
如果你只运行 `util/gem5img.py`，它会显示所有可能的命令。

```
Usage: %s [command] <command arguments>
where [command] is one of
    init: Create an image with an empty file system.
    mount: Mount the first partition in the disk image.
    umount: Unmount the first partition in the disk image.
    new: File creation part of "init".
    partition: Partition part of "init".
    format: Formatting part of "init".
Watch for orphaned loopback devices and delete them with
losetup -d. Mounted images will belong to root, so you may need
to use sudo to modify their contents
```

### 把根文件系统复制到磁盘

现在我们创建了空白磁盘，需要用它装入操作系统的所有文件。
Ubuntu 专门为此分发了一套文件。
你可以在 <http://cdimage.ubuntu.com/releases/14.04/release/> 找到 14.04 版的 [Ubuntu core](https://wiki.ubuntu.com/Core) 发行版。由于我们模拟的是 x86 机器，因此使用 `ubuntu-core-14.04-core-amd64.tar.gz`。
下载适合你所模拟系统的镜像。

接下来，我们需要挂载空白磁盘并把所有文件复制到磁盘上。

```
mkdir mnt
../../util/gem5img.py mount ubuntu-14.04.img mnt
wget http://cdimage.ubuntu.com/ubuntu-core/releases/14.04/release/ubuntu-core-14.04-core-amd64.tar.gz
sudo tar xzvf ubuntu-core-14.04-core-amd64.tar.gz -C mnt
```

下一步是把一些必需文件从你的工作系统复制到磁盘上，以便我们 chroot 进入新磁盘。我们需要把 `/etc/resolv.conf` 复制到新磁盘上。

```
sudo cp /etc/resolv.conf mnt/etc/
```

### 配置 gem5 专用文件

#### 创建串口终端

默认情况下，gem5 使用串口来实现从宿主系统到被模拟系统的通信。要使用它，我们需要创建一个串口 tty。
由于 Ubuntu 使用 upstart 控制 init 进程，我们需要在 /etc/init 中添加一个文件来初始化我们的终端。
此外，在该文件中我们会加入一些代码，检测是否向被模拟系统传入了脚本。
如果有脚本，我们会执行该脚本而不是创建终端。

把以下代码放入名为 /etc/init/tty-gem5.conf 的文件：

```
# ttyS0 - getty
#
# This service maintains a getty on ttyS0 from the point the system is
# started until it is shut down again, unless there is a script passed to gem5.
# If there is a script, the script is executed then simulation is stopped.

start on stopped rc RUNLEVEL=[12345]
stop on runlevel [!12345]

console owner
respawn
script
   # Create the serial tty if it doesn't already exist
   if [ ! -c /dev/ttyS0 ]
   then
      mknod /dev/ttyS0 -m 660 /dev/ttyS0 c 4 64
   fi

   # Try to read in the script from the host system
   /sbin/m5 readfile > /tmp/script
   chmod 755 /tmp/script
   if [ -s /tmp/script ]
   then
      # If there is a script, execute the script and then exit the simulation
      exec su root -c '/tmp/script' # gives script full privileges as root user in multi-user mode
      /sbin/m5 exit
   else
      # If there is no script, login the root user and drop to a console
      # Use m5term to connect to this console
      exec /sbin/getty --autologin root -8 38400 ttyS0
   fi
end script
```

#### 配置 localhost

如果我们打算使用任何依赖 localhost 回环设备的应用，也需要把它配置好。
为此，我们需要把以下内容加入 `/etc/hosts` 文件。

```
127.0.0.1 localhost
::1 localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts
```

#### 更新 fstab

接下来，我们需要为希望从被模拟系统访问的每个分区在 `/etc/fstab` 中建立条目。绝对必需的只有一个分区（`/`）；不过你可能想添加其他分区，例如交换分区。

`/etc/fstab` 文件中应出现以下内容。

```
# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a
# device; this may be used with UUID= as a more robust way to name devices
# that works even if disks are added and removed. See fstab(5).
#
# <file system>    <mount point>   <type>  <options>   <dump>  <pass>
/dev/hda1      /       ext3        noatime     0 1
```

#### 把 `m5` 二进制程序复制到磁盘

gem5 附带一个额外的二进制应用程序，它执行伪指令，使被模拟系统能够与宿主系统交互。
要构建该二进制程序，在 `gem5/m5` 目录中运行 `make -f Makefile.<isa>`，其中 `<isa>` 是你要模拟的指令集架构（例如 x86）。之后，你应该得到一个 `m5` 二进制文件。
把该文件复制到新建磁盘的 /sbin 目录。

用所有 gem5 专用文件更新磁盘之后，除非你还要继续添加更多应用或复制其他文件，请卸载该磁盘镜像。

```
> util/gem5img.py umount mnt
```

### 安装新应用

在磁盘上安装新应用最简单的方式是使用 `chroot`。
该程序在逻辑上把根目录（"/"）改为另一个目录，此处即 mnt。
在改变根目录之前，你必须先在新根目录中建立特殊目录。为此，
我们使用 `mount -o bind`。

```
> sudo /bin/mount -o bind /sys mnt/sys
> sudo /bin/mount -o bind /dev mnt/dev
> sudo /bin/mount -o bind /proc mnt/proc
```

绑定这些目录之后，你现在可以 `chroot`：

```
> sudo /usr/sbin/chroot mnt /bin/bash
```

此时你会看到 root 提示符，并且处于新磁盘的 `/`
目录中。

你应该更新仓库信息。

```
> apt-get update
```

你可能想用以下命令把 universe 仓库加入列表。
注意：在 14.04 中第一条命令是必需的。

```
> apt-get install software-properties-common
> add-apt-repository universe
> apt-get update
```

现在，你就可以通过 `apt-get` 安装任何在原生 Ubuntu 机器上能安装的应用了。

请记住，退出之后你需要卸载所有我们
绑定过的目录。

```
> sudo /bin/umount mnt/sys
> sudo /bin/umount mnt/proc
> sudo /bin/umount mnt/dev
```


## 3) 使用 QEMU 创建磁盘镜像

该方法是上一创建磁盘镜像方法的延续。
我们将看到如何用 qemu 而不是 gem5 工具来创建、编辑和配置磁盘镜像。
本节假设你已在系统中安装了 qemu。
在 Ubuntu 中，可以通过以下命令完成

```
sudo apt-get install qemu-kvm libvirt-bin ubuntu-vm-builder bridge-utils
```

### 步骤 1：创建空磁盘
使用 qemu 磁盘工具创建一个空的原始磁盘镜像。
在本例中，我选择创建名为 "ubuntu-test.img"、大小为 8GB 的磁盘。

```
qemu-img create ubuntu-test.img 8G
```

### 步骤 2：用 qemu 安装 ubuntu
现在我们有了空白磁盘，将使用 qemu 在磁盘上安装 Ubuntu。
建议使用 Ubuntu 的服务器版本，因为 gem5 对显示的支持并不好。
因此桌面环境用处不大。

首先，你需要从 [Ubuntu 网站](https://www.ubuntu.com/download/server)下载安装 CD 镜像。

接下来，用 qemu 从该 CD 镜像启动，并把系统中的磁盘设为上面创建的空白磁盘。
Ubuntu 需要至少 1GB 内存才能正确安装，因此务必把 qemu 配置为使用至少 1GB 内存。

```
qemu-system-x86_64 -hda ../gem5-fs-testing/ubuntu-test.img -cdrom ubuntu-16.04.1-server-amd64.iso -m 1024 -enable-kvm -boot d
```

这样，你只需按屏幕上的指引把 Ubuntu 安装到磁盘镜像即可。
安装中唯一的坑是 gem5 的 IDE 驱动似乎与逻辑分区配合不佳。
因此，在安装 Ubuntu 期间，务必手动分区并删除任何逻辑分区。
反正除非你专门要用交换空间，磁盘上并不需要任何交换空间。

### 步骤 3：启动并安装所需软件

在磁盘上安装好 Ubuntu 之后，退出 qemu 并去掉 `-boot d` 选项，这样就不再从 CD 启动。
现在，你可以再次从已安装 Ubuntu 的主磁盘镜像启动。

由于我们使用 qemu，你应当有网络连接（尽管 [ping 不会
工作](http://wiki.qemu.org/Documentation/Networking#User_Networking_.28SLIRP.29)）。
在 qemu 中启动时，你可以直接使用 `sudo apt-get install`，把需要的任何软件
安装到磁盘上。

```
qemu-system-x86_64 -hda ../gem5-fs-testing/ubuntu-test.img -cdrom ubuntu-16.04.1-server-amd64.iso -m 1024 -enable-kvm
```

### 步骤 4：更新 init 脚本

默认情况下，gem5 期望有一个修改过的 init 脚本，它从宿主机加载脚本并在客户机（guest）中执行。
要使用该特性，你需要按下面的步骤操作。

或者，你可以安装这个[网站](http://cs.wisc.edu/~powerjg/files/gem5-guest-tools-x86.tgz)上提供的 x86 预编译二进制程序。
在 qemu 中，你可以运行以下命令，它会替你完成上述步骤。

```
wget http://cs.wisc.edu/~powerjg/files/gem5-guest-tools-x86.tgz
tar xzvf gem5-guest-tools-x86.tgz
cd gem5-guest-tools/
sudo ./install
```

现在，你就可以在 Python 配置脚本中使用 `system.readfile` 参数了。该文件会被（`gem5init` 脚本）自动加载并执行。

### 手动安装 gem5 init 脚本

首先，在宿主机上构建 m5 二进制程序。

```
cd util/m5
make -f Makefile.x86
```

然后，把该二进制程序复制到客户机中并放入 `/sbin`。同时创建指向它的链接 `/sbin/gem5`。

接着，为了让 init 脚本在 gem5 启动时执行，创建文件 /lib/systemd/system/gem5.service，内容如下：

```
[Unit]
Description=gem5 init script
Documentation=http://gem5.org
After=getty.target

[Service]
Type=idle
ExecStart=/sbin/gem5init
StandardOutput=tty
StandardInput=tty-force
StandardError=tty

[Install]
WantedBy=default.target
```

启用 gem5 服务，并**禁用 ttyS0 服务**。
如果你的磁盘启动后停在登录提示符，可能是因为没有禁用 ttyS0 服务。

```
systemctl enable gem5.service
```

最后，创建由该服务执行的 init 脚本。在
`/sbin/gem5init` 中：

```
#!/bin/bash -

CPU=`cat /proc/cpuinfo | grep vendor_id | head -n 1 | cut -d ' ' -f2-`
echo "Got CPU type: $CPU"

if [ "$CPU" != "M5 Simulator" ];
then
    echo "Not in gem5. Not loading script"
    exit 0
fi

# Try to read in the script from the host system
/sbin/m5 readfile > /tmp/script
chmod 755 /tmp/script
if [ -s /tmp/script ]
then
    # If there is a script, execute the script and then exit the simulation
    su root -c '/tmp/script' # gives script full privileges as root user in multi-user mode
    sync
    sleep 10
    /sbin/m5 exit
fi
echo "No script found"
```

### 问题与（部分）解决方案

按该方法操作时你可能会遇到一些问题。
其中一些问题和解决方案在这个[页面](http://www.lowepower.com/jason/setting-up-gem5-full-system.html)上讨论。

## 4) 使用 Packer 创建磁盘镜像

本节讨论一种自动化创建装有 Ubuntu 服务器、与 gem5 兼容的磁盘镜像的方法。我们借助 packer 来完成，它使用一个 .json 模板文件来构建和配置磁盘镜像。该模板文件可以配置为构建装有特定基准测试（benchmark）的磁盘镜像。所提到的模板文件见[此处]({{ site.baseurl }}/assets/files/packer_template.json)。


### 用 Packer 构建简单磁盘镜像

#### a. 简要说明其工作方式
我们使用 [Packer](https://www.packer.io/) 和 [QEMU](https://www.qemu.org/) 来自动化磁盘创建过程。
本质上，QEMU 负责建立虚拟机以及在构建过程中与磁盘镜像的所有交互。
这些交互包括把 Ubuntu Server 安装到磁盘镜像、把文件从你的机器复制到磁盘镜像，以及在 Ubuntu 安装完成后在磁盘镜像上运行脚本。
不过我们不会直接使用 QEMU。
Packer 提供了一种通过 JSON 脚本与 QEMU 交互的更简单方式，它比从命令行使用 QEMU 更具表达力。

#### b. 安装所需软件/依赖项
如果尚未安装，可以用以下命令安装 QEMU：
```shell
sudo apt-get install qemu
```
从[官方网站](https://www.packer.io/downloads.html)下载 Packer 二进制程序。

#### c. 定制 Packer 脚本
默认 packer 脚本 `template.json` 应根据所需的磁盘镜像和构建过程可用资源进行修改与调整。我们会把默认模板重命名为 `[disk-name].json`。需要修改的变量出现在 `[disk-name].json` 文件的末尾 `variables` 部分。
用于构建磁盘镜像的配置文件及目录结构如下所示：
```shell
disk-image/
    [disk-name].json: packer script
    Any experiment-specific post installation script
    post-installation.sh: generic shell script that is executed after Ubuntu is installed
    preseed.cfg: preseeded configuration to install Ubuntu
```

##### i. 定制虚拟机（VM）
在 `[disk-name].json` 中，以下变量可用于定制虚拟机：

| 变量         | 用途     | 示例  |
| ---------------- |-------------|----------|
| [vm_cpus](https://www.packer.io/docs/builders/qemu.html#cpus) **（应修改）** | 虚拟机使用的宿主机 CPU 数量 | "2"：虚拟机使用 2 个 CPU |
| [vm_memory](https://www.packer.io/docs/builders/qemu.html#memory) **（应修改）**| 虚拟机内存量，单位 MB | "2048"：虚拟机使用 2 GB 内存 |
| [vm_accelerator](https://www.packer.io/docs/builders/qemu.html#accelerator) **（应修改）** | 虚拟机使用的加速器，例如 Kvm | "kvm"：将使用 kvm |

<br />

##### ii. 定制磁盘镜像
在 `[disk-name].json` 中，可以用以下变量定制磁盘镜像大小：

| 变量        | 用途     | 示例  |
| ---------------- |-------------|----------|
| [image_size](https://www.packer.io/docs/builders/qemu.html#disk_size) **（应修改）** | 磁盘镜像大小，单位 MB | "8192"：镜像大小为 8 GB  |
| [image_name] | 所构建磁盘镜像的名称 | "boot-exit"  |

<br />

##### iii. 文件传输
在构建磁盘镜像时，用户需要把文件（基准测试、数据集等）移到
磁盘镜像中。要进行这种文件传输，可以在 `[disk-name].json` 的 `provisioners` 下加入：

```shell
{
    "type": "file",
    "source": "post_installation.sh",
    "destination": "/home/gem5/",
    "direction": "upload"
}
```
上面的示例把文件 `post_installation.sh` 从宿主机复制到磁盘镜像中的 `/home/gem5/`。
该方法也能从宿主机把文件夹复制到磁盘镜像，反之亦然。
需要注意的是，结尾的斜杠会影响复制过程[（更多细节）](https://www.packer.io/docs/provisioners/file.html#directory-uploads)。
下面是一些关于在路径末尾使用斜杠所产生效果的重要示例。

| `source`        | `destination`     | `direction`  |  `Effect`  |
| ---------------- |-------------|----------|-----|
| `foo.txt` | `/home/gem5/bar.txt` | `upload` | 把文件（宿主机）复制为文件（镜像） |
| `foo.txt` | `bar/` | `upload` | 把文件（宿主机）复制到文件夹（镜像） |
| `/foo` | `/tmp` | `upload` | `mkdir /tmp/foo`（镜像）；  `cp -r /foo/* (host) /tmp/foo/ (image)`； |
| `/foo/` | `/tmp` | `upload` | `cp -r /foo/* (host) /tmp/ (image)` |

如果 `direction` 为 `download`，文件将从镜像复制到宿主机。

**注意**：[这是一种在安装 Ubuntu 后仅运行一次脚本而不复制到磁盘镜像的方式](#customizingscripts3)。

##### iv. 安装基准测试依赖项
要安装依赖项，你可以使用 bash 脚本 `post_installation.sh`，它会在 Ubuntu 安装和文件复制完成后运行。
例如，如果我们想安装 `gfortran`，在 `post_installation.sh` 中加入：
```shell
echo '12345' | sudo apt-get install gfortran;
```
在上面的示例中，我们假设用户密码是 `12345`。
它本质上是一个在文件复制完成后在虚拟机上执行的 bash 脚本，你可以把该脚本修改为适合任何用途的 bash 脚本。

##### v. 在磁盘镜像上运行其他脚本
在 `[disk-name].json` 中，我们可以向 `provisioners` 添加更多脚本。
注意这些文件在宿主机上，但作用效果在磁盘镜像上。
例如，下面的示例在 Ubuntu 安装完成后运行 `post_installation.sh`，
{% raw %}
```sh
{
    "type": "shell",
    "execute_command": "echo '{{ user `ssh_password` }}' | {{.Vars}} sudo -E -S bash '{{.Path}}'",
    "scripts":
    [
        "post-installation.sh"
    ]
}
```
{% endraw %}

#### d. 构建磁盘镜像

##### i. 构建
要构建磁盘镜像，首先用以下命令校验模板文件：
```sh
./packer validate [disk-name].json
```
然后，就可以用该模板文件构建磁盘镜像：
```sh
./packer build [disk-name].json
```
在相当新的机器上，构建过程用不了 15 分钟。
使用用户自定义名称（image_name）的磁盘镜像会生成在名为 [image_name]-image 的文件夹中。
[我们建议使用 VNC 查看器来观察构建过程](#inspect)。

##### ii. 观察构建过程
在磁盘镜像构建过程中，Packer 会运行一个 VNC（Virtual Network Computing）服务器，你可以通过从 VNC 客户端连接到该服务器来观察构建过程。VNC 客户端有很多选择。运行 Packer 脚本时，它会告诉你 VNC 服务器使用哪个端口。例如，如果它显示 `qemu: Connecting to VM via VNC (127.0.0.1:5932)`，那么 VNC 端口就是 5932。
要从 VNC 客户端连接到 VNC 服务器，使用地址 `127.0.0.1:5932`（对应端口号 5932）。
如果你需要通过端口转发把 VNC 端口从远程机器转发到本地机器，可以使用 SSH 隧道
```shell
ssh -L 5932:127.0.0.1:5932 <username>@<host>
```
该命令会把宿主机上的端口 5932 转发到你的机器，然后你就可以在 VNC 查看器中使用地址 `127.0.0.1:5932` 连接到该 VNC 服务器。

**注意**：当 Packer 正在安装 Ubuntu 时，终端屏幕会长时间显示 "waiting for SSH" 而没有任何更新。
这不是 Ubuntu 安装是否出错的表现。
因此，我们强烈建议至少用一次 VNC 查看器来观察镜像构建过程。
