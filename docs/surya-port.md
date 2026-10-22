# POCO X3 NFC (`surya`) bring-up

Status: hardware inventory only. No `surya` boot image has been built or booted.
The observations below came from a rooted M2007J20CG running Android on
2026-10-22. Device serial and raw device-tree dumps are intentionally omitted.

## Confirmed hardware facts

| Area | Live `surya` value | `ios-sweet` assumption | Initial assessment |
| --- | --- | --- | --- |
| SoC | SM7150 / Snapdragon 732G | SM7150 | Same SoC family |
| RAM | `0x80000000` + `0x80000000`, `0x100000000` + `0xfcc00000` | Same two banks; upper bank for XNU | Matches |
| Splash framebuffer reservation | `0x9c000000` + `0x1700000` | Same base and size | Matches; pixel format still unverified |
| Display | Huaxing NT36672C, 1080x2400 (kernel cmdline and `wm size`) | 1080x2400 bootloader framebuffer on `sweet` | Panel initialization and framebuffer behavior unverified |
| UFS host | `0x01d84000` + `0x3000` | Same host MMIO | Matches address; controller state and partition mapping unverified |
| GIC | Distributor `0x17a00000` + `0x10000`, redistributors `0x17a60000` + `0x100000` | Same addresses | Matches |
| Touch | `novatek,NVT-ts-spi` at SPI `0x880000`, active `NVTCapacitiveTouchScreen` input | Goodix GT9896 at GENI I2C `0xa84000` | Needs a separate SPI/Novatek driver; disable `sweettouch` for early boot |

## First milestones

1. Inspect the stock `surya` boot image/DTB and the shim's boot-header assumptions. Do not reuse a `sweet` DTB or boot image.
2. Build a `surya` diagnostic shim using the matching DTB, then test via temporary `fastboot boot` only. Confirm the shim console and RAM/UFS reads before loading XNU. Do not write to UFS in this phase.
3. Generate a `surya` ADT from validated live addresses. Boot XNU with touch disabled and a diagnostic RAM disk. A kernel log is stronger evidence than a boot logo.
4. After kernel boot, validate the UFS root path and only then prepare the iOS 16.7.16 root image. Flashing it to `userdata` would erase the current Android installation and requires a separate decision and backup.
5. Add Novatek SPI touch support after the display and iOS UI work. Do not run the `sweet` Goodix I2C probe on `surya`.

The upstream project uses the iPhone X (`iPhone10,3`) iOS 16.7.16 (`20H392`)
IPSW. It is an Apple userland source, not an image that can be flashed directly
to this phone. Root-image construction in the upstream README requires Linux.
