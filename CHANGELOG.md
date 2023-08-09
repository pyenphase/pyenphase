# Changelog

<!--next-version-placeholder-->

## v1.2.2 (2023-08-09)

### Fix

* Remove unreachable code in inverters updater ([#61](https://github.com/pyenphase/pyenphase/issues/61)) ([`84b6be0`](https://github.com/pyenphase/pyenphase/commit/84b6be081cde7bf624baaae2b5df5c1177144dec))

## v1.2.1 (2023-08-09)

### Fix

* Incorrect typing on enpower mains_*_state attributes ([#59](https://github.com/pyenphase/pyenphase/issues/59)) ([`14c7c14`](https://github.com/pyenphase/pyenphase/commit/14c7c14124ca33df6e011b1fa32ed4c57da7e294))

## v1.2.0 (2023-08-09)

### Feature

* Refactor to break updaters into modules ([#54](https://github.com/pyenphase/pyenphase/issues/54)) ([`a4686a3`](https://github.com/pyenphase/pyenphase/commit/a4686a30be37f88a3af27257b4a8d017d1579122))

## v1.1.4 (2023-08-08)

### Fix

* Return DryContactStatus enum for status ([#53](https://github.com/pyenphase/pyenphase/issues/53)) ([`d366ff3`](https://github.com/pyenphase/pyenphase/commit/d366ff3c86a3419bb0ffcbd24a1edb0333b0a32f))

## v1.1.3 (2023-08-08)

### Fix

* Handle envoy sending bad json ([#52](https://github.com/pyenphase/pyenphase/issues/52)) ([`7109e66`](https://github.com/pyenphase/pyenphase/commit/7109e6604f5fc1d1b197a128ceb264c9e00410d4))

## v1.1.2 (2023-08-08)

### Fix

* Adjust timeouts for when envoy is having trouble with DNS ([#51](https://github.com/pyenphase/pyenphase/issues/51)) ([`c82f9bb`](https://github.com/pyenphase/pyenphase/commit/c82f9bbf69f884516985dde04207d375c4953ad3))

## v1.1.1 (2023-08-08)

### Fix

* Add Enpower and DryContact classes to __all__ ([#50](https://github.com/pyenphase/pyenphase/issues/50)) ([`d37b5e9`](https://github.com/pyenphase/pyenphase/commit/d37b5e9b6e6f12d62ba57a2f6d745868adf67914))

## v1.1.0 (2023-08-08)

### Feature

* Add support for pulling dry contact data ([#48](https://github.com/pyenphase/pyenphase/issues/48)) ([`7814650`](https://github.com/pyenphase/pyenphase/commit/78146506bb4a93b51987a2b8725cc32f35368643))

## v1.0.0 (2023-08-08)

### Breaking

* drop python3.10 support ([#49](https://github.com/pyenphase/pyenphase/issues/49)) ([`9d8c20d`](https://github.com/pyenphase/pyenphase/commit/9d8c20d8f1d9b08b57649f7c8b84715f25312887))

## v0.18.0 (2023-08-08)

### Feature

* Add support for polling Enpower data ([#47](https://github.com/pyenphase/pyenphase/issues/47)) ([`0ac58e0`](https://github.com/pyenphase/pyenphase/commit/0ac58e0396d67b4e858deba08eb6bef5c6de9f39))

## v0.17.0 (2023-08-07)

### Feature

* Add fixtures for 7.6.114 without clamps ([#44](https://github.com/pyenphase/pyenphase/issues/44)) ([`4be0a33`](https://github.com/pyenphase/pyenphase/commit/4be0a339ed9ae458246f2260e03c5d4c89c58410))

## v0.16.0 (2023-08-07)

### Feature

* Collect headers as well as XML files ([#43](https://github.com/pyenphase/pyenphase/issues/43)) ([`82678be`](https://github.com/pyenphase/pyenphase/commit/82678be2bdcd59b77befc04883b2bb4693789f36))
* Update 7.6.175 fixtures ([#45](https://github.com/pyenphase/pyenphase/issues/45)) ([`9c96475`](https://github.com/pyenphase/pyenphase/commit/9c96475f345786a24b5b786a4880a949a01cabd8))

## v0.15.1 (2023-08-07)

### Fix

* Add Encharge classes to __all__ ([#42](https://github.com/pyenphase/pyenphase/issues/42)) ([`229a84d`](https://github.com/pyenphase/pyenphase/commit/229a84df72a1ec6292f47fe426c46890feb1b83e))

## v0.15.0 (2023-08-07)

### Feature

* Add Encharge battery support ([#40](https://github.com/pyenphase/pyenphase/issues/40)) ([`e1a96e9`](https://github.com/pyenphase/pyenphase/commit/e1a96e9de3ade6429561ef863ed8302b481e02df))

## v0.14.1 (2023-08-07)

### Fix

* Probe failures with 5.0.62 firmware ([#38](https://github.com/pyenphase/pyenphase/issues/38)) ([`314df6d`](https://github.com/pyenphase/pyenphase/commit/314df6d83c4dfd7c91970e61f86e34218ce46be8))

## v0.14.0 (2023-08-06)

### Feature

* Add part number ([#36](https://github.com/pyenphase/pyenphase/issues/36)) ([`5b1d46d`](https://github.com/pyenphase/pyenphase/commit/5b1d46dd7c64180fff3118b087330a48de6646fe))

## v0.13.0 (2023-08-06)

### Feature

* Add fixture collecting script ([#30](https://github.com/pyenphase/pyenphase/issues/30)) ([`5d66ee9`](https://github.com/pyenphase/pyenphase/commit/5d66ee96154bbd6238a27b6e449b6bb0aece3a54))

## v0.12.0 (2023-08-06)

### Feature

* Probe for Encharge and Enpower support ([#26](https://github.com/pyenphase/pyenphase/issues/26)) ([`da2db7d`](https://github.com/pyenphase/pyenphase/commit/da2db7d8005c81153dff6b5802d3c4851dd79432))

## v0.11.0 (2023-08-06)

### Feature

* Add support for bifurcated endpoints ([#28](https://github.com/pyenphase/pyenphase/issues/28)) ([`7853cfd`](https://github.com/pyenphase/pyenphase/commit/7853cfd1ecb2e1cadf8e874f6d351c4efe408a79))

## v0.10.0 (2023-08-06)

### Feature

* Add the ability to refresh the token on demand ([#25](https://github.com/pyenphase/pyenphase/issues/25)) ([`d1e391c`](https://github.com/pyenphase/pyenphase/commit/d1e391ccd9fcc9fcb3636f6f4a101005998f9f60))

## v0.9.0 (2023-08-05)

### Feature

* Add EnvoyTokenAuth to __all__ ([#24](https://github.com/pyenphase/pyenphase/issues/24)) ([`738f4c7`](https://github.com/pyenphase/pyenphase/commit/738f4c7b1385e1045e9ca5065e06b0816d6a398f))

## v0.8.0 (2023-08-05)

### Feature

* Add EnvoyData to __all__ ([#23](https://github.com/pyenphase/pyenphase/issues/23)) ([`63f9ba9`](https://github.com/pyenphase/pyenphase/commit/63f9ba94f7d10945aa314836f9a7425cda28ae59))

## v0.7.1 (2023-08-05)

### Fix

* Legacy installer auth was not working ([#22](https://github.com/pyenphase/pyenphase/issues/22)) ([`a2dd5e5`](https://github.com/pyenphase/pyenphase/commit/a2dd5e55ccfc796d7e162ccc75bb116fde1ca631))

## v0.7.0 (2023-08-05)

### Feature

* Export a few more models for type checking ([#21](https://github.com/pyenphase/pyenphase/issues/21)) ([`e2337c4`](https://github.com/pyenphase/pyenphase/commit/e2337c4b8bf69e816611e76e4239fdbea78bf6e9))

## v0.6.1 (2023-08-05)

### Fix

* Unclosed cloud client session ([#20](https://github.com/pyenphase/pyenphase/issues/20)) ([`b46282a`](https://github.com/pyenphase/pyenphase/commit/b46282a9f9ed20be4487582cd2461a02b7740de6))

## v0.6.0 (2023-08-05)

### Feature

* Export names at top level ([#19](https://github.com/pyenphase/pyenphase/issues/19)) ([`b209357`](https://github.com/pyenphase/pyenphase/commit/b2093578d12978da49788ca08c3959d2c3fb3641))

## v0.5.0 (2023-08-05)

### Feature

* Add consumption api ([#17](https://github.com/pyenphase/pyenphase/issues/17)) ([`f094c4d`](https://github.com/pyenphase/pyenphase/commit/f094c4d129cbb26e0f6bf3cf9024967a0def46e7))

## v0.4.0 (2023-08-05)

### Feature

* Add update functions ([#16](https://github.com/pyenphase/pyenphase/issues/16)) ([`d2802e0`](https://github.com/pyenphase/pyenphase/commit/d2802e0e9322050d37e0affa4a87f127731c29a2))

## v0.3.0 (2023-07-26)

### Feature

* Add support for legacy firmware ([#11](https://github.com/pyenphase/pyenphase/issues/11)) ([`49cb15c`](https://github.com/pyenphase/pyenphase/commit/49cb15c58cde38dc41ff30c24c3365c491605274))

## v0.2.0 (2023-07-26)

### Feature

* Use sessionId cookie to have access to some endpoints ([#7](https://github.com/pyenphase/pyenphase/issues/7)) ([`09a1a8a`](https://github.com/pyenphase/pyenphase/commit/09a1a8aa30f2e3be1aa636f2488dc736f4d4f476))

## v0.1.0 (2023-05-28)
### Feature
* Add initial cloud auth support ([#6](https://github.com/pyenphase/pyenphase/issues/6)) ([`28f4872`](https://github.com/pyenphase/pyenphase/commit/28f4872625a01ee209153d489de566b7ba2302e6))

## v0.0.3 (2023-05-23)
### Fix
* Permission ([`89f9399`](https://github.com/pyenphase/pyenphase/commit/89f9399bccafcc611d83e264d8f4795d43a7f34e))
* Permission ([`c73e3ed`](https://github.com/pyenphase/pyenphase/commit/c73e3ed86106d6a9b4ea78c37c1a3133ef0af458))
* Permission ([`39e5209`](https://github.com/pyenphase/pyenphase/commit/39e520904e649bb37bd13c790d221b455b4dc90b))
* Permission ([`2068511`](https://github.com/pyenphase/pyenphase/commit/2068511f19a8c2c9ac8322937c830762cba27a16))
* Test publish ([#2](https://github.com/pyenphase/pyenphase/issues/2)) ([`e3df6b2`](https://github.com/pyenphase/pyenphase/commit/e3df6b264ca55dc12b75dd602cc1f92fa3a54950))
* Update ci python version ([#1](https://github.com/pyenphase/pyenphase/issues/1)) ([`4c2dd2e`](https://github.com/pyenphase/pyenphase/commit/4c2dd2e70464b884b9d8a02ccaf39f04f46ab270))
* Drop 3.12 ([`8e0c0f4`](https://github.com/pyenphase/pyenphase/commit/8e0c0f40ad38152bc13a85566d67c7e86345d291))
* Lint ([`683691c`](https://github.com/pyenphase/pyenphase/commit/683691c730e1ef4c491348d66dce70cd75917fd1))
* Typing ([`a75ae30`](https://github.com/pyenphase/pyenphase/commit/a75ae303ef4f98cfafe95081901df7ce88f4fb9e))
* Bump versions ([`eef5623`](https://github.com/pyenphase/pyenphase/commit/eef56234a9353d110b174b445da1cfb4034d7c1f))
