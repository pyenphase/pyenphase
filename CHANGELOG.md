# Changelog

<!--next-version-placeholder-->

## v1.21.0 (2024-07-16)

### Feature

* **generator:** Probe for generator ([#160](https://github.com/pyenphase/pyenphase/issues/160)) ([`42a2533`](https://github.com/pyenphase/pyenphase/commit/42a2533f44ec975c72bd0be9dc70c75a987ff030))

## v1.20.6 (2024-07-03)

### Fix

*  raise EnvoyCommunicationError for httpx ConnectError and TimeoutException exceptions during Envoy.update ([#170](https://github.com/pyenphase/pyenphase/issues/170)) ([`c6d238f`](https://github.com/pyenphase/pyenphase/commit/c6d238f83b10622cb20493bcf70e4e54deb751d2))

## v1.20.5 (2024-07-03)

### Fix

* Report EnvoyHTTPStatusError for _json_request if status not in 200-300 ([#171](https://github.com/pyenphase/pyenphase/issues/171)) ([`46fb2b3`](https://github.com/pyenphase/pyenphase/commit/46fb2b386ff1991ba26d4b60628163cff147afa9))

## v1.20.4 (2024-07-02)

### Fix

* For fw 3.x mark production with only zero values as EnvoyPoorDataQuality error ([#173](https://github.com/pyenphase/pyenphase/issues/173)) ([`8b6b302`](https://github.com/pyenphase/pyenphase/commit/8b6b302b626742e101708c5bbd0c0a46e86f9cb7))

## v1.20.3 (2024-05-07)

### Fix

* Get production phase data using details parameter ([#159](https://github.com/pyenphase/pyenphase/issues/159)) ([`d2a478c`](https://github.com/pyenphase/pyenphase/commit/d2a478c25581cbb147506d138db3043c70345fae))

## v1.20.2 (2024-04-18)

### Fix

* Add missing EnvoyTokenAuth class properties ([#150](https://github.com/pyenphase/pyenphase/issues/150)) ([`d01157a`](https://github.com/pyenphase/pyenphase/commit/d01157a1ec3139f67e085f0a4e529f2e7af09943))

### Documentation

* Use new format to specify virtual env for readthedocs ([#152](https://github.com/pyenphase/pyenphase/issues/152)) ([`4b9a9ea`](https://github.com/pyenphase/pyenphase/commit/4b9a9ea79ef94dfd1fed2b262a12cb016da2802c))
* Let readthedocs use virtualenv for build ([#151](https://github.com/pyenphase/pyenphase/issues/151)) ([`9e8b648`](https://github.com/pyenphase/pyenphase/commit/9e8b648875db5fcc2210d7f180c0d278485eafb8))

## v1.20.1 (2024-03-26)

### Fix

* Endless loop on envoy unreachable ([#145](https://github.com/pyenphase/pyenphase/issues/145)) ([`f074c61`](https://github.com/pyenphase/pyenphase/commit/f074c61b56b0fdb1080ff3c54f82c59a8015b6d9))

## v1.20.0 (2024-03-21)

### Feature

* Report storage CT data ([#144](https://github.com/pyenphase/pyenphase/issues/144)) ([`52c53fe`](https://github.com/pyenphase/pyenphase/commit/52c53fe20123514177290e964e03a23454e42e9c))

## v1.19.2 (2024-03-08)

### Fix

* Consumption CT not found when 3 CT reported ([#140](https://github.com/pyenphase/pyenphase/issues/140)) ([`7c2f52c`](https://github.com/pyenphase/pyenphase/commit/7c2f52cc28fdc872a8c5875fc7f7d8b7e233bc01))

## v1.19.1 (2024-02-27)

### Fix

* Force release ([#139](https://github.com/pyenphase/pyenphase/issues/139)) ([`b16f132`](https://github.com/pyenphase/pyenphase/commit/b16f13264ffdb90de53d3d9730eb0cd700724ffd))

## v1.19.0 (2024-01-27)

### Feature

* Add envoy_model property ([#136](https://github.com/pyenphase/pyenphase/issues/136)) ([`42652cd`](https://github.com/pyenphase/pyenphase/commit/42652cda168d1cf1d4b637071f0603d0b0707066))

## v1.18.0 (2024-01-23)

### Feature

* Add updater for Current Transformer data ([#135](https://github.com/pyenphase/pyenphase/issues/135)) ([`1ca6118`](https://github.com/pyenphase/pyenphase/commit/1ca6118e6aaecb829b4cd711d72d6296fad26bae))

### Documentation

* Document CT meter data ([#134](https://github.com/pyenphase/pyenphase/issues/134)) ([`cfd396b`](https://github.com/pyenphase/pyenphase/commit/cfd396bde18a908d7703d421a10126abc06f0542))

## v1.17.0 (2024-01-11)

### Feature

* Write request reply to debuglog when in debug ([#131](https://github.com/pyenphase/pyenphase/issues/131)) ([`e255684`](https://github.com/pyenphase/pyenphase/commit/e25568444ca4a629bc38904c0f27777550219117))

### Documentation

* Reorganize and extend documentation. ([#129](https://github.com/pyenphase/pyenphase/issues/129)) ([`4d8e463`](https://github.com/pyenphase/pyenphase/commit/4d8e463fc5d5e500876f721ae2831cc90a275d9a))

## v1.16.0 (2024-01-09)

### Feature

* Provide phase data for envoy metered with ct ([#126](https://github.com/pyenphase/pyenphase/issues/126)) ([`454dbc5`](https://github.com/pyenphase/pyenphase/commit/454dbc58ebb2edf23e9c64173fb8b5d155b327fc))

## v1.15.2 (2023-12-20)

### Fix

* 3.9.x firmware with meters probe ([#128](https://github.com/pyenphase/pyenphase/issues/128)) ([`06606c5`](https://github.com/pyenphase/pyenphase/commit/06606c5516c84b3ee500843b8b843bf180658055))

## v1.15.1 (2023-12-20)

### Fix

* Skip meters endpoint if it returns a 401 ([#125](https://github.com/pyenphase/pyenphase/issues/125)) ([`166c25c`](https://github.com/pyenphase/pyenphase/commit/166c25c410b6fa319bddea78db44606da7364aeb))

## v1.15.0 (2023-12-19)

### Feature

* Provide phase configuration for envoy metered with ct ([#122](https://github.com/pyenphase/pyenphase/issues/122)) ([`12204a8`](https://github.com/pyenphase/pyenphase/commit/12204a8ec2082cb561f334e21e6febfdb2c8a082))

## v1.14.3 (2023-11-11)

### Fix

* **#99:** Envoy metered without CT reporting wrong values ([#111](https://github.com/pyenphase/pyenphase/issues/111)) ([`2188969`](https://github.com/pyenphase/pyenphase/commit/21889696fdc06f423f382eb404483e1b5d641094))

### Documentation

* Update usage.md ([#109](https://github.com/pyenphase/pyenphase/issues/109)) ([`2e31671`](https://github.com/pyenphase/pyenphase/commit/2e316718081fccab314844a76aa9c6e4e54d20a9))

## v1.14.2 (2023-11-06)

### Fix

* Make date field optional in storage settings tariff model ([#112](https://github.com/pyenphase/pyenphase/issues/112)) ([`cf98198`](https://github.com/pyenphase/pyenphase/commit/cf98198b80326f5bf57c58c77eedbe17b6142b0b))

## v1.14.1 (2023-11-02)

### Fix

* Add economy EnvoyStorageMode ([#110](https://github.com/pyenphase/pyenphase/issues/110)) ([`edaf93c`](https://github.com/pyenphase/pyenphase/commit/edaf93c8c1cd71f34bf0be227436f676b1c13772))

## v1.14.0 (2023-10-24)

### Feature

* **multiphase:** Add phase_count property to envoy ([#105](https://github.com/pyenphase/pyenphase/issues/105)) ([`39ec460`](https://github.com/pyenphase/pyenphase/commit/39ec4606b1bfc152189c48edc89396267564ac13))

## v1.13.1 (2023-10-21)

### Fix

* Ensure tariff endpoint is skipped on firmware 3 ([#102](https://github.com/pyenphase/pyenphase/issues/102)) ([`4fd7796`](https://github.com/pyenphase/pyenphase/commit/4fd77967230089ec9e86c6e6c3e237b6153abb87))

## v1.13.0 (2023-10-20)

### Feature

* Add support for changing storage mode and reserve soc ([#101](https://github.com/pyenphase/pyenphase/issues/101)) ([`16a1471`](https://github.com/pyenphase/pyenphase/commit/16a1471d7b2e961be218825151401a4cd27fe096))

## v1.12.0 (2023-10-11)

### Feature

* Add initial tariff support and charge from grid functions ([#95](https://github.com/pyenphase/pyenphase/issues/95)) ([`5418d4c`](https://github.com/pyenphase/pyenphase/commit/5418d4c99ee6a5f0998367525ccba65f0edb9bc5))

## v1.11.4 (2023-09-13)

### Fix

* Use eim if activeCount is true ([#91](https://github.com/pyenphase/pyenphase/issues/91)) ([`ac041a4`](https://github.com/pyenphase/pyenphase/commit/ac041a4abd2119fa3c784aa74634b27e118b7624))

## v1.11.3 (2023-09-13)

### Fix

* More dry contact settings should be optional ([#90](https://github.com/pyenphase/pyenphase/issues/90)) ([`4fc503a`](https://github.com/pyenphase/pyenphase/commit/4fc503a4f8f60051319aaabf386bced2cd0f3076))

## v1.11.2 (2023-09-12)

### Fix

* Disable consumption when there are no active meters ([#87](https://github.com/pyenphase/pyenphase/issues/87)) ([`fa28f1c`](https://github.com/pyenphase/pyenphase/commit/fa28f1c31344f0e2d1bc60640902e94bd55b0331))

## v1.11.1 (2023-09-12)

### Fix

* Black_s_start key not returned by all Ensemble systems ([#84](https://github.com/pyenphase/pyenphase/issues/84)) ([`357f0bd`](https://github.com/pyenphase/pyenphase/commit/357f0bd132a976f31a052063ce514ac86534de8e))

## v1.11.0 (2023-09-08)

### Feature

* Add fallback when api/v1/production endpoint is broken ([#83](https://github.com/pyenphase/pyenphase/issues/83)) ([`d7e195e`](https://github.com/pyenphase/pyenphase/commit/d7e195e498362d1374366d88a24afc8da6b01321))

## v1.10.0 (2023-09-08)

### Feature

* Add 7.6.175 fixtures with total consumption ([#81](https://github.com/pyenphase/pyenphase/issues/81)) ([`1bc2b20`](https://github.com/pyenphase/pyenphase/commit/1bc2b20a427c6d03df318fcf5c529391fc6e25ed))

## v1.9.3 (2023-09-07)

### Fix

* Handle /production returning a 401 even with the correct auth on some 3.x firmwares ([#80](https://github.com/pyenphase/pyenphase/issues/80)) ([`947605f`](https://github.com/pyenphase/pyenphase/commit/947605fba25b41d12db273e9352c29b08cac1d4d))

## v1.9.2 (2023-09-07)

### Fix

* Raise EnvoyAuthenticationRequired when local auth is incorrect ([#79](https://github.com/pyenphase/pyenphase/issues/79)) ([`208e91a`](https://github.com/pyenphase/pyenphase/commit/208e91a6a66e8afa0931bb3a78e557b882277148))

## v1.9.1 (2023-09-04)

### Fix

* Envoy default password is last 6 not first 6 ([#78](https://github.com/pyenphase/pyenphase/issues/78)) ([`33d07f6`](https://github.com/pyenphase/pyenphase/commit/33d07f6fb231a274bfdf5e693d1d2200fc0b516d))

## v1.9.0 (2023-09-03)

### Feature

* Add ivp/meters and ivp/meters/readings to fixture collector ([#77](https://github.com/pyenphase/pyenphase/issues/77)) ([`74c02bc`](https://github.com/pyenphase/pyenphase/commit/74c02bc882435f8605c85600c7f598a7e77c7141))

## v1.8.1 (2023-08-23)

### Fix

* Preemptively update dry contact state when toggling ([#75](https://github.com/pyenphase/pyenphase/issues/75)) ([`6a3f12f`](https://github.com/pyenphase/pyenphase/commit/6a3f12f26355721a4d12f3ef490659e4c4ce4a4c))

## v1.8.0 (2023-08-19)

### Feature

* Add initial support for firmware 8.1.41 ([#73](https://github.com/pyenphase/pyenphase/issues/73)) ([`3562261`](https://github.com/pyenphase/pyenphase/commit/3562261d51a2f3d539d125c3512d9b1ca9b9bd6d))

## v1.7.1 (2023-08-15)

### Fix

* Startup was blocked for multiple minutes if the envoy was offline ([#71](https://github.com/pyenphase/pyenphase/issues/71)) ([`983ef52`](https://github.com/pyenphase/pyenphase/commit/983ef52e92ffff5a91b8de8bddda68f460058b56))

## v1.7.0 (2023-08-15)

### Feature

* Add support for opening and closing dry contact relays ([#70](https://github.com/pyenphase/pyenphase/issues/70)) ([`f59aa54`](https://github.com/pyenphase/pyenphase/commit/f59aa546e4991c5aee446e9629b48df2ca556272))

## v1.6.0 (2023-08-13)

### Feature

* Add support for changing settings on dry contact relays ([#68](https://github.com/pyenphase/pyenphase/issues/68)) ([`345165a`](https://github.com/pyenphase/pyenphase/commit/345165a92ffc7ffc35c5d09626757c53f4add7d2))

## v1.5.3 (2023-08-12)

### Fix

* Add "schedule" to DryContactAction ([#67](https://github.com/pyenphase/pyenphase/issues/67)) ([`403d8dc`](https://github.com/pyenphase/pyenphase/commit/403d8dc5c0361a30b95e57fdeda13ea25fd8179a))

## v1.5.2 (2023-08-11)

### Fix

* Add EnvoyEnchargeAggregate to __all__ ([#66](https://github.com/pyenphase/pyenphase/issues/66)) ([`63b7698`](https://github.com/pyenphase/pyenphase/commit/63b76980d620cf7e125df0d6058c80230f66756a))

## v1.5.1 (2023-08-11)

### Fix

* Switch fetching aggregate Encharge data to simpler endpoint ([#65](https://github.com/pyenphase/pyenphase/issues/65)) ([`e076476`](https://github.com/pyenphase/pyenphase/commit/e07647656920779e7a18a045ddfea1dec583fba7))

## v1.5.0 (2023-08-11)

### Feature

* Add EnchargeAggregate model for aggregated battery data ([#64](https://github.com/pyenphase/pyenphase/issues/64)) ([`6985935`](https://github.com/pyenphase/pyenphase/commit/69859358ad6c4146fac30198ec5a342633db9834))

## v1.4.0 (2023-08-10)

### Feature

* Add support for toggling grid on/off ([#62](https://github.com/pyenphase/pyenphase/issues/62)) ([`63d44dd`](https://github.com/pyenphase/pyenphase/commit/63d44ddbc59d04ca6afb6b3526a37cda32c7417d))

## v1.3.0 (2023-08-09)

### Feature

* Refactor register interface to allow unregistering an updater ([#60](https://github.com/pyenphase/pyenphase/issues/60)) ([`82efcec`](https://github.com/pyenphase/pyenphase/commit/82efcec228dbe263c3f1c39e6ded3e9283fbfac2))

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
