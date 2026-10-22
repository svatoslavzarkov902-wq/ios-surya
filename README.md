# ios-surya

**Apple's iOS 16 (XNU-8796) on the Xiaomi POCO X3 NFC (`surya` / `karna`, Qualcomm Snapdragon 732G / SM7150).**

[![CI](https://github.com/MATRIX2244/ios-surya/actions/workflows/xnu.yml/badge.svg)](https://github.com/MATRIX2244/ios-surya/actions/workflows/xnu.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Device](https://img.shields.io/badge/Device-POCO%20X3%20NFC-orange.svg)](docs/surya-port.md)

This project ports Apple's open-source XNU kernel (`xnu-8796`, the iOS 16 era) to the **POCO X3 NFC** (`surya`, model `M2007J20CG`, Qualcomm SM7150 / Snapdragon 732G, Adreno 618). On top runs the **unmodified iOS 16.7.16 (20H392) userland of the iPhone X (`iPhone10,3` / `D22AP`)**: `launchd`, system daemons, `backboardd`, `SpringBoard`, and stock applications.

It builds upon the pioneering work of [dipa-studio/ios-sweet](https://github.com/dipa-studio/ios-sweet) (Redmi Note 10 Pro) and synthesizes the major breakthroughs from sibling projects:
- **[joranv1/ios-sailfish](https://github.com/joranv1/ios-sailfish)** — GPU acceleration via Mesa Freedreno, in-kernel Apple80211 Wi-Fi stack, screen brightness/sleep DSI commands, battery gauge, and offline Hactivation.
- **[MakrSas/ios-topaz](https://github.com/MakrSas/ios-topaz)** & **HackiOS** — Freedreno CoreAnimation OpenGL ES renderer (`sweetgl.dylib`) and TrustZone PAS modem glue.
- **[palazik/ios-dodge](https://github.com/palazik/ios-dodge)** — Device safety protocols, LUN0 GPT preservation, and fault reporting.
- **[ch1tmdgus/ios-v60](https://github.com/ch1tmdgus/ios-v60)** — Hardware touch driver isolation and SPMI hardware button monitoring.

> **CRITICAL SAFETY NOTICE:**
> Before any on-device testing, read [RECOVERY.md](RECOVERY.md). This project runs **strictly in RAM** via `fastboot boot` during development. Never flash unverified boot images or partition tables to your device.

---

## Hardware Comparison & Architecture

The POCO X3 NFC (`surya`) shares the **exact same Snapdragon 732G (SM7150)** platform with the Redmi Note 10 Pro (`sweet`), giving it a massive advantage over other ports:

| Component | Redmi Note 10 Pro (`sweet`) | POCO X3 NFC (`surya`) | Status / Porting Assessment |
| :--- | :--- | :--- | :--- |
| **SoC** | Qualcomm SM7150 (SD732G) | Qualcomm SM7150 (SD732G) | **100% Identical**; same CPU architecture (2x Kryo 470 Gold + 6x Silver) |
| **Translation Granule** | 16 KiB native support | 16 KiB native support | **No 4K hacks needed** (`ID_AA64MMFR0.TGran16 = 1`) |
| **RAM Mapping** | `0x80000000` + `0x100000000` | `0x80000000` + `0x100000000` | **Matches 1:1**; upper bank used for XNU |
| **Framebuffer** | `0x9c000000` (1080x2400) | `0x9c000000` (1080x2400) | **Matches 1:1** (Huaxing NT36672C panel) |
| **GICv3 Interrupts** | Dist `0x17a00000`, Redist `0x17a60000` | Dist `0x17a00000`, Redist `0x17a60000` | **Matches 1:1** |
| **Storage (UFS)** | `0x01d84000` (UFS 2.1) | `0x01d84000` (UFS 2.1) | **Matches 1:1** |
| **GPU** | Adreno 618 | Adreno 618 | Full Mesa Freedreno support via `sweetgl.dylib` |
| **Touchscreen** | Goodix GT9896 (I²C `0xa84000`) | Novatek NVT-ts-spi (SPI `0x880000`) | **Driver adaptation**: Goodix disabled, Novatek SPI driver mapped |

Full hardware register inventory: [docs/surya-port.md](docs/surya-port.md).

---

## Features & Solution Roadmap

| Area | Status | Technical Implementation |
| :--- | :--- | :--- |
| **Boot Chain** | Working | Stock Xiaomi ABL → `fastboot boot shim-boot.img` (RAM only) → XNU. Nothing flashed to boot. |
| **CPU / SMP** | Planned | All 8 Kryo 470 cores via PSCI, 16K translation granule, timers, GICv3 device interrupts. |
| **GPU Acceleration** | Ported Tools | **Adreno 618**: Mesa Freedreno GLES 3.1 inside `backboardd` as `sweetgl.dylib`. CoreAnimation OpenGL ES renderer targets 30–60 FPS. |
| **Display** | Prepared | Huaxing NT36672C panel (1080x2400) presented to iOS as iPhone X canvas (1125x2436). DSI DCS `0x51` backlight control. |
| **Touch & Keys** | In Progress | Novatek SPI (`novatek,NVT-ts-spi`) IOKit driver. Power and volume keys via SPMI observer. |
| **Wi-Fi** | Integrated | Integrated **Apple80211** stack: modem firmware booted via TrustZone PAS from `modem_a`, GLINK/QRTR, in-kernel WPA2-PSK 4-way handshake, native `en0` interface for `wifid` and Safari. |
| **Battery & Charging** | Planned | PM6150 / PM7150 fuel-gauge telemetry via IOPMPowerSource. |
| **Activation & UI** | Solved | Offline Hactivation path in `mobileactivationd`. `tools/wallpaper-heic2png.sh` converts wallpaper layers to PNG to prevent black screen. |

---

## Repository Structure

```
├── docs/                 # Hardware audit, memory maps, and technical bring-up notes
│   ├── surya-port.md     # Physical POCO X3 NFC hardware inspection
│   └── QEMU_TESTING.md   # Local emulation and diagnostics guide
├── shim/                 # Early bootloader shim (MMU, FDT parser, UFS loader, console)
├── tools/                # Build and injection toolchain
│   ├── mkiosroot-mac.sh  # Build iOS rootfs directly on macOS
│   ├── mkiosroot.sh      # Build iOS rootfs on Linux
│   ├── mkadt.py          # Apple Device Tree (ADT) generator
│   ├── wallpaper-heic2png.sh # Converts stock iOS wallpapers to PNG
│   ├── sweetgl/          # Mesa Freedreno Adreno GPU wrapper
│   └── sweetgpu-ca/      # CoreAnimation OpenGL ES presentation glue
├── xnu/patches/          # Incremental kernel patches for XNU-8796
├── RECOVERY.md           # Safety rules and emergency GPT backup procedures
└── README.md
```

---

## How to Build & Test

### 1. Build the Kernel (GitHub Actions CI)
The kernel builds automatically on macOS runners (Xcode 15 / `macos-14`) via GitHub Actions:
```sh
gh workflow run xnu.yml -R MATRIX2244/ios-surya
gh run download -R MATRIX2244/ios-surya -n xnu-kernel -D xnu/out
```

### 2. Prepare the iOS Rootfs
Download the official **iPhone X iOS 16.7.16 (20H392)** IPSW from Apple:
```sh
# Using our macOS-native script:
./tools/mkiosroot-mac.sh /path/to/iPhone10,3,iPhone10,6_16.7.16_20H392_Restore.ipsw /path/to/output_root.img
```

### 3. Generate Boot Shim & RAM Boot
```sh
# 1. Package payload with kernel, DTB, and tested boot args:
# (rd=ufsroot0 ufsrw=1 rootrw=1 unentitled_ios_sim_launch=1 launchd_unsecure_cache=1 wdt=-1)
python3 tools/mkpayload.py \
  xnu/out/kernel.development.surya \
  dtb/surya.dtb \
  out/payload.bin \
  "rd=ufsroot0 ufsrw=1 rootrw=1 unentitled_ios_sim_launch=1 launchd_unsecure_cache=1 wdt=-1 serial=0x3"

# 2. Package Android boot v2 image using standalone mkbootv2:
python3 tools/mkbootv2.py \
  --kernel shim/out/Image \
  --ramdisk out/payload.bin \
  --output out/surya-boot.img

# 3. Boot in RAM via fastboot (does NOT touch boot partition):
fastboot boot out/surya-boot.img
```

### 4. Flashing Large Rootfs to Userdata
If fastboot fails on macOS reading large raw disk images:
```sh
python3 tools/img2simg.py /path/to/rootfs.img /path/to/rootfs.simg
fastboot flash userdata /path/to/rootfs.simg
```

---

## Credits & Acknowledgements

This project stands on the shoulders of the open-source XNU community:
* **[dipa-studio/ios-sweet](https://github.com/dipa-studio/ios-sweet)** — Foundational XNU porting method on Qualcomm SM7150.
* **[joranv1/ios-sailfish](https://github.com/joranv1/ios-sailfish)** — Adreno GPU driver pipeline, Apple80211 Wi-Fi implementation, and macOS rootfs tooling.
* **[MakrSas/ios-topaz](https://github.com/MakrSas/ios-topaz)** & **[HackiOS](https://github.com/oosexgang/hackios-xnu-kernel)** — Freedreno Darwin glue and modem integration.
* **[palazik/ios-dodge](https://github.com/palazik/ios-dodge)** — Recovery procedures and UFS partition safety guidelines.
* **[ch1tmdgus/ios-v60](https://github.com/ch1tmdgus/ios-v60)** — Hardware touch isolation and button observer logic.
