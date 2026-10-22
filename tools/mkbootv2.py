#!/usr/bin/env python3
"""Pack kernel, ramdisk, and dtb into an Android boot image v2."""
import argparse, struct, os, hashlib

def pad(data, page_size):
    rem = len(data) % page_size
    return data + (b'\0' * (page_size - rem) if rem else b'')

def pack_bootv2(kernel_path, ramdisk_path, dtb_path, out_path, cmdline="console=null"):
    page_size = 4096
    kernel = open(kernel_path, 'rb').read()
    ramdisk = open(ramdisk_path, 'rb').read() if ramdisk_path and os.path.exists(ramdisk_path) else b''
    dtb = open(dtb_path, 'rb').read() if dtb_path and os.path.exists(dtb_path) else b''

    header = bytearray(page_size)
    # Magic + sizes + addresses
    struct.pack_into('<8s10I', header, 0,
        b'ANDROID!',
        len(kernel), 0x8000,
        len(ramdisk), 0x1000000,
        0, 0,               # second size, second addr
        0x100,              # tags addr
        page_size,
        2,                  # header version = 2
        0x200001a6          # os version
    )
    # cmdline (up to 512 bytes)
    cmd_bytes = cmdline.encode('utf-8')[:512]
    header[64:64+len(cmd_bytes)] = cmd_bytes

    # Version 1/2 fields: header_size = 1660, dtb_size, dtb_addr
    struct.pack_into('<IQI', header, 1632, 0, 0, 1660)
    struct.pack_into('<IQ', header, 1648, len(dtb), 0x1f00000)

    # Calculate SHA
    h = hashlib.sha1()
    h.update(kernel)
    h.update(ramdisk)
    h.update(dtb)
    header[576:576+20] = h.digest()

    with open(out_path, 'wb') as f:
        f.write(header)
        f.write(pad(kernel, page_size))
        if ramdisk:
            f.write(pad(ramdisk, page_size))
        if dtb:
            f.write(pad(dtb, page_size))

    print(f"Boot image packed: {out_path} ({os.path.getsize(out_path)} bytes)")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--kernel', required=True)
    parser.add_argument('--ramdisk', required=False, default='')
    parser.add_argument('--dtb', required=False, default='')
    parser.add_argument('--cmdline', default='console=null')
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args()
    pack_bootv2(args.kernel, args.ramdisk, args.dtb, args.output, args.cmdline)
