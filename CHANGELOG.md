# CHANGELOG


## v1.26.0 (2025-04-25)

### Chores

- **deps**: Bump lxml from 5.3.1 to 5.3.2 ([#262](https://github.com/pyenphase/pyenphase/pull/262),
  [`eea42ef`](https://github.com/pyenphase/pyenphase/commit/eea42ef0700ca583728a650dfec6c96fbe18f74b))

Bumps [lxml](https://github.com/lxml/lxml) from 5.3.1 to 5.3.2. - [Release
  notes](https://github.com/lxml/lxml/releases) -
  [Changelog](https://github.com/lxml/lxml/blob/master/CHANGES.txt) -
  [Commits](https://github.com/lxml/lxml/compare/lxml-5.3.1...lxml-5.3.2)

--- updated-dependencies: - dependency-name: lxml dependency-version: 5.3.2

dependency-type: direct:production

update-type: version-update:semver-patch ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps**: Bump tenacity from 9.0.0 to 9.1.2
  ([#263](https://github.com/pyenphase/pyenphase/pull/263),
  [`7a3e38b`](https://github.com/pyenphase/pyenphase/commit/7a3e38b0fdb0d46a32f4b43e1efc86c07383af80))

Bumps [tenacity](https://github.com/jd/tenacity) from 9.0.0 to 9.1.2. - [Release
  notes](https://github.com/jd/tenacity/releases) -
  [Commits](https://github.com/jd/tenacity/compare/9.0.0...9.1.2)

--- updated-dependencies: - dependency-name: tenacity dependency-version: 9.1.2

dependency-type: direct:production

update-type: version-update:semver-minor ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps-dev**: Bump pytest-cov from 6.0.0 to 6.1.1
  ([#264](https://github.com/pyenphase/pyenphase/pull/264),
  [`aa99971`](https://github.com/pyenphase/pyenphase/commit/aa99971016ca1808a1a90f704c4771ec754d2e97))

Bumps [pytest-cov](https://github.com/pytest-dev/pytest-cov) from 6.0.0 to 6.1.1. -
  [Changelog](https://github.com/pytest-dev/pytest-cov/blob/master/CHANGELOG.rst) -
  [Commits](https://github.com/pytest-dev/pytest-cov/compare/v6.0.0...v6.1.1)

--- updated-dependencies: - dependency-name: pytest-cov dependency-version: 6.1.1

dependency-type: direct:development

update-type: version-update:semver-minor ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **pre-commit.ci**: Pre-commit autoupdate ([#265](https://github.com/pyenphase/pyenphase/pull/265),
  [`5f5b120`](https://github.com/pyenphase/pyenphase/commit/5f5b12053df3c4165c2e6df130afafeeeeb703b1))

- **pre-commit.ci**: Pre-commit autoupdate ([#266](https://github.com/pyenphase/pyenphase/pull/266),
  [`ff371d0`](https://github.com/pyenphase/pyenphase/commit/ff371d0b24292d73605b41e437a74c3d31efde0d))

- **pre-commit.ci**: Pre-commit autoupdate ([#267](https://github.com/pyenphase/pyenphase/pull/267),
  [`e3f555c`](https://github.com/pyenphase/pyenphase/commit/e3f555c246561f35c1befee1a25c880485803829))

updates: - [github.com/astral-sh/ruff-pre-commit: v0.11.5 →
  v0.11.6](https://github.com/astral-sh/ruff-pre-commit/compare/v0.11.5...v0.11.6)

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

### Features

- Add method to return envoy active interface settings
  ([#268](https://github.com/pyenphase/pyenphase/pull/268),
  [`70ff7ac`](https://github.com/pyenphase/pyenphase/commit/70ff7ac6e1a01b6ea62e1ea6df2638cddd4215e1))

* feat: add method to return envoy active interface settings

---------

Co-authored-by: coderabbitai[bot] <136622811+coderabbitai[bot]@users.noreply.github.com>

### Testing

- De-duplicate fixture loading by using single fixture load function
  ([#261](https://github.com/pyenphase/pyenphase/pull/261),
  [`8ec3fba`](https://github.com/pyenphase/pyenphase/commit/8ec3fba4c1769bd1df702b5db182ec18cb0a6d2c))

* test: de-duplicate fixture loading by using single function

* test: run blocking calls in executor


## v1.25.5 (2025-04-02)

### Bug Fixes

- V4 metered without cons CT crashes with KeyError: 'measurementType'
  ([#259](https://github.com/pyenphase/pyenphase/pull/259),
  [`da11b5b`](https://github.com/pyenphase/pyenphase/commit/da11b5bd84463188e6f98eb823a1a2f8420fde60))

* fix: v4 metered without cons CT crashes with KeyError: 'measurementType' * Ignore meter if
  activeCount is zero * Make meters statusFlags optional

### Chores

- Restore some legacy poetry keys to fix dependabot
  ([#232](https://github.com/pyenphase/pyenphase/pull/232),
  [`48e930e`](https://github.com/pyenphase/pyenphase/commit/48e930e51ceb9bada135b7fa6a064dc36c5b78de))

- Update dependabot.yml to force re-run attempt
  ([#231](https://github.com/pyenphase/pyenphase/pull/231),
  [`baabe6e`](https://github.com/pyenphase/pyenphase/commit/baabe6e5ddfe3f13c75c8b638b90f96cb7c990ec))

- Update dependabot.yml to force rerun
  ([`ba8f487`](https://github.com/pyenphase/pyenphase/commit/ba8f487f1f036304b7433276fffb23a3c77dc436))

- Update dev status to production/stable ([#243](https://github.com/pyenphase/pyenphase/pull/243),
  [`d97f24c`](https://github.com/pyenphase/pyenphase/commit/d97f24cb14451ea75d16e43e796e0ea968c38ff7))

- **ci**: Bump the github-actions group with 2 updates
  ([#247](https://github.com/pyenphase/pyenphase/pull/247),
  [`31475ff`](https://github.com/pyenphase/pyenphase/commit/31475ffd7772b5bab3915c29aa2f52e789f8aec1))

- **deps**: Bump orjson from 3.10.15 to 3.10.16
  ([#256](https://github.com/pyenphase/pyenphase/pull/256),
  [`abfd861`](https://github.com/pyenphase/pyenphase/commit/abfd8617dd006b3d40ac8a08bcef222c9ad14928))

- **deps**: Bump tenacity from 8.2.3 to 9.0.0
  ([#236](https://github.com/pyenphase/pyenphase/pull/236),
  [`dffeee0`](https://github.com/pyenphase/pyenphase/commit/dffeee0becae187b154e8c63b56ccfdd6b6abaae))

* chore(deps): bump tenacity from 8.2.3 to 9.0.0

Bumps [tenacity](https://github.com/jd/tenacity) from 8.2.3 to 9.0.0. - [Release
  notes](https://github.com/jd/tenacity/releases) -
  [Commits](https://github.com/jd/tenacity/compare/8.2.3...9.0.0)

--- updated-dependencies: - dependency-name: tenacity dependency-type: direct:production

update-type: version-update:semver-major ...

Signed-off-by: dependabot[bot] <support@github.com>

* chore: lock due to https://github.com/dependabot/dependabot-core/pull/11275

* chore: replace tenacity .retry.statistics by .statistics

---------

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

Co-authored-by: J. Nick Koston <nick@koston.org>

Co-authored-by: Arie Catsman <catsmanac@outlook.com>

- **deps-dev**: Bump jinja2 from 3.1.5 to 3.1.6
  ([#251](https://github.com/pyenphase/pyenphase/pull/251),
  [`f0b50de`](https://github.com/pyenphase/pyenphase/commit/f0b50dea3f98374821d0d01055d95c3bcba0ff65))

Bumps [jinja2](https://github.com/pallets/jinja) from 3.1.5 to 3.1.6. - [Release
  notes](https://github.com/pallets/jinja/releases) -
  [Changelog](https://github.com/pallets/jinja/blob/main/CHANGES.rst) -
  [Commits](https://github.com/pallets/jinja/compare/3.1.5...3.1.6)

--- updated-dependencies: - dependency-name: jinja2 dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps-dev**: Bump myst-parser from 4.0.0 to 4.0.1
  ([#240](https://github.com/pyenphase/pyenphase/pull/240),
  [`5423632`](https://github.com/pyenphase/pyenphase/commit/54236321c624e980a537fb6b7af01e5d1a14fc45))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

Co-authored-by: J. Nick Koston <nick@koston.org>

- **deps-dev**: Bump pytest from 7.4.4 to 8.3.4
  ([#235](https://github.com/pyenphase/pyenphase/pull/235),
  [`199bd4a`](https://github.com/pyenphase/pyenphase/commit/199bd4a9cbe3c96a6abbee8a2c0b2dc4371e3a26))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

Co-authored-by: J. Nick Koston <nick@koston.org>

- **deps-dev**: Bump pytest from 8.3.4 to 8.3.5
  ([#248](https://github.com/pyenphase/pyenphase/pull/248),
  [`fb8ad43`](https://github.com/pyenphase/pyenphase/commit/fb8ad430a676ce43d22e9210d5e18e06eab3606d))

* chore(deps-dev): bump pytest from 8.3.4 to 8.3.5

Bumps [pytest](https://github.com/pytest-dev/pytest) from 8.3.4 to 8.3.5. - [Release
  notes](https://github.com/pytest-dev/pytest/releases) -
  [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst) -
  [Commits](https://github.com/pytest-dev/pytest/compare/8.3.4...8.3.5)

--- updated-dependencies: - dependency-name: pytest dependency-type: direct:development

update-type: version-update:semver-patch ...

Signed-off-by: dependabot[bot] <support@github.com>

* chore: update poetry.lock

---------

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

Co-authored-by: Arie Catsman <catsmanac@outlook.com>

- **deps-dev**: Bump pytest-asyncio from 0.21.2 to 0.25.3
  ([#239](https://github.com/pyenphase/pyenphase/pull/239),
  [`24ab1c0`](https://github.com/pyenphase/pyenphase/commit/24ab1c0c36a1b5fcdcce7c4d948f7bed7d34445e))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

Co-authored-by: J. Nick Koston <nick@koston.org>

- **deps-dev**: Bump pytest-asyncio from 0.25.3 to 0.26.0
  ([#257](https://github.com/pyenphase/pyenphase/pull/257),
  [`9f73bce`](https://github.com/pyenphase/pyenphase/commit/9f73bce62b15fed33082a36ff5f8b150eef0eaf5))

- **deps-dev**: Bump sphinx from 7.3.7 to 8.1.3
  ([#234](https://github.com/pyenphase/pyenphase/pull/234),
  [`6310f28`](https://github.com/pyenphase/pyenphase/commit/6310f2881e5b7250b69885a2344bbdf6d71f7933))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

Co-authored-by: J. Nick Koston <nick@koston.org>

- **deps-dev**: Bump sphinx-autodoc-typehints from 1.25.3 to 3.0.1
  ([#233](https://github.com/pyenphase/pyenphase/pull/233),
  [`29ca29d`](https://github.com/pyenphase/pyenphase/commit/29ca29dd8e97b59a427d7fe017ea5bc34411c238))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

Co-authored-by: J. Nick Koston <nick@koston.org>

- **deps-dev**: Bump sphinx-rtd-theme from 2.0.0 to 3.0.2
  ([#237](https://github.com/pyenphase/pyenphase/pull/237),
  [`7d4498b`](https://github.com/pyenphase/pyenphase/commit/7d4498b2327f1e39a524668f578c923636d2a783))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

Co-authored-by: J. Nick Koston <nick@koston.org>

- **deps-dev**: Bump syrupy from 4.8.1 to 4.8.2
  ([#245](https://github.com/pyenphase/pyenphase/pull/245),
  [`351036f`](https://github.com/pyenphase/pyenphase/commit/351036fa541075073c5bec8c30cfdf1dfc02a613))

* chore(deps-dev): bump syrupy from 4.8.1 to 4.8.2

Bumps [syrupy](https://github.com/syrupy-project/syrupy) from 4.8.1 to 4.8.2. - [Release
  notes](https://github.com/syrupy-project/syrupy/releases) -
  [Changelog](https://github.com/syrupy-project/syrupy/blob/main/CHANGELOG.md) -
  [Commits](https://github.com/syrupy-project/syrupy/compare/v4.8.1...v4.8.2)

--- updated-dependencies: - dependency-name: syrupy dependency-type: direct:development

update-type: version-update:semver-patch ...

Signed-off-by: dependabot[bot] <support@github.com>

* chore: rebuild poetry.lock

---------

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

Co-authored-by: Arie Catsman <catsmanac@outlook.com>

- **deps-dev**: Bump syrupy from 4.8.2 to 4.9.0
  ([#250](https://github.com/pyenphase/pyenphase/pull/250),
  [`107e0c6`](https://github.com/pyenphase/pyenphase/commit/107e0c6e9829dafd0dca90ea754c4a408d0e8b4e))

Bumps [syrupy](https://github.com/syrupy-project/syrupy) from 4.8.2 to 4.9.0. - [Release
  notes](https://github.com/syrupy-project/syrupy/releases) -
  [Changelog](https://github.com/syrupy-project/syrupy/blob/main/CHANGELOG.md) -
  [Commits](https://github.com/syrupy-project/syrupy/compare/v4.8.2...v4.9.0)

--- updated-dependencies: - dependency-name: syrupy dependency-type: direct:development

update-type: version-update:semver-minor ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps-dev**: Bump syrupy from 4.9.0 to 4.9.1
  ([#254](https://github.com/pyenphase/pyenphase/pull/254),
  [`7f964d2`](https://github.com/pyenphase/pyenphase/commit/7f964d2e6dafed0dc62cf38a542c61e11c8fe2c6))

Bumps [syrupy](https://github.com/syrupy-project/syrupy) from 4.9.0 to 4.9.1. - [Release
  notes](https://github.com/syrupy-project/syrupy/releases) -
  [Changelog](https://github.com/syrupy-project/syrupy/blob/main/CHANGELOG.md) -
  [Commits](https://github.com/syrupy-project/syrupy/compare/v4.9.0...v4.9.1)

--- updated-dependencies: - dependency-name: syrupy dependency-type: direct:development

update-type: version-update:semver-patch ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **pre-commit.ci**: Pre-commit autoupdate ([#241](https://github.com/pyenphase/pyenphase/pull/241),
  [`df71b5c`](https://github.com/pyenphase/pyenphase/commit/df71b5c3de495acaab0d484ff732b9044279b4f5))

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- **pre-commit.ci**: Pre-commit autoupdate ([#246](https://github.com/pyenphase/pyenphase/pull/246),
  [`9878d8f`](https://github.com/pyenphase/pyenphase/commit/9878d8fb0e4946bf1a2566fd72c6100b4c300464))

updates: - [github.com/astral-sh/ruff-pre-commit: v0.9.6 →
  v0.9.7](https://github.com/astral-sh/ruff-pre-commit/compare/v0.9.6...v0.9.7)

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- **pre-commit.ci**: Pre-commit autoupdate ([#249](https://github.com/pyenphase/pyenphase/pull/249),
  [`78547ef`](https://github.com/pyenphase/pyenphase/commit/78547efabf80242680498c801823ee8f661c535a))

updates: - [github.com/astral-sh/ruff-pre-commit: v0.9.7 →
  v0.9.9](https://github.com/astral-sh/ruff-pre-commit/compare/v0.9.7...v0.9.9)

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- **pre-commit.ci**: Pre-commit autoupdate ([#252](https://github.com/pyenphase/pyenphase/pull/252),
  [`ea01214`](https://github.com/pyenphase/pyenphase/commit/ea012147bb5b18efc6f3f6d831708af23f5cc438))

- **pre-commit.ci**: Pre-commit autoupdate ([#253](https://github.com/pyenphase/pyenphase/pull/253),
  [`3601946`](https://github.com/pyenphase/pyenphase/commit/3601946bed60eea298f215735fc0695d15af55d2))

* chore(pre-commit.ci): pre-commit autoupdate

updates: - [github.com/astral-sh/ruff-pre-commit: v0.9.10 →
  v0.11.0](https://github.com/astral-sh/ruff-pre-commit/compare/v0.9.10...v0.11.0)

* refactor: remove unneeded int cast based on ruf046

---------

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

Co-authored-by: Arie Catsman <catsmanac@outlook.com>

- **pre-commit.ci**: Pre-commit autoupdate ([#255](https://github.com/pyenphase/pyenphase/pull/255),
  [`20772e5`](https://github.com/pyenphase/pyenphase/commit/20772e5039e24983fbc2c030bd881dc044b925e5))

updates: - [github.com/astral-sh/ruff-pre-commit: v0.11.0 →
  v0.11.2](https://github.com/astral-sh/ruff-pre-commit/compare/v0.11.0...v0.11.2)

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- **pre-commit.ci**: Pre-commit autoupdate ([#258](https://github.com/pyenphase/pyenphase/pull/258),
  [`153787d`](https://github.com/pyenphase/pyenphase/commit/153787d76070f30504dd41847b2863ca2471535d))

updates: - [github.com/python-poetry/poetry: 2.1.1 →
  2.1.2](https://github.com/python-poetry/poetry/compare/2.1.1...2.1.2)

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

### Documentation

- Reorganize and update usage documentation
  ([#244](https://github.com/pyenphase/pyenphase/pull/244),
  [`37d107b`](https://github.com/pyenphase/pyenphase/commit/37d107be3e9f87d02fe45d6abd36b4f8f25004fb))

* docs: reorganize and update usage documentation

---------

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

Co-authored-by: J. Nick Koston <nick@koston.org>

- Replace black badge by ruff badge in readme
  ([#242](https://github.com/pyenphase/pyenphase/pull/242),
  [`d3fb541`](https://github.com/pyenphase/pyenphase/commit/d3fb541e342377e0eed98d6c8561f99deb9b3a2f))

- Update docstring examples to reflect ruff formatting rules.
  ([#238](https://github.com/pyenphase/pyenphase/pull/238),
  [`ede8786`](https://github.com/pyenphase/pyenphase/commit/ede87866a41cd55403c12031058cef28fc0c4852))


## v1.25.4 (2025-02-11)

### Bug Fixes

- Add missing requires-python key to project
  ([#230](https://github.com/pyenphase/pyenphase/pull/230),
  [`8f48344`](https://github.com/pyenphase/pyenphase/commit/8f48344d4b4e73ba54548979355d0a6ab3c8fbff))

### Chores

- Add Python 3.13 to the CI ([#213](https://github.com/pyenphase/pyenphase/pull/213),
  [`3678102`](https://github.com/pyenphase/pyenphase/commit/36781022234d9efd5beefe02e5394908c97737e4))

- Bump pytest-asyncio to 0.21.2 ([#226](https://github.com/pyenphase/pyenphase/pull/226),
  [`098fa61`](https://github.com/pyenphase/pyenphase/commit/098fa61f0f262dbd84fc7773a0bf71a6b353ff33))

- Modify dependabot config to force re-run ([#219](https://github.com/pyenphase/pyenphase/pull/219),
  [`77c5f75`](https://github.com/pyenphase/pyenphase/commit/77c5f75bea06539698b12a897a8bfff7a6f329da))

- Switch to ruff to replace black/isort/flake8
  ([#217](https://github.com/pyenphase/pyenphase/pull/217),
  [`716eca6`](https://github.com/pyenphase/pyenphase/commit/716eca6a9bd7f80e98734d88f2c4d0a897368167))

- Update anyio in poetry.lock ([#224](https://github.com/pyenphase/pyenphase/pull/224),
  [`51d496c`](https://github.com/pyenphase/pyenphase/commit/51d496c91ff2c5953980da32a2899a7eb8b604e9))

- Update certifi to 2025.1.31 ([#227](https://github.com/pyenphase/pyenphase/pull/227),
  [`b9ad2a2`](https://github.com/pyenphase/pyenphase/commit/b9ad2a25d2f6887c9b0110a0e6a957e636ec67f7))

- Update dependabot.yml to retrigger run
  ([`20fc3bb`](https://github.com/pyenphase/pyenphase/commit/20fc3bb0b74a64bb45642c662925722e3a12c1aa))

- Update httpcore in poetry.lock ([#223](https://github.com/pyenphase/pyenphase/pull/223),
  [`f284b80`](https://github.com/pyenphase/pyenphase/commit/f284b80199cf570a4fe1c2fe8200ee41d964849b))

- Update httpx in the poetry lock ([#220](https://github.com/pyenphase/pyenphase/pull/220),
  [`e3d5717`](https://github.com/pyenphase/pyenphase/commit/e3d5717dd4d2f02bcf91b76a36c2845e62cbd676))

- Update idna in poetry lock ([#222](https://github.com/pyenphase/pyenphase/pull/222),
  [`cbf3b28`](https://github.com/pyenphase/pyenphase/commit/cbf3b28efc95bb97fc838f437328ce0c597b28fd))

- Update packaging to 24.2 ([#229](https://github.com/pyenphase/pyenphase/pull/229),
  [`828e960`](https://github.com/pyenphase/pyenphase/commit/828e96027ed4b13484280e236af506c3a4973860))

- Update pluggy to 1.5.0 ([#228](https://github.com/pyenphase/pyenphase/pull/228),
  [`c7b042e`](https://github.com/pyenphase/pyenphase/commit/c7b042ecf16d0fa0b3eef1587f4ab68b68719eb6))

- Update pyjwt in poetry.lock ([#225](https://github.com/pyenphase/pyenphase/pull/225),
  [`9d1b4ba`](https://github.com/pyenphase/pyenphase/commit/9d1b4bab44d463c8c1236e3432c41821ecfab653))

- Update pyupgrade to Python 3.10+ ([#216](https://github.com/pyenphase/pyenphase/pull/216),
  [`5278800`](https://github.com/pyenphase/pyenphase/commit/5278800f2de866cd1149096647b5f10052ae0eba))

- Update requests in poetry.lock ([#221](https://github.com/pyenphase/pyenphase/pull/221),
  [`8d19c79`](https://github.com/pyenphase/pyenphase/commit/8d19c79294e2d01628948ff192cd24071a38941f))

- Update zeroconf in the lock to speed up CI
  ([#218](https://github.com/pyenphase/pyenphase/pull/218),
  [`c89bfbe`](https://github.com/pyenphase/pyenphase/commit/c89bfbed1a728d930f4db98977dad4e3c59909ff))

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- **ci**: Bump the github-actions group with 7 updates
  ([#206](https://github.com/pyenphase/pyenphase/pull/206),
  [`61e31b4`](https://github.com/pyenphase/pyenphase/commit/61e31b48da41fb606ee8135443b308fe0a472141))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

Co-authored-by: J. Nick Koston <nick@koston.org>


## v1.25.3 (2025-02-11)

### Bug Fixes

- Bump orjson requirement to 3.10+ for Python 3.13
  ([#215](https://github.com/pyenphase/pyenphase/pull/215),
  [`7db2256`](https://github.com/pyenphase/pyenphase/commit/7db2256a59a26a4fc89b79a8dbaf4fbb16d5eb35))


## v1.25.2 (2025-02-11)

### Bug Fixes

- Update to poetry 2 ([#212](https://github.com/pyenphase/pyenphase/pull/212),
  [`43e5a15`](https://github.com/pyenphase/pyenphase/commit/43e5a15d747251dbecbad343b71562000d7f5b4f))

### Chores

- Add missing cache to CI ([#214](https://github.com/pyenphase/pyenphase/pull/214),
  [`d97d6cc`](https://github.com/pyenphase/pyenphase/commit/d97d6cc42b3eace1aa500d07d9abf5824b3ee7ad))

- Create dependabot.yml ([#205](https://github.com/pyenphase/pyenphase/pull/205),
  [`f3cf369`](https://github.com/pyenphase/pyenphase/commit/f3cf369a866fc91621e6cfb661e51643ed62aad2))

- **deps**: Bump awesomeversion from 24.2.0 to 24.6.0
  ([#208](https://github.com/pyenphase/pyenphase/pull/208),
  [`6488aa6`](https://github.com/pyenphase/pyenphase/commit/6488aa67d4d2c53783894ef31ba90135c0075b52))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps-dev**: Bump pytest-cov from 5.0.0 to 6.0.0
  ([#210](https://github.com/pyenphase/pyenphase/pull/210),
  [`c8924a4`](https://github.com/pyenphase/pyenphase/commit/c8924a434311c9051efdc4e24ccab21347384219))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps-dev**: Bump respx from 0.20.2 to 0.22.0
  ([#209](https://github.com/pyenphase/pyenphase/pull/209),
  [`607cbdf`](https://github.com/pyenphase/pyenphase/commit/607cbdf56db34b99f16ba005880aa4a617be1ceb))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps-dev**: Bump sphinx-autodoc-typehints from 1.25.3 to 3.0.1
  ([#207](https://github.com/pyenphase/pyenphase/pull/207),
  [`bbf89ad`](https://github.com/pyenphase/pyenphase/commit/bbf89adf4c9d9f8b3081299dfc59d72c4affe19d))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps-dev**: Bump syrupy from 4.6.1 to 4.8.1
  ([#211](https://github.com/pyenphase/pyenphase/pull/211),
  [`1ac802e`](https://github.com/pyenphase/pyenphase/commit/1ac802e6a5763d579fca1a731a969d461778718c))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>


## v1.25.1 (2025-02-11)

### Bug Fixes

- Indexerror crash for fw 8.3.5027 that sends data for not present CT
  ([#203](https://github.com/pyenphase/pyenphase/pull/203),
  [`770cab0`](https://github.com/pyenphase/pyenphase/commit/770cab092890d05b8f32fc9b180be6f58081a013))

* bug: fix indexerror crash for fw 8.3.5027 that sends data for not present CT

* chore(pre-commit.ci): auto fixes

---------

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

Co-authored-by: J. Nick Koston <nick@koston.org>


## v1.25.0 (2025-02-11)

### Features

- Add http method to request method parameters
  ([#197](https://github.com/pyenphase/pyenphase/pull/197),
  [`943f8d9`](https://github.com/pyenphase/pyenphase/commit/943f8d99306cc3dd1b45cf9ec810aa8936698c53))


## v1.24.0 (2025-02-11)

### Chores

- **deps-dev**: Bump jinja2 from 3.1.4 to 3.1.5
  ([#200](https://github.com/pyenphase/pyenphase/pull/200),
  [`ed9b448`](https://github.com/pyenphase/pyenphase/commit/ed9b448d3937fb922ecaccb2ee7dc135113f216b))

Bumps [jinja2](https://github.com/pallets/jinja) from 3.1.4 to 3.1.5. - [Release
  notes](https://github.com/pallets/jinja/releases) -
  [Changelog](https://github.com/pallets/jinja/blob/main/CHANGES.rst) -
  [Commits](https://github.com/pallets/jinja/compare/3.1.4...3.1.5)

--- updated-dependencies: - dependency-name: jinja2 dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **pre-commit.ci**: Pre-commit autoupdate ([#201](https://github.com/pyenphase/pyenphase/pull/201),
  [`5fbb475`](https://github.com/pyenphase/pyenphase/commit/5fbb475b9c3770cc132d1ad36472dbd5842561bd))

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- **pre-commit.ci**: Pre-commit autoupdate ([#202](https://github.com/pyenphase/pyenphase/pull/202),
  [`75b0ef0`](https://github.com/pyenphase/pyenphase/commit/75b0ef075ed29793471110de3e3fd0de9fe6d450))

updates: - [github.com/PyCQA/isort: 5.13.2 →
  6.0.0](https://github.com/PyCQA/isort/compare/5.13.2...6.0.0) - [github.com/psf/black: 24.10.0 →
  25.1.0](https://github.com/psf/black/compare/24.10.0...25.1.0) -
  [github.com/codespell-project/codespell: v2.4.0 →
  v2.4.1](https://github.com/codespell-project/codespell/compare/v2.4.0...v2.4.1)

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- **pre-commit.ci**: Pre-commit autoupdate ([#204](https://github.com/pyenphase/pyenphase/pull/204),
  [`2e5920d`](https://github.com/pyenphase/pyenphase/commit/2e5920d18569868cd6e1ede48678158465b5bd08))

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

### Features

- Add token_type property to identify user or installer type token.
  ([#180](https://github.com/pyenphase/pyenphase/pull/180),
  [`3708a54`](https://github.com/pyenphase/pyenphase/commit/3708a543bada7827fc16c52f9b747c0808061260))

* feat: add token_type property to identify user or installer type token.

- **tariff**: Add new firmware 8.2.42xx Storage settings opt_schedules property to
  EnvoyStorageSettings ([#179](https://github.com/pyenphase/pyenphase/pull/179),
  [`7b3d559`](https://github.com/pyenphase/pyenphase/commit/7b3d559ab56582519a6ccd34ce446f0f4014656e))

* feat(tariff): Add opt_schedules to EnvoyStorageSettings

### Refactoring

- Add exception catch for envoy._json_request() indirectly used by HA actions.
  ([#194](https://github.com/pyenphase/pyenphase/pull/194),
  [`e2224e2`](https://github.com/pyenphase/pyenphase/commit/e2224e22d8870210c8e1614b7114e16c9426c535))

* refactor: add exception catch for envoy._json_request() indirectly used by HA actions.


## v1.23.1 (2025-01-21)

### Bug Fixes

- Set EnvoyStorageMode to None if tariff storage_settings mode is null and causes exception None is
  not a valid EnvoyStorageMode. ([#199](https://github.com/pyenphase/pyenphase/pull/199),
  [`d06680a`](https://github.com/pyenphase/pyenphase/commit/d06680adee686929aa648d294358e0c9a951f1be))

fix: tariff storage_settings mode: None causes exception "None is not a valid EnvoyStorageMode", set
  EnvoyStorageMode to None.

### Chores

- **pre-commit.ci**: Pre-commit autoupdate ([#193](https://github.com/pyenphase/pyenphase/pull/193),
  [`60d9fbf`](https://github.com/pyenphase/pyenphase/commit/60d9fbfe64ebf346d3802ea903d2c3446580d008))

updates: - [github.com/PyCQA/bandit: 1.7.10 →
  1.8.0](https://github.com/PyCQA/bandit/compare/1.7.10...1.8.0)

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- **pre-commit.ci**: Pre-commit autoupdate ([#196](https://github.com/pyenphase/pyenphase/pull/196),
  [`ed7c44a`](https://github.com/pyenphase/pyenphase/commit/ed7c44aa486ecd14e129cdd030b6a38684ab3514))

updates: - [github.com/asottile/pyupgrade: v3.19.0 →
  v3.19.1](https://github.com/asottile/pyupgrade/compare/v3.19.0...v3.19.1) -
  [github.com/pre-commit/mirrors-mypy: v1.13.0 →
  v1.14.0](https://github.com/pre-commit/mirrors-mypy/compare/v1.13.0...v1.14.0)

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- **pre-commit.ci**: Pre-commit autoupdate ([#198](https://github.com/pyenphase/pyenphase/pull/198),
  [`a4bc451`](https://github.com/pyenphase/pyenphase/commit/a4bc451f254d9fc7a5000d5f0e7b2d227950483e))

updates: - [github.com/python-poetry/poetry: 1.8.0 →
  2.0.1](https://github.com/python-poetry/poetry/compare/1.8.0...2.0.1) -
  [github.com/pre-commit/mirrors-mypy: v1.14.0 →
  v1.14.1](https://github.com/pre-commit/mirrors-mypy/compare/v1.14.0...v1.14.1) -
  [github.com/PyCQA/bandit: 1.8.0 → 1.8.2](https://github.com/PyCQA/bandit/compare/1.8.0...1.8.2)

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

### Documentation

- Docs gen 2, refactor authentication doc ([#181](https://github.com/pyenphase/pyenphase/pull/181),
  [`a6bbc25`](https://github.com/pyenphase/pyenphase/commit/a6bbc256eedf2b8edbcaae7ed0549cb99957fc11))

* docs: docs gen 2, refactor authentication doc

* chore(pre-commit.ci): auto fixes

* chore: fix lint text issues

---------

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- Refactor const.py to use docstring for documentation.
  ([#190](https://github.com/pyenphase/pyenphase/pull/190),
  [`58b2df1`](https://github.com/pyenphase/pyenphase/commit/58b2df1faa077fcc834377b4a03caf619156c2d2))

* docs: refactor const.py to use docstring for documentation.

* docs: fix multiple docstrings in const.py

* chore(pre-commit.ci): auto fixes

---------

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- Refactor envoy class documentation using docstrings
  ([#184](https://github.com/pyenphase/pyenphase/pull/184),
  [`b869d0d`](https://github.com/pyenphase/pyenphase/commit/b869d0d9bcb9341c83d3848879efcac5ff5d597f))

* docs: refactor envoy class documentation using docstrings

* chore(pre-commit.ci): auto fixes

* docs: fix textlint issues

* docs: fix more textlint issues

---------

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- Refactor EnvoyData class documentation using docstrings
  ([#189](https://github.com/pyenphase/pyenphase/pull/189),
  [`6048a0f`](https://github.com/pyenphase/pyenphase/commit/6048a0fda2ef9eae1404962db13fcf300291530e))

- Refactor firmware class documentation using docstrings
  ([#185](https://github.com/pyenphase/pyenphase/pull/185),
  [`ab7bae4`](https://github.com/pyenphase/pyenphase/commit/ab7bae40d135207f34ba762a14b35c0fa24acb08))

docs: refactor firmware class documentation

- Refactor json helper documentation using docstrings
  ([#188](https://github.com/pyenphase/pyenphase/pull/188),
  [`aea3359`](https://github.com/pyenphase/pyenphase/commit/aea3359762a105106705d066324729d7ac768b48))

- Refactor ssl helper documentation using docstring
  ([#186](https://github.com/pyenphase/pyenphase/pull/186),
  [`76de306`](https://github.com/pyenphase/pyenphase/commit/76de306906e0a7252def6c133a16c88d71913276))

* docs: refactor ssl helper documentation using docstring

* chore(pre-commit.ci): auto fixes

* docs: fix issue with multiple docstrings in ssl module.

---------

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- Update guidelines to documentation for using docstring
  ([#187](https://github.com/pyenphase/pyenphase/pull/187),
  [`ecc88c2`](https://github.com/pyenphase/pyenphase/commit/ecc88c285147ac55b2c370a6b28376ca68d4532d))

* docs: update guidelines to documentation for using docstring

* chore(pre-commit.ci): auto fixes

* docs: fix codespell lint issues

---------

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>


## v1.23.0 (2024-11-21)

### Chores

- **pre-commit.ci**: Pre-commit autoupdate ([#176](https://github.com/pyenphase/pyenphase/pull/176),
  [`fc76ed5`](https://github.com/pyenphase/pyenphase/commit/fc76ed5a43b76b4506b99423938bfbef49ad3a5d))

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

Co-authored-by: Joostlek <joostlek@outlook.com>

### Documentation

- Add license to documentation project info section
  ([#182](https://github.com/pyenphase/pyenphase/pull/182),
  [`fa24372`](https://github.com/pyenphase/pyenphase/commit/fa2437208e76d6c1f90a01b55c98fdd1ca3cb450))

* docs-2.1-license

* chore(pre-commit.ci): auto fixes

---------

Co-authored-by: pre-commit-ci[bot] <66853113+pre-commit-ci[bot]@users.noreply.github.com>

- Minor updates to usage example. ([#183](https://github.com/pyenphase/pyenphase/pull/183),
  [`b287005`](https://github.com/pyenphase/pyenphase/commit/b28700558b53ebfaeb7d21e7cdb68415c9a78f1a))

### Features

- Add support for ACB batteries ([#191](https://github.com/pyenphase/pyenphase/pull/191),
  [`1caeff2`](https://github.com/pyenphase/pyenphase/commit/1caeff2f49397e6c2dabf2ff99cb7a8ccc685a50))

* feat: add model for ACB batteries

* feat: add ACB model documentation and some pre-commit cleanup

* feat: Add ACB updaters

* test: Add 8.2.4382 ACB battery fixture

* test: Add ACB battery tests

* refactor: implement review change proposals.


## v1.22.0 (2024-08-03)

### Features

- **netconsumption**: Add system_net_consumption and phases
  ([#177](https://github.com/pyenphase/pyenphase/pull/177),
  [`c734a6d`](https://github.com/pyenphase/pyenphase/commit/c734a6d67b6ac355ba528fcf78fd86a33e48a419))

* feat(netconsumption): Add system_net_consumption and phases


## v1.21.0 (2024-07-16)

### Chores

- **deps**: Bump certifi from 2024.2.2 to 2024.7.4
  ([#175](https://github.com/pyenphase/pyenphase/pull/175),
  [`52eb502`](https://github.com/pyenphase/pyenphase/commit/52eb502f4a710259cffc5313432c2b7ea8fee603))

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

### Features

- **generator**: Probe for generator ([#160](https://github.com/pyenphase/pyenphase/pull/160),
  [`42a2533`](https://github.com/pyenphase/pyenphase/commit/42a2533f44ec975c72bd0be9dc70c75a987ff030))

* feat(generator): Probe for generator

---------

Co-authored-by: J. Nick Koston <nick@koston.org>

Co-authored-by: Arie Catsman <catsmanac@outlook.com>

Co-authored-by: Arie Catsman <120491684+catsmanac@users.noreply.github.com>

### Refactoring

- Extend fixture_collector with cmdline args and option to read HA config file
  ([#162](https://github.com/pyenphase/pyenphase/pull/162),
  [`cb6c40c`](https://github.com/pyenphase/pyenphase/commit/cb6c40cf5d423893f259bb7fd4c98a5a1e693b92))

* refactor: use HA config information and cmdline args for fixture collection

* Handle multiple Envoy and implement suggested changes

* refactor: tweak code

---------

Co-authored-by: J. Nick Koston <nick@koston.org>


## v1.20.6 (2024-07-03)

### Bug Fixes

- Raise EnvoyCommunicationError for httpx ConnectError and TimeoutException exceptions during
  Envoy.update ([#170](https://github.com/pyenphase/pyenphase/pull/170),
  [`c6d238f`](https://github.com/pyenphase/pyenphase/commit/c6d238f83b10622cb20493bcf70e4e54deb751d2))

* fix: raise EnvoyCommunicationError for hhtpx NetworkError and TimeoutExcpetion exceptions

* test: httpx.TimeoutException and NetworkError map to EnvoyCommunicationError

Co-authored-by: J. Nick Koston <nick@koston.org>


## v1.20.5 (2024-07-03)

### Bug Fixes

- Report EnvoyHTTPStatusError for _json_request if status not in 200-300
  ([#171](https://github.com/pyenphase/pyenphase/pull/171),
  [`46fb2b3`](https://github.com/pyenphase/pyenphase/commit/46fb2b386ff1991ba26d4b60628163cff147afa9))

* fix: report EnvoyHTTPStatusError for _json_request if status not in 200-300

* test: add test for request status not between 200-300

### Chores

- **pre-commit.ci**: Pre-commit autoupdate ([#174](https://github.com/pyenphase/pyenphase/pull/174),
  [`3fc9920`](https://github.com/pyenphase/pyenphase/commit/3fc99208c47f6d491442b341d9d571f658623169))

### Refactoring

- Unify request reply debug log all showing url and duration.
  ([#172](https://github.com/pyenphase/pyenphase/pull/172),
  [`8f0e092`](https://github.com/pyenphase/pyenphase/commit/8f0e092a52b7eea7d9c13a0d1ba1bf2172992e88))

* refactor: unify request reply debug log all showing url and duration.

* refactor: get monotonic time and only when in debug mode

---------

Co-authored-by: J. Nick Koston <nick@koston.org>


## v1.20.4 (2024-07-02)

### Bug Fixes

- For fw 3.x mark production with only zero values as EnvoyPoorDataQuality error
  ([#173](https://github.com/pyenphase/pyenphase/pull/173),
  [`8b6b302`](https://github.com/pyenphase/pyenphase/commit/8b6b302b626742e101708c5bbd0c0a46e86f9cb7))

When Envoy running FW 3.x restart it may send all zero values with status 200, while the internals
  are still restoring data. If major firmware version is 3 and all values in data.system_production
  are zero signal exception EnvoyPoorDataQuality.

### Chores

- **deps-dev**: Bump jinja2 from 3.1.3 to 3.1.4
  ([#163](https://github.com/pyenphase/pyenphase/pull/163),
  [`d8d90f9`](https://github.com/pyenphase/pyenphase/commit/d8d90f92344ee10d2fe7bacdc7b40a59166be1fc))

Bumps [jinja2](https://github.com/pallets/jinja) from 3.1.3 to 3.1.4. - [Release
  notes](https://github.com/pallets/jinja/releases) -
  [Changelog](https://github.com/pallets/jinja/blob/main/CHANGES.rst) -
  [Commits](https://github.com/pallets/jinja/compare/3.1.3...3.1.4)

--- updated-dependencies: - dependency-name: jinja2 dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps-dev**: Bump requests from 2.31.0 to 2.32.0
  ([#164](https://github.com/pyenphase/pyenphase/pull/164),
  [`114854d`](https://github.com/pyenphase/pyenphase/commit/114854df454ad6b8d8a0aad9abd87168857af7ed))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps-dev**: Bump urllib3 from 2.2.1 to 2.2.2
  ([#167](https://github.com/pyenphase/pyenphase/pull/167),
  [`9f130fb`](https://github.com/pyenphase/pyenphase/commit/9f130fb4e816953ea8652552b744cf5c4ea48cbb))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>


## v1.20.3 (2024-05-07)

### Bug Fixes

- Get production phase data using details parameter
  ([#159](https://github.com/pyenphase/pyenphase/pull/159),
  [`d2a478c`](https://github.com/pyenphase/pyenphase/commit/d2a478c25581cbb147506d138db3043c70345fae))

make productionjsonupdater first production updater using details=1 to get phase details for
  production report.

### Chores

- **deps**: Bump pytest-cov to 5.0 ([#156](https://github.com/pyenphase/pyenphase/pull/156),
  [`a955c65`](https://github.com/pyenphase/pyenphase/commit/a955c6587595cd36a2a0a24274de0778ae23df3d))

- **deps**: Remove deprecated cookies on request
  ([#158](https://github.com/pyenphase/pyenphase/pull/158),
  [`b4eecda`](https://github.com/pyenphase/pyenphase/commit/b4eecda718fd89894396d48e1c5ec484898ffe99))

httpxcookies

- **deps**: Replace deprecated httpx data with content
  ([#157](https://github.com/pyenphase/pyenphase/pull/157),
  [`86f8ba2`](https://github.com/pyenphase/pyenphase/commit/86f8ba2a183ebdf0ca57bd92fd75c57841f4875d))

deprecatedcontent


## v1.20.2 (2024-04-18)

### Bug Fixes

- Add missing EnvoyTokenAuth class properties
  ([#150](https://github.com/pyenphase/pyenphase/pull/150),
  [`d01157a`](https://github.com/pyenphase/pyenphase/commit/d01157a1ec3139f67e085f0a4e529f2e7af09943))

* fix: add missing EnvoyTokenAuth class properties

### Chores

- Update dependancies to latest versions ([#153](https://github.com/pyenphase/pyenphase/pull/153),
  [`e750144`](https://github.com/pyenphase/pyenphase/commit/e7501441baff3c66a198e8eec260292dc13bbb85))

- **deps**: Bump idna from 3.4 to 3.7 ([#149](https://github.com/pyenphase/pyenphase/pull/149),
  [`0596e59`](https://github.com/pyenphase/pyenphase/commit/0596e59d1f232376ce3f97342b8a76ba1bdac174))

Bumps [idna](https://github.com/kjd/idna) from 3.4 to 3.7. - [Release
  notes](https://github.com/kjd/idna/releases) -
  [Changelog](https://github.com/kjd/idna/blob/master/HISTORY.rst) -
  [Commits](https://github.com/kjd/idna/compare/v3.4...v3.7)

--- updated-dependencies: - dependency-name: idna dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

### Documentation

- Let readthedocs use virtualenv for build ([#151](https://github.com/pyenphase/pyenphase/pull/151),
  [`9e8b648`](https://github.com/pyenphase/pyenphase/commit/9e8b648875db5fcc2210d7f180c0d278485eafb8))

docs: let readtedocs use virtualenv for build

- Use new format to specify virtual env for readthedocs
  ([#152](https://github.com/pyenphase/pyenphase/pull/152),
  [`4b9a9ea`](https://github.com/pyenphase/pyenphase/commit/4b9a9ea79ef94dfd1fed2b262a12cb016da2802c))

### Testing

- Correct 7.6.175 fw fixture and add 7.3.466 fw
  ([#155](https://github.com/pyenphase/pyenphase/pull/155),
  [`074eb7c`](https://github.com/pyenphase/pyenphase/commit/074eb7cd7ca6d19534ef84be3dc7a281edf3af48))

- Improve code coverage ([#146](https://github.com/pyenphase/pyenphase/pull/146),
  [`c55aa92`](https://github.com/pyenphase/pyenphase/commit/c55aa92e0b45fb9ed7b435d6fdc55c3a49e552dd))

* create common test functions. * move ct meter tests to separate test file. * move pre v7 fw tests
  to seperate test file. * create auth test functions * improve cov.

Co-authored-by: J. Nick Koston <nick@koston.org>


## v1.20.1 (2024-03-26)

### Bug Fixes

- Endless loop on envoy unreachable ([#145](https://github.com/pyenphase/pyenphase/pull/145),
  [`f074c61`](https://github.com/pyenphase/pyenphase/commit/f074c61b56b0fdb1080ff3c54f82c59a8015b6d9))

Changed timeout logic to end after 4 tries or 50 seconds, whichever happens first. Lowered httpx
  read timeout to 45 sec. Effectively limiting to 1 retry on read timeout and 4 retries on
  connection failures.


## v1.20.0 (2024-03-21)

### Features

- Report storage CT data ([#144](https://github.com/pyenphase/pyenphase/pull/144),
  [`52c53fe`](https://github.com/pyenphase/pyenphase/commit/52c53fe20123514177290e964e03a23454e42e9c))

* feat: report storage CT data

Co-authored-by: J. Nick Koston <nick@koston.org>

### Refactoring

- Add empty data structures for storage CT ([#142](https://github.com/pyenphase/pyenphase/pull/142),
  [`669b95a`](https://github.com/pyenphase/pyenphase/commit/669b95aba0d333807d795e6a83a657ae5c7c295b))


## v1.19.2 (2024-03-08)

### Bug Fixes

- Consumption CT not found when 3 CT reported
  ([#140](https://github.com/pyenphase/pyenphase/pull/140),
  [`7c2f52c`](https://github.com/pyenphase/pyenphase/commit/7c2f52cc28fdc872a8c5875fc7f7d8b7e233bc01))

* fix: consumption CT not found when 3 CT reported


## v1.19.1 (2024-02-27)

### Bug Fixes

- Force release ([#139](https://github.com/pyenphase/pyenphase/pull/139),
  [`b16f132`](https://github.com/pyenphase/pyenphase/commit/b16f13264ffdb90de53d3d9730eb0cd700724ffd))

### Chores

- **deps**: Bump orjson from 3.9.10 to 3.9.15
  ([#137](https://github.com/pyenphase/pyenphase/pull/137),
  [`25ad476`](https://github.com/pyenphase/pyenphase/commit/25ad4769681e70cd414ddb4efd665f3334aee361))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

### Refactoring

- Add type hint to PHASENAMES ([#138](https://github.com/pyenphase/pyenphase/pull/138),
  [`b20d60f`](https://github.com/pyenphase/pyenphase/commit/b20d60fe8a4262c605e9598d5d33468aeb85051b))


## v1.19.0 (2024-01-27)

### Features

- Add envoy_model property ([#136](https://github.com/pyenphase/pyenphase/pull/136),
  [`42652cd`](https://github.com/pyenphase/pyenphase/commit/42652cda168d1cf1d4b637071f0603d0b0707066))

Add Envoy_Model property that returns a descriptive name for the Envoy model, including installed CT
  and phases.


## v1.18.0 (2024-01-23)

### Documentation

- Document CT meter data ([#134](https://github.com/pyenphase/pyenphase/pull/134),
  [`cfd396b`](https://github.com/pyenphase/pyenphase/commit/cfd396bde18a908d7703d421a10126abc06f0542))

### Features

- Add updater for Current Transformer data ([#135](https://github.com/pyenphase/pyenphase/pull/135),
  [`1ca6118`](https://github.com/pyenphase/pyenphase/commit/1ca6118e6aaecb829b4cd711d72d6296fad26bae))

### Refactoring

- Add CT meters model datastructures ([#133](https://github.com/pyenphase/pyenphase/pull/133),
  [`8d6e2c5`](https://github.com/pyenphase/pyenphase/commit/8d6e2c585b2962838fc9be0ff30153915e6873c2))

refactor: Add meters model datastructures


## v1.17.0 (2024-01-11)

### Chores

- Bump python for readthedocs to 3.11 ([#130](https://github.com/pyenphase/pyenphase/pull/130),
  [`35fa785`](https://github.com/pyenphase/pyenphase/commit/35fa78501c0e0656c33c79bf96476b01ac0a2913))

- **deps-dev**: Bump jinja2 from 3.1.2 to 3.1.3
  ([#132](https://github.com/pyenphase/pyenphase/pull/132),
  [`c2a9460`](https://github.com/pyenphase/pyenphase/commit/c2a9460d8a958cc0b3d161e2fbfdcbaf648b021e))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

### Documentation

- Reorganize and extend documentation. ([#129](https://github.com/pyenphase/pyenphase/pull/129),
  [`4d8e463`](https://github.com/pyenphase/pyenphase/commit/4d8e463fc5d5e500876f721ae2831cc90a275d9a))

- Combine Ensemble description in single file and describe methods and refer to models. - Extend
  auto-documentation structure and allow entry without docstrings. - Add small description on how to
  code for auto-documenting - Minor text corrections after review

### Features

- Write request reply to debuglog when in debug
  ([#131](https://github.com/pyenphase/pyenphase/pull/131),
  [`e255684`](https://github.com/pyenphase/pyenphase/commit/e25568444ca4a629bc38904c0f27777550219117))


## v1.16.0 (2024-01-09)

### Features

- Provide phase data for envoy metered with ct
  ([#126](https://github.com/pyenphase/pyenphase/pull/126),
  [`454dbc5`](https://github.com/pyenphase/pyenphase/commit/454dbc58ebb2edf23e9c64173fb8b5d155b327fc))

* feat: provide phase data for envoy metered with ct

-Add from_production_phase method to production and consumption models. -In production updater get
  phase data from models and report in system_production_phase and system_consumption_phase. Set
  active_phase_count common_property of Envoy -Update tests and snapshots to include phase data.
  -Move phase documentation to its own section in the docs.


## v1.15.2 (2023-12-20)

### Bug Fixes

- 3.9.x firmware with meters probe ([#128](https://github.com/pyenphase/pyenphase/pull/128),
  [`06606c5`](https://github.com/pyenphase/pyenphase/commit/06606c5516c84b3ee500843b8b843bf180658055))


## v1.15.1 (2023-12-20)

### Bug Fixes

- Skip meters endpoint if it returns a 401 ([#125](https://github.com/pyenphase/pyenphase/pull/125),
  [`166c25c`](https://github.com/pyenphase/pyenphase/commit/166c25c410b6fa319bddea78db44606da7364aeb))

* fix: skip meters endpoint if it returns a 401

For D3.18.10 (f0855e) systems return 401 even if the user has access to the endpoint so we must skip
  it.

* chore: add tests

* chore: lint


## v1.15.0 (2023-12-19)

### Features

- Provide phase configuration for envoy metered with ct
  ([#122](https://github.com/pyenphase/pyenphase/pull/122),
  [`12204a8`](https://github.com/pyenphase/pyenphase/commit/12204a8ec2082cb561f334e21e6febfdb2c8a082))

### Refactoring

- Add empty data structures and tests for phase information
  ([#121](https://github.com/pyenphase/pyenphase/pull/121),
  [`f5cbea7`](https://github.com/pyenphase/pyenphase/commit/f5cbea7bf431c1ce10420851a6e66383c6641fbb))

- Add sphinx napoleon extension for auto doc generation.
  ([#117](https://github.com/pyenphase/pyenphase/pull/117),
  [`577c40e`](https://github.com/pyenphase/pyenphase/commit/577c40ee9310ed02dfca675ffd63826c8c0287b1))

- Rename data parameter of EnvoyUpdater base class to envoy_data
  ([#119](https://github.com/pyenphase/pyenphase/pull/119),
  [`a0abccd`](https://github.com/pyenphase/pyenphase/commit/a0abccd7423ed0fa48e67543cd9bcc32352b0b74))

- Use TypedDict for meter data and enum for fields and phasenames
  ([#116](https://github.com/pyenphase/pyenphase/pull/116),
  [`0f7fe6b`](https://github.com/pyenphase/pyenphase/commit/0f7fe6bb80cd44f5fbd3bcededdb2d0e4ff2d3a1))

### Testing

- Add 401 test for ivp/meters and change not existing reply to 404
  ([#120](https://github.com/pyenphase/pyenphase/pull/120),
  [`12bbe91`](https://github.com/pyenphase/pyenphase/commit/12bbe91812161360e2f6f62269f19544084e2f77))


## v1.14.3 (2023-11-11)

### Bug Fixes

- **#99**: Envoy metered without CT reporting wrong values
  ([#111](https://github.com/pyenphase/pyenphase/pull/111),
  [`2188969`](https://github.com/pyenphase/pyenphase/commit/21889696fdc06f423f382eb404483e1b5d641094))

Co-authored-by: J. Nick Koston <nick@koston.org>

### Chores

- Fix docs build ([#115](https://github.com/pyenphase/pyenphase/pull/115),
  [`809bb5a`](https://github.com/pyenphase/pyenphase/commit/809bb5affd67c2d846485728fe03e329392b9fa3))

- Fix python version in readthedocs ([#114](https://github.com/pyenphase/pyenphase/pull/114),
  [`c89c989`](https://github.com/pyenphase/pyenphase/commit/c89c98989033b382bc05170972e1c4bedc67c3db))

### Documentation

- Update usage.md ([#109](https://github.com/pyenphase/pyenphase/pull/109),
  [`2e31671`](https://github.com/pyenphase/pyenphase/commit/2e316718081fccab314844a76aa9c6e4e54d20a9))

Co-authored-by: J. Nick Koston <nick@koston.org>

Co-authored-by: Charles Garwood <cgarwood@gmail.com>

Co-authored-by: github-actions <github-actions@github.com>


## v1.14.2 (2023-11-06)

### Bug Fixes

- Make date field optional in storage settings tariff model
  ([#112](https://github.com/pyenphase/pyenphase/pull/112),
  [`cf98198`](https://github.com/pyenphase/pyenphase/commit/cf98198b80326f5bf57c58c77eedbe17b6142b0b))

* fix: Make date field optional in storage settings tariff model

* update test

### Chores

- **deps**: Update deps via poetry ([#113](https://github.com/pyenphase/pyenphase/pull/113),
  [`34aaa0e`](https://github.com/pyenphase/pyenphase/commit/34aaa0e210c36cfe63e72fe5b1c3fef0f02ab4eb))


## v1.14.1 (2023-11-02)

### Bug Fixes

- Add economy EnvoyStorageMode ([#110](https://github.com/pyenphase/pyenphase/pull/110),
  [`edaf93c`](https://github.com/pyenphase/pyenphase/commit/edaf93c8c1cd71f34bf0be227436f676b1c13772))

* fix: Add economy EnvoyStorageMode

* Convert savings-mode to economy

* fix value check

* add new fixture for savings-mode conversion

* Update tests


## v1.14.0 (2023-10-24)

### Features

- **multiphase**: Add phase_count property to envoy
  ([#105](https://github.com/pyenphase/pyenphase/pull/105),
  [`39ec460`](https://github.com/pyenphase/pyenphase/commit/39ec4606b1bfc152189c48edc89396267564ac13))


## v1.13.1 (2023-10-21)

### Bug Fixes

- Ensure tariff endpoint is skipped on firmware 3
  ([#102](https://github.com/pyenphase/pyenphase/pull/102),
  [`4fd7796`](https://github.com/pyenphase/pyenphase/commit/4fd77967230089ec9e86c6e6c3e237b6153abb87))

### Chores

- Add python 3.12 to the CI ([#103](https://github.com/pyenphase/pyenphase/pull/103),
  [`c23c3cf`](https://github.com/pyenphase/pyenphase/commit/c23c3cf1402076bf32af685187247d240b4790d4))

- **deps-dev**: Bump urllib3 from 2.0.4 to 2.0.7
  ([#100](https://github.com/pyenphase/pyenphase/pull/100),
  [`f9ae1a7`](https://github.com/pyenphase/pyenphase/commit/f9ae1a766eafd5287c4801a55faa8f1b9a510dfc))

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>


## v1.13.0 (2023-10-20)

### Features

- Add support for changing storage mode and reserve soc
  ([#101](https://github.com/pyenphase/pyenphase/pull/101),
  [`16a1471`](https://github.com/pyenphase/pyenphase/commit/16a1471d7b2e961be218825151401a4cd27fe096))

* feat: Add support for changing storage mode and reserve soc

* tests round 1

* tests

* Tweak enum check


## v1.12.0 (2023-10-11)

### Chores

- Add 4.10.35 fixtures ([#92](https://github.com/pyenphase/pyenphase/pull/92),
  [`27e81d2`](https://github.com/pyenphase/pyenphase/commit/27e81d2233594b07d86eb2927bb97acbe10e7e08))

- Add fixtures for 7.6.185 with cts and battery 3t
  ([#93](https://github.com/pyenphase/pyenphase/pull/93),
  [`5d7a8f8`](https://github.com/pyenphase/pyenphase/commit/5d7a8f83fc0892c01ce7eae4d8c503090847ae8c))

- Add tests for 7.6.185_with_cts_and_battery_3t
  ([#94](https://github.com/pyenphase/pyenphase/pull/94),
  [`2ae0fa2`](https://github.com/pyenphase/pyenphase/commit/2ae0fa2058c34ca16cd005395bfaa51f79f29561))

- Bump syrupy to 4.5.0 ([#98](https://github.com/pyenphase/pyenphase/pull/98),
  [`7ea6c1c`](https://github.com/pyenphase/pyenphase/commit/7ea6c1cf2ca596c8b02ec1975d56121cec143147))

Bump syrupy to 4.5.0

### Features

- Add initial tariff support and charge from grid functions
  ([#95](https://github.com/pyenphase/pyenphase/pull/95),
  [`5418d4c`](https://github.com/pyenphase/pyenphase/commit/5418d4c99ee6a5f0998367525ccba65f0edb9bc5))

* feat: Add initial tariff support and charge from grid functions

* Tweak request and add SupportedFeature flag

* use keyword argument for method

* Review comments

* mypy

* Update tests

* seasons_sell is not present in firmware 4.x

* rebase and update tests

---------

Co-authored-by: J. Nick Koston <nick@koston.org>


## v1.11.4 (2023-09-13)

### Bug Fixes

- Use eim if activeCount is true ([#91](https://github.com/pyenphase/pyenphase/pull/91),
  [`ac041a4`](https://github.com/pyenphase/pyenphase/commit/ac041a4abd2119fa3c784aa74634b27e118b7624))

The logic was reversed here


## v1.11.3 (2023-09-13)

### Bug Fixes

- More dry contact settings should be optional
  ([#90](https://github.com/pyenphase/pyenphase/pull/90),
  [`4fc503a`](https://github.com/pyenphase/pyenphase/commit/4fc503a4f8f60051319aaabf386bced2cd0f3076))

* fix: more dry contact settings should be optional

* forgot manual override

* fix manual override comparison

* update snapshot

### Chores

- Update fixtures for 5.0.62 with newer fixture collector
  ([#88](https://github.com/pyenphase/pyenphase/pull/88),
  [`9086494`](https://github.com/pyenphase/pyenphase/commit/9086494081b02e0b9a97c606a0eb16e9f97dfa7f))


## v1.11.2 (2023-09-12)

### Bug Fixes

- Disable consumption when there are no active meters
  ([#87](https://github.com/pyenphase/pyenphase/pull/87),
  [`fa28f1c`](https://github.com/pyenphase/pyenphase/commit/fa28f1c31344f0e2d1bc60640902e94bd55b0331))

### Chores

- Add 7.3.130 fixtures without consumption ([#85](https://github.com/pyenphase/pyenphase/pull/85),
  [`4922693`](https://github.com/pyenphase/pyenphase/commit/49226932a95a69cab59c740f3033b4ebe413e8b0))

- Add tests for no consumption ([#86](https://github.com/pyenphase/pyenphase/pull/86),
  [`14039a6`](https://github.com/pyenphase/pyenphase/commit/14039a6b9481dfcda1ba3810584a0f1560acf36a))


## v1.11.1 (2023-09-12)

### Bug Fixes

- Black_s_start key not returned by all Ensemble systems
  ([#84](https://github.com/pyenphase/pyenphase/pull/84),
  [`357f0bd`](https://github.com/pyenphase/pyenphase/commit/357f0bd132a976f31a052063ce514ac86534de8e))

* fix: black_s_start not returned by all Ensemble systems

* updatet test

* Update tests


## v1.11.0 (2023-09-08)

### Chores

- Compare Enphase dataclasses as dict ([#82](https://github.com/pyenphase/pyenphase/pull/82),
  [`fd93f4c`](https://github.com/pyenphase/pyenphase/commit/fd93f4ceb4825feba80dcbedf0b6beb1b10af688))

### Features

- Add fallback when api/v1/production endpoint is broken
  ([#83](https://github.com/pyenphase/pyenphase/pull/83),
  [`d7e195e`](https://github.com/pyenphase/pyenphase/commit/d7e195e498362d1374366d88a24afc8da6b01321))

* feat: add fallback when api/v1/production endpoint if broken

* fix: update

* fix: get watt_hours_lifetime on total system


## v1.10.0 (2023-09-08)

### Features

- Add 7.6.175 fixtures with total consumption
  ([#81](https://github.com/pyenphase/pyenphase/pull/81),
  [`1bc2b20`](https://github.com/pyenphase/pyenphase/commit/1bc2b20a427c6d03df318fcf5c529391fc6e25ed))


## v1.9.3 (2023-09-07)

### Bug Fixes

- Handle /production returning a 401 even with the correct auth on some 3.x firmwares
  ([#80](https://github.com/pyenphase/pyenphase/pull/80),
  [`947605f`](https://github.com/pyenphase/pyenphase/commit/947605fba25b41d12db273e9352c29b08cac1d4d))


## v1.9.2 (2023-09-07)

### Bug Fixes

- Raise EnvoyAuthenticationRequired when local auth is incorrect
  ([#79](https://github.com/pyenphase/pyenphase/pull/79),
  [`208e91a`](https://github.com/pyenphase/pyenphase/commit/208e91a6a66e8afa0931bb3a78e557b882277148))


## v1.9.1 (2023-09-04)

### Bug Fixes

- Envoy default password is last 6 not first 6
  ([#78](https://github.com/pyenphase/pyenphase/pull/78),
  [`33d07f6`](https://github.com/pyenphase/pyenphase/commit/33d07f6fb231a274bfdf5e693d1d2200fc0b516d))

* fix: envoy default password is last 6 not first 6

https://github.com/jesserizzo/envoy_reader/blob/0d3fb696519d487d14b0fff7def7d77ab2173cff/envoy_reader/envoy_reader.py#L388

* chore: fix snapshot

* Update src/pyenphase/envoy.py


## v1.9.0 (2023-09-03)

### Chores

- Add additional endpoints to fixture collector
  ([#76](https://github.com/pyenphase/pyenphase/pull/76),
  [`9590d21`](https://github.com/pyenphase/pyenphase/commit/9590d219cdee3049364ce82691b74606062898e5))

* Add additional endpoints to fixture collector

* Add additional generator endpoint

* update snapshot

### Features

- Add ivp/meters and ivp/meters/readings to fixture collector
  ([#77](https://github.com/pyenphase/pyenphase/pull/77),
  [`74c02bc`](https://github.com/pyenphase/pyenphase/commit/74c02bc882435f8605c85600c7f598a7e77c7141))


## v1.8.1 (2023-08-23)

### Bug Fixes

- Preemptively update dry contact state when toggling
  ([#75](https://github.com/pyenphase/pyenphase/pull/75),
  [`6a3f12f`](https://github.com/pyenphase/pyenphase/commit/6a3f12f26355721a4d12f3ef490659e4c4ce4a4c))

* Pre-emptively update Dry Contact Status when toggling

* Add comment

* add test

* review comments

* nosec

* ci


## v1.8.0 (2023-08-19)

### Features

- Add initial support for firmware 8.1.41 ([#73](https://github.com/pyenphase/pyenphase/pull/73),
  [`3562261`](https://github.com/pyenphase/pyenphase/commit/3562261d51a2f3d539d125c3512d9b1ca9b9bd6d))


## v1.7.1 (2023-08-15)

### Bug Fixes

- Startup was blocked for multiple minutes if the envoy was offline
  ([#71](https://github.com/pyenphase/pyenphase/pull/71),
  [`983ef52`](https://github.com/pyenphase/pyenphase/commit/983ef52e92ffff5a91b8de8bddda68f460058b56))


## v1.7.0 (2023-08-15)

### Features

- Add support for opening and closing dry contact relays
  ([#70](https://github.com/pyenphase/pyenphase/pull/70),
  [`f59aa54`](https://github.com/pyenphase/pyenphase/commit/f59aa546e4991c5aee446e9629b48df2ca556272))


## v1.6.0 (2023-08-13)

### Features

- Add support for changing settings on dry contact relays
  ([#68](https://github.com/pyenphase/pyenphase/pull/68),
  [`345165a`](https://github.com/pyenphase/pyenphase/commit/345165a92ffc7ffc35c5d09626757c53f4add7d2))

* Add support for changing settings on dry contact relays

* refactor

* Add tests

* Add additional test

* Guard logging

* codecov


## v1.5.3 (2023-08-12)

### Bug Fixes

- Add "schedule" to DryContactAction ([#67](https://github.com/pyenphase/pyenphase/pull/67),
  [`403d8dc`](https://github.com/pyenphase/pyenphase/commit/403d8dc5c0361a30b95e57fdeda13ea25fd8179a))

Add schedule to DryContactAction


## v1.5.2 (2023-08-11)

### Bug Fixes

- Add EnvoyEnchargeAggregate to __all__ ([#66](https://github.com/pyenphase/pyenphase/pull/66),
  [`63b7698`](https://github.com/pyenphase/pyenphase/commit/63b76980d620cf7e125df0d6058c80230f66756a))

Add EnvoyEnchargeAggregate to __all__


## v1.5.1 (2023-08-11)

### Bug Fixes

- Switch fetching aggregate Encharge data to simpler endpoint
  ([#65](https://github.com/pyenphase/pyenphase/pull/65),
  [`e076476`](https://github.com/pyenphase/pyenphase/commit/e07647656920779e7a18a045ddfea1dec583fba7))

* Switch fetching aggregate Encharge data to simpler endpoint

* Update tests


## v1.5.0 (2023-08-11)

### Features

- Add EnchargeAggregate model for aggregated battery data
  ([#64](https://github.com/pyenphase/pyenphase/pull/64),
  [`6985935`](https://github.com/pyenphase/pyenphase/commit/69859358ad6c4146fac30198ec5a342633db9834))

* Add EnchargeAggregate model for aggregated battery data

* Update tests


## v1.4.0 (2023-08-10)

### Features

- Add support for toggling grid on/off ([#62](https://github.com/pyenphase/pyenphase/pull/62),
  [`63d44dd`](https://github.com/pyenphase/pyenphase/commit/63d44ddbc59d04ca6afb6b3526a37cda32c7417d))


## v1.3.0 (2023-08-09)

### Features

- Refactor register interface to allow unregistering an updater
  ([#60](https://github.com/pyenphase/pyenphase/pull/60),
  [`82efcec`](https://github.com/pyenphase/pyenphase/commit/82efcec228dbe263c3f1c39e6ded3e9283fbfac2))


## v1.2.2 (2023-08-09)

### Bug Fixes

- Remove unreachable code in inverters updater
  ([#61](https://github.com/pyenphase/pyenphase/pull/61),
  [`84b6be0`](https://github.com/pyenphase/pyenphase/commit/84b6be081cde7bf624baaae2b5df5c1177144dec))


## v1.2.1 (2023-08-09)

### Bug Fixes

- Incorrect typing on enpower mains_*_state attributes
  ([#59](https://github.com/pyenphase/pyenphase/pull/59),
  [`14c7c14`](https://github.com/pyenphase/pyenphase/commit/14c7c14124ca33df6e011b1fa32ed4c57da7e294))

### Chores

- Add collected and mocked fixtures for 3.7.0
  ([#58](https://github.com/pyenphase/pyenphase/pull/58),
  [`56ba6fa`](https://github.com/pyenphase/pyenphase/commit/56ba6fa54cdac7f4680697a5a54d97d595246f30))

- Update 3.17.3 with new fixture downloader ([#57](https://github.com/pyenphase/pyenphase/pull/57),
  [`afb525c`](https://github.com/pyenphase/pyenphase/commit/afb525ce60900192cfa1e088a890da652b1b70bd))

- Update fixtures for 3.9.36 with new fixture fetcher
  ([#56](https://github.com/pyenphase/pyenphase/pull/56),
  [`20e7bbf`](https://github.com/pyenphase/pyenphase/commit/20e7bbfee2d9a49b2cb10bb3766ab6eb6cd2af18))


## v1.2.0 (2023-08-09)

### Chores

- Update firmware 7.3.517 fixtures ([#55](https://github.com/pyenphase/pyenphase/pull/55),
  [`c2dcb19`](https://github.com/pyenphase/pyenphase/commit/c2dcb19e4ea1aef815c145ad5dc688881215dcc2))

### Features

- Refactor to break updaters into modules ([#54](https://github.com/pyenphase/pyenphase/pull/54),
  [`a4686a3`](https://github.com/pyenphase/pyenphase/commit/a4686a30be37f88a3af27257b4a8d017d1579122))


## v1.1.4 (2023-08-08)

### Bug Fixes

- Return DryContactStatus enum for status ([#53](https://github.com/pyenphase/pyenphase/pull/53),
  [`d366ff3`](https://github.com/pyenphase/pyenphase/commit/d366ff3c86a3419bb0ffcbd24a1edb0333b0a32f))

* fix: Return DryContactStatus enum for status

* Update snapshot


## v1.1.3 (2023-08-08)

### Bug Fixes

- Handle envoy sending bad json ([#52](https://github.com/pyenphase/pyenphase/pull/52),
  [`7109e66`](https://github.com/pyenphase/pyenphase/commit/7109e6604f5fc1d1b197a128ceb264c9e00410d4))


## v1.1.2 (2023-08-08)

### Bug Fixes

- Adjust timeouts for when envoy is having trouble with DNS
  ([#51](https://github.com/pyenphase/pyenphase/pull/51),
  [`c82f9bb`](https://github.com/pyenphase/pyenphase/commit/c82f9bbf69f884516985dde04207d375c4953ad3))


## v1.1.1 (2023-08-08)

### Bug Fixes

- Add Enpower and DryContact classes to __all__
  ([#50](https://github.com/pyenphase/pyenphase/pull/50),
  [`d37b5e9`](https://github.com/pyenphase/pyenphase/commit/d37b5e9b6e6f12d62ba57a2f6d745868adf67914))

Add Enpower and DryContacts to __all__


## v1.1.0 (2023-08-08)

### Features

- Add support for pulling dry contact data ([#48](https://github.com/pyenphase/pyenphase/pull/48),
  [`7814650`](https://github.com/pyenphase/pyenphase/commit/78146506bb4a93b51987a2b8725cc32f35368643))

Co-authored-by: J. Nick Koston <nick@koston.org>


## v1.0.0 (2023-08-08)

### Refactoring

- Drop python3.10 support ([#49](https://github.com/pyenphase/pyenphase/pull/49),
  [`9d8c20d`](https://github.com/pyenphase/pyenphase/commit/9d8c20d8f1d9b08b57649f7c8b84715f25312887))


## v0.18.0 (2023-08-08)

### Features

- Add support for polling Enpower data ([#47](https://github.com/pyenphase/pyenphase/pull/47),
  [`0ac58e0`](https://github.com/pyenphase/pyenphase/commit/0ac58e0396d67b4e858deba08eb6bef5c6de9f39))

Add support for polling Enpower data


## v0.17.0 (2023-08-07)

### Features

- Add fixtures for 7.6.114 without clamps ([#44](https://github.com/pyenphase/pyenphase/pull/44),
  [`4be0a33`](https://github.com/pyenphase/pyenphase/commit/4be0a339ed9ae458246f2260e03c5d4c89c58410))

* Add fixtures for 7.6.114

* It's not metered


## v0.16.0 (2023-08-07)

### Features

- Collect headers as well as XML files ([#43](https://github.com/pyenphase/pyenphase/pull/43),
  [`82678be`](https://github.com/pyenphase/pyenphase/commit/82678be2bdcd59b77befc04883b2bb4693789f36))

* Collect headers as well as XML files

* Fix headers

- Update 7.6.175 fixtures ([#45](https://github.com/pyenphase/pyenphase/pull/45),
  [`9c96475`](https://github.com/pyenphase/pyenphase/commit/9c96475f345786a24b5b786a4880a949a01cabd8))

* Update 7.6.175 fixtures


## v0.15.1 (2023-08-07)

### Bug Fixes

- Add Encharge classes to __all__ ([#42](https://github.com/pyenphase/pyenphase/pull/42),
  [`229a84d`](https://github.com/pyenphase/pyenphase/commit/229a84df72a1ec6292f47fe426c46890feb1b83e))


## v0.15.0 (2023-08-07)

### Chores

- Remove unreachable code ([#39](https://github.com/pyenphase/pyenphase/pull/39),
  [`4335835`](https://github.com/pyenphase/pyenphase/commit/43358358ceb32ed114987931e90db1e7176d05ef))

### Features

- Add Encharge battery support ([#40](https://github.com/pyenphase/pyenphase/pull/40),
  [`e1a96e9`](https://github.com/pyenphase/pyenphase/commit/e1a96e9de3ade6429561ef863ed8302b481e02df))

* Add Encharge support

* Update tests

* Update import

* Add Encharge support (#41)

refactor

* Update test snapshot

---------

Co-authored-by: J. Nick Koston <nick@koston.org>


## v0.14.1 (2023-08-07)

### Bug Fixes

- Probe failures with 5.0.62 firmware ([#38](https://github.com/pyenphase/pyenphase/pull/38),
  [`314df6d`](https://github.com/pyenphase/pyenphase/commit/314df6d83c4dfd7c91970e61f86e34218ce46be8))

### Chores

- Add tests for 7.6.175 with CTs ([#37](https://github.com/pyenphase/pyenphase/pull/37),
  [`84884f9`](https://github.com/pyenphase/pyenphase/commit/84884f9c1fa40ba7a78babfb1173a088c4c10248))


## v0.14.0 (2023-08-06)

### Chores

- Add second 7.6.175 fixtures ([#35](https://github.com/pyenphase/pyenphase/pull/35),
  [`6bf5309`](https://github.com/pyenphase/pyenphase/commit/6bf530964b13aa3c20524cc18626f64f15118c00))

### Features

- Add part number ([#36](https://github.com/pyenphase/pyenphase/pull/36),
  [`5b1d46d`](https://github.com/pyenphase/pyenphase/commit/5b1d46dd7c64180fff3118b087330a48de6646fe))


## v0.13.0 (2023-08-06)

### Features

- Add fixture collecting script ([#30](https://github.com/pyenphase/pyenphase/pull/30),
  [`5d66ee9`](https://github.com/pyenphase/pyenphase/commit/5d66ee96154bbd6238a27b6e449b6bb0aece3a54))

Co-authored-by: J. Nick Koston <nick@koston.org>


## v0.12.0 (2023-08-06)

### Chores

- Add test fixtures from Envoy 7.3.517 and Ensemble
  ([#29](https://github.com/pyenphase/pyenphase/pull/29),
  [`31ffcfa`](https://github.com/pyenphase/pyenphase/commit/31ffcfa00bd39c62df3abf791c250b859234f1b3))

Co-authored-by: J. Nick Koston <nick@koston.org>

- Add tests for 7.3.517 firmware/setup ([#33](https://github.com/pyenphase/pyenphase/pull/33),
  [`4d6434f`](https://github.com/pyenphase/pyenphase/commit/4d6434f0af01e0b4aff50d0d5624eb63519f91a5))

- Update gitignore ([#32](https://github.com/pyenphase/pyenphase/pull/32),
  [`57f5b52`](https://github.com/pyenphase/pyenphase/commit/57f5b526706151a0124a99983909a4f3f2aec1e2))

Co-authored-by: J. Nick Koston <nick@koston.org>

### Features

- Probe for Encharge and Enpower support ([#26](https://github.com/pyenphase/pyenphase/pull/26),
  [`da2db7d`](https://github.com/pyenphase/pyenphase/commit/da2db7d8005c81153dff6b5802d3c4851dd79432))

Co-authored-by: J. Nick Koston <nick@koston.org>

### Refactoring

- Small cleanups ([#31](https://github.com/pyenphase/pyenphase/pull/31),
  [`3b4c5ae`](https://github.com/pyenphase/pyenphase/commit/3b4c5ae1070cd2e67df0d1155422a03be8d1c887))


## v0.11.0 (2023-08-06)

### Features

- Add support for bifurcated endpoints ([#28](https://github.com/pyenphase/pyenphase/pull/28),
  [`7853cfd`](https://github.com/pyenphase/pyenphase/commit/7853cfd1ecb2e1cadf8e874f6d351c4efe408a79))


## v0.10.0 (2023-08-06)

### Features

- Add the ability to refresh the token on demand
  ([#25](https://github.com/pyenphase/pyenphase/pull/25),
  [`d1e391c`](https://github.com/pyenphase/pyenphase/commit/d1e391ccd9fcc9fcb3636f6f4a101005998f9f60))


## v0.9.0 (2023-08-05)

### Features

- Add EnvoyTokenAuth to __all__ ([#24](https://github.com/pyenphase/pyenphase/pull/24),
  [`738f4c7`](https://github.com/pyenphase/pyenphase/commit/738f4c7b1385e1045e9ca5065e06b0816d6a398f))


## v0.8.0 (2023-08-05)

### Features

- Add EnvoyData to __all__ ([#23](https://github.com/pyenphase/pyenphase/pull/23),
  [`63f9ba9`](https://github.com/pyenphase/pyenphase/commit/63f9ba94f7d10945aa314836f9a7425cda28ae59))


## v0.7.1 (2023-08-05)

### Bug Fixes

- Legacy installer auth was not working ([#22](https://github.com/pyenphase/pyenphase/pull/22),
  [`a2dd5e5`](https://github.com/pyenphase/pyenphase/commit/a2dd5e55ccfc796d7e162ccc75bb116fde1ca631))


## v0.7.0 (2023-08-05)

### Features

- Export a few more models for type checking ([#21](https://github.com/pyenphase/pyenphase/pull/21),
  [`e2337c4`](https://github.com/pyenphase/pyenphase/commit/e2337c4b8bf69e816611e76e4239fdbea78bf6e9))


## v0.6.1 (2023-08-05)

### Bug Fixes

- Unclosed cloud client session ([#20](https://github.com/pyenphase/pyenphase/pull/20),
  [`b46282a`](https://github.com/pyenphase/pyenphase/commit/b46282a9f9ed20be4487582cd2461a02b7740de6))


## v0.6.0 (2023-08-05)

### Features

- Export names at top level ([#19](https://github.com/pyenphase/pyenphase/pull/19),
  [`b209357`](https://github.com/pyenphase/pyenphase/commit/b2093578d12978da49788ca08c3959d2c3fb3641))


## v0.5.0 (2023-08-05)

### Features

- Add consumption api ([#17](https://github.com/pyenphase/pyenphase/pull/17),
  [`f094c4d`](https://github.com/pyenphase/pyenphase/commit/f094c4d129cbb26e0f6bf3cf9024967a0def46e7))


## v0.4.0 (2023-08-05)

### Chores

- Add comments for properties that come from additional API endpoints
  ([#14](https://github.com/pyenphase/pyenphase/pull/14),
  [`73520b6`](https://github.com/pyenphase/pyenphase/commit/73520b6c72e1dfb867d945054fcada84ee75d879))

- Adjust CI to only validate PR title ([#12](https://github.com/pyenphase/pyenphase/pull/12),
  [`b518216`](https://github.com/pyenphase/pyenphase/commit/b518216d37eadb46b9ad0c785b7182bac94453b2))

- Cleanup duplicate endpoints ([#15](https://github.com/pyenphase/pyenphase/pull/15),
  [`cb0ed2a`](https://github.com/pyenphase/pyenphase/commit/cb0ed2a66c8d4242345dab390b7636cf4c81e7d0))

- Only run action-semantic-pull-request on pull request
  ([#18](https://github.com/pyenphase/pyenphase/pull/18),
  [`ce022aa`](https://github.com/pyenphase/pyenphase/commit/ce022aab4a7594a66ebc97da503a1fc3a0b6b661))

- Start bootstrapping some models ([#13](https://github.com/pyenphase/pyenphase/pull/13),
  [`c5d2f36`](https://github.com/pyenphase/pyenphase/commit/c5d2f364f00c9efd7b3c239d2bb16c6affd84ff7))

* Start bootstrapping some models

* Use slots

* Update src/pyenphase/models/inverter.py

Co-authored-by: J. Nick Koston <nick@koston.org>

* Add model for Enpower/IQ System Controller

* Update class name

* Add model for Encharge/IQ Batteries

* Add model for dry contact relays

* lint

* Add temperature_unit properties

* Add additional Encharge properties from URL_ENCHARGE_BATTERY

* Add comment with data source

* Add comment with data sources

---------

### Features

- Add update functions ([#16](https://github.com/pyenphase/pyenphase/pull/16),
  [`d2802e0`](https://github.com/pyenphase/pyenphase/commit/d2802e0e9322050d37e0affa4a87f127731c29a2))


## v0.3.0 (2023-07-26)

### Chores

- Update deps to fix certifi vuln ([#10](https://github.com/pyenphase/pyenphase/pull/10),
  [`243d28b`](https://github.com/pyenphase/pyenphase/commit/243d28b9e7be10aba73d8f7fefc2123f0ea717fc))

### Features

- Add support for legacy firmware ([#11](https://github.com/pyenphase/pyenphase/pull/11),
  [`49cb15c`](https://github.com/pyenphase/pyenphase/commit/49cb15c58cde38dc41ff30c24c3365c491605274))

Co-authored-by: Joost Lekkerkerker <joostlek@outlook.com>


## v0.2.0 (2023-07-26)

### Chores

- Bump PSR to fix release process ([#8](https://github.com/pyenphase/pyenphase/pull/8),
  [`d2889e2`](https://github.com/pyenphase/pyenphase/commit/d2889e2c10e4565cddee1c10c337159fa4fa4e8b))

- Remove unused labels workflow ([#9](https://github.com/pyenphase/pyenphase/pull/9),
  [`a4c9d1b`](https://github.com/pyenphase/pyenphase/commit/a4c9d1bf158bcc8899c6388dc15d0a4938f78a79))

### Features

- Use sessionId cookie to have access to some endpoints
  ([#7](https://github.com/pyenphase/pyenphase/pull/7),
  [`09a1a8a`](https://github.com/pyenphase/pyenphase/commit/09a1a8aa30f2e3be1aa636f2488dc736f4d4f476))

* auth for D7.0.88 working

* feature: should work at detecting R3.9.36 firmware

* feat: use cookie sessionId

* address review comments

* minor improvs

* use tenacity


## v0.1.0 (2023-05-28)

### Chores

- Add constants for API endpoint URLs ([#5](https://github.com/pyenphase/pyenphase/pull/5),
  [`9583a1f`](https://github.com/pyenphase/pyenphase/commit/9583a1fdc1d6070897fc6793c7f2dc8f13482bc2))

chore: add constants for API endpoint URLs

### Features

- Add initial cloud auth support ([#6](https://github.com/pyenphase/pyenphase/pull/6),
  [`28f4872`](https://github.com/pyenphase/pyenphase/commit/28f4872625a01ee209153d489de566b7ba2302e6))

* auth for D7.0.88 working

* feature: should work at detecting R3.9.36 firmware


## v0.0.3 (2023-05-23)

### Bug Fixes

- Bump versions
  ([`eef5623`](https://github.com/pyenphase/pyenphase/commit/eef56234a9353d110b174b445da1cfb4034d7c1f))

- Drop 3.12
  ([`8e0c0f4`](https://github.com/pyenphase/pyenphase/commit/8e0c0f40ad38152bc13a85566d67c7e86345d291))

- Lint
  ([`683691c`](https://github.com/pyenphase/pyenphase/commit/683691c730e1ef4c491348d66dce70cd75917fd1))

- Permission
  ([`89f9399`](https://github.com/pyenphase/pyenphase/commit/89f9399bccafcc611d83e264d8f4795d43a7f34e))

- Permission
  ([`c73e3ed`](https://github.com/pyenphase/pyenphase/commit/c73e3ed86106d6a9b4ea78c37c1a3133ef0af458))

- Permission
  ([`39e5209`](https://github.com/pyenphase/pyenphase/commit/39e520904e649bb37bd13c790d221b455b4dc90b))

- Permission
  ([`2068511`](https://github.com/pyenphase/pyenphase/commit/2068511f19a8c2c9ac8322937c830762cba27a16))

- Test publish ([#2](https://github.com/pyenphase/pyenphase/pull/2),
  [`e3df6b2`](https://github.com/pyenphase/pyenphase/commit/e3df6b264ca55dc12b75dd602cc1f92fa3a54950))

- Typing
  ([`a75ae30`](https://github.com/pyenphase/pyenphase/commit/a75ae303ef4f98cfafe95081901df7ce88f4fb9e))

- Update ci python version ([#1](https://github.com/pyenphase/pyenphase/pull/1),
  [`4c2dd2e`](https://github.com/pyenphase/pyenphase/commit/4c2dd2e70464b884b9d8a02ccaf39f04f46ab270))

### Chores

- Initial commit
  ([`1c7e27b`](https://github.com/pyenphase/pyenphase/commit/1c7e27b67febf534f5700fd1c6ea3abd7c04ca4b))
