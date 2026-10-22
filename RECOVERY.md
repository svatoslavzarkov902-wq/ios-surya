# POCO X3 NFC (`surya`) — On-Device Safety & Recovery Protocol

Read this carefully before booting anything on your physical device. In sibling ports (such as `MakrSas/ios-topaz`), buggy UFS driver writes caused corruption to LUN0, wiping out partition tables and bricks. Following these protocols guarantees you will **never** brick your phone.

---

## The Golden Rules

### ❌ NEVER DO:
1. **Never use `fastboot flash boot ...` or `fastboot flash recovery ...`** during early bring-up. Always use RAM boot: `fastboot boot <image>`.
2. **Never flash any `gpt_*.bin`** or run `fastboot flash partition ...`.
3. **Never erase or format critical partitions** (`fastboot erase <part>` or `fastboot format <part>`).
4. **Never boot XNU with write-enabled flags** (`ufsrw=1` or `rootrw=1`) until the UFS driver has been verified as read-only safe.

### ✅ ALWAYS DO:
1. **Always boot temporarily in RAM**: `fastboot boot shim-boot.img`. A power-cycle immediately returns the phone to Android/recovery untouched.
2. **Keep the bootloader unlocked.**
3. **Backup critical unique partitions before doing anything else.**

---

## 1. Back Up Unique Radio & Calibration Partitions
These partitions contain unique device calibration, Wi-Fi MAC address, and IMEI data that **cannot be downloaded from any stock ROM**:
- `modemst1`
- `modemst2`
- `fsg`
- `fsc`
- `persist`

From a root shell (in TWRP, OrangeFox, or rooted Android):
```sh
adb shell "su -c 'dd if=/dev/block/bootdevice/by-name/persist of=/sdcard/persist.img'"
adb shell "su -c 'dd if=/dev/block/bootdevice/by-name/modemst1 of=/sdcard/modemst1.img'"
adb shell "su -c 'dd if=/dev/block/bootdevice/by-name/modemst2 of=/sdcard/modemst2.img'"
adb shell "su -c 'dd if=/dev/block/bootdevice/by-name/fsg of=/sdcard/fsg.img'"
adb shell "su -c 'dd if=/dev/block/bootdevice/by-name/fsc of=/sdcard/fsc.img'"
adb pull /sdcard/persist.img .
adb pull /sdcard/modemst1.img .
adb pull /sdcard/modemst2.img .
adb pull /sdcard/fsg.img .
adb pull /sdcard/fsc.img .
```
Store these files in a safe external location.

---

## 2. Back Up LUN0 Partition Table (GPT)
LUN0 is the main physical UFS storage block (`/dev/block/sda`). Back up both the primary GPT (first 1 MiB) and secondary backup GPT (last 1 MiB):

```sh
# 1. Primary GPT (first 1 MiB)
adb exec-out "su -c 'dd if=/dev/block/sda bs=1M count=1'" > lun0-head-1MiB.bin

# 2. Backup GPT (last 1 MiB)
S=$(adb shell "su -c 'blockdev --getsz /dev/block/sda'" | tr -d '')
adb exec-out "su -c 'dd if=/dev/block/sda bs=512 skip=$((S-2048)) count=2048'" > lun0-tail-1MiB.bin

# 3. Text partition map
adb shell "su -c 'sgdisk -p /dev/block/sda'" > lun0-sgdisk.txt 2>/dev/null || true
```

---

## 3. Recovery Procedures

### If the phone reboots during an experiment:
* Since no partitions were flashed, simply hold the **Power** button to reboot into normal Android.

### If fastboot mode is needed:
* Hold **Power + Volume Down** until the Fastboot logo appears.

### If recovery mode is needed (OrangeFox / TWRP):
* Hold **Power + Volume Up** until the custom recovery appears.
