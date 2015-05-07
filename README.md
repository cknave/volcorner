Volcorner
=========

A volume hot-corner utility, currently in alpha.

![Screenshot](https://cloud.githubusercontent.com/assets/4196901/7334538/81ac5988-eb64-11e4-8db5-6a6065959d61.png)

System requirements
-------------------

* X11 with XInput2, RANDR, Shape, and XFixes extensions
* ALSA
* Python 3.4 with [CFFI](http://cffi.readthedocs.org/en/latest/)
* [PyQt4](http://www.riverbankcomputing.com/software/pyqt/download)

Installation
------------

CFFI is required to run the setup script.  Make sure it's installed first:

    pip install cffi

PyQt4 is required for the UI overlay.  Install it using your system package manager:

    sudo apt-get install python-qt4   # Ubuntu
    sudo emerge -av dev-python/PyQt4  # Gentoo

pip can then install volcorner along with the remaining dependencies:

    pip install volcorner

Usage
-----

    usage: volcorner [-h] [-c FILE] [-a N] [-d N]
                     [-x {top-left,top-right,bottom-left,bottom-right}] [-v] [-s]

    optional arguments:
      -h, --help            show this help message and exit
      -c FILE, --config-file FILE
                            specify config file (default:
                            $HOME/.config/volcorner/volcorner.conf)
      -a N, --activate-size N
                            hot corner activation size, in pixels
      -d N, --deactivate-size N
                            hot corner deactivation size, in pixels
      -x {top-left,top-right,bottom-left,bottom-right}, --corner {top-left,top-right,bottom-left,bottom-right}
                            corner to use
      -v                    increase verbosity (up to -vvv)
      -s, --save            save this configuration as the new default
