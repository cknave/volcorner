Volcorner
=========

A volume hot-corner utility, currently in alpha.

System requirements
-------------------

* X11 with XInput2 and RANDR extensions
* ALSA
* Python 3.4 with [CFFI](http://cffi.readthedocs.org/en/latest/)

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
