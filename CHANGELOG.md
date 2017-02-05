# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased][unreleased]
### Added
### Changed
- Using CFFI in ABI mode to load libasound.so.2 directly instead of needing to
  compile an extension module

### Deprecated
### Removed
- Removed dependency on Xlib since Qt5 supports XCB

### Fixed
### Security

## [0.3.0] - 2017-02-04
### Changed
- Migrate from PyQt4 to PyQt5

### Removed
- README.md no longer has instructions to install PyQt through the OS now that
  it can be installed through pip

## [0.2.3] - 2016-07-30
### Changed
- Allow xcffib 0.4.2 to be used

### Fixed
- UI overlay no longer appears in the task manager or pager
- Removed unused imports

## [0.2.2] - 2016-03-02
### Fixed
- Blacklist xcffib 0.4, which temporarily broke compatibility
- Receive volume updates when other programs change it

## [0.2.1] - 2015-05-06
### Fixed
- UI overlay displays on all desktops
- Overlay no longer eats mouse/keyboard input
- Initial volume is now set

## [0.2.0] - 2015-04-25
### Added
- Qt UI overlay

### Changed
- Somewhat flatten module hierarchy

## [0.1.3] - 2015-04-12
### Fixed
- Fix ungrabbing mouse wheel with any modifier

## [0.1.2] - 2015-04-12
### Added
- Volume setting is now logged

### Fixed
- Mouse wheel is grabbed regardless of any X modifier flags

## [0.1.1] - 2015-03-27
### Fixed
- Build script works when dependencies aren't installed
- Build script points to the correct main script

## 0.1.0 - 2015-03-26
### Added
- Initial release

[unreleased]: https://github.com/cknave/volcorner/compare/volcorner-0.3.0...HEAD
[0.1.1]: https://github.com/cknave/volcorner/compare/volcorner-0.1.0...volcorner-0.1.1
[0.1.2]: https://github.com/cknave/volcorner/compare/volcorner-0.1.1...volcorner-0.1.2
[0.1.3]: https://github.com/cknave/volcorner/compare/volcorner-0.1.2...volcorner-0.1.3
[0.2.0]: https://github.com/cknave/volcorner/compare/volcorner-0.1.3...volcorner-0.2.0
[0.2.1]: https://github.com/cknave/volcorner/compare/volcorner-0.2.0...volcorner-0.2.1
[0.2.2]: https://github.com/cknave/volcorner/compare/volcorner-0.2.1...volcorner-0.2.2
[0.2.3]: https://github.com/cknave/volcorner/compare/volcorner-0.2.2...volcorner-0.2.3
[0.3.0]: https://github.com/cknave/volcorner/compare/volcorner-0.2.3...volcorner-0.3.0
