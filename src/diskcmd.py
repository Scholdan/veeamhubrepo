#
# pure disk-command helpers (no external deps, so they stay unit-testable)

import re

# below this a 256m internal log risks exceeding the XFS allocation-group size
# (mkfs.xfs would fail); large hardened repos are far above this, small demo
# disks stay on the safe auto-sized log.
BIG_LOG_MIN_BYTES = 64 * 1024**3  # 64 GiB

def mkfsxfs_cmd(part, force=False, size_bytes=None):
    # -K skips the whole-device BLKDISCARD/TRIM: on large RAID/SAN volumes that
    # discard is split into millions of requests and makes mkfs.xfs look hung.
    cmd = ["mkfs.xfs"]
    if force:
        cmd.append("-f")
    cmd += ["-K", "-b", "size=4096", "-m", "reflink=1,crc=1"]
    # -l size=256m is Veeam's recommended log for large RAID; only safe when the
    # filesystem is big enough to hold it (see BIG_LOG_MIN_BYTES).
    if size_bytes is not None and size_bytes >= BIG_LOG_MIN_BYTES:
        cmd += ["-l", "size=256m"]
    cmd.append(part)
    return cmd

def partition_node(dev):
    # kernel convention: partition 1 is <dev>p1 when the device name ends in a
    # digit (nvme0n1, mmcblk0, mapper/mpatha1-style), else <dev>1 (sda -> sda1).
    sep = "p" if re.search(r"[0-9]$", dev) else ""
    return f"{dev}{sep}1"

def is_whole_disk(dev):
    # a whole disk with no partitions: sd*/vd*/xvd* names, or nvme/mmc base nodes
    return bool(re.match(r"^/dev/[a-z]+d[a-z]{1,2}$", dev)
                or re.match(r"^/dev/nvme[0-9]+n[0-9]+$", dev)
                or re.match(r"^/dev/mmcblk[0-9]+$", dev))
