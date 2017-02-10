"""Configuration interface."""

from argparse import ArgumentParser
import configparser
import logging
import sys

import os.path
from appdirs import AppDirs
import volcorner.logging
from volcorner.corner import Corner

__all__ = [
    # Constants
    'APP_NAME',
    'APP_AUTHOR',
    'APP_DIRS',
    'FILENAME',
    'SECTION_DEFAULTS',
    'DEFAULTS',
    'KEY_ACTIVATE_SIZE',
    'KEY_DEACTIVATE_SIZE',
    'KEY_CORNER',
    'KEY_VERBOSE',

    # Functions
    'get_config',
    'config_file_path',
    'create_default_config',
    'read_config_file',
    'log_level_for_verbosity',
    'write_config',
]

# Config file constants
APP_NAME = 'volcorner'
APP_AUTHOR = 'kvance.com'
APP_DIRS = AppDirs(APP_NAME, APP_AUTHOR)
FILENAME = 'volcorner.conf'

# Config file sections
SECTION_DEFAULTS = 'Defaults'

# Config file keys
KEY_ACTIVATE_SIZE = "activate_size"
KEY_DEACTIVATE_SIZE = "deactivate_size"
KEY_CORNER = "corner"
KEY_VERBOSE = "verbose"
ALL_KEYS = (KEY_ACTIVATE_SIZE, KEY_DEACTIVATE_SIZE, KEY_CORNER, KEY_VERBOSE)

# Default configuration (non-platform specific)
DEFAULTS = {
    KEY_CORNER: 'top-left',
    KEY_ACTIVATE_SIZE: 1,
    KEY_DEACTIVATE_SIZE: 100,
    KEY_VERBOSE: 0,
}

_log = logging.getLogger("config")


def get_config(argv=sys.argv[1:], app_dirs=APP_DIRS, defaults=DEFAULTS):
    """
    Get the configuration, from the command line and the config file.

    :return: (configuration, path) tuple
    :rtype: (Namespace, str)
    """
    # Get the config file path.
    config_parser = ArgumentParser(add_help=False)  # Help will be added on the real ArgumentParser
    config_parser.add_argument('-c', '--config-file', metavar='FILE',
                               help="specify config file (default: %s)" % _user_config_file_path())
    path, remaining_argv = config_file_path(config_parser, argv, app_dirs, defaults)

    # Read the defaults from the config file.
    defaults = DEFAULTS.copy()
    config_values = read_config_file(path)
    if config_values:
        defaults.update(config_values)

    # Coerce types
    defaults['verbose'] = int(defaults['verbose'])

    def flag(s):
        """To get a flag name, prefix with '--' and replace '_' with '-'."""
        return '--' + s.replace('_', '-')

    # Parse the rest of the command line arguments with the config file as defaults.
    parser = ArgumentParser(parents=[config_parser])
    parser.set_defaults(**defaults)
    parser.add_argument('-a', flag(KEY_ACTIVATE_SIZE), type=int, metavar='N',
                        help="hot corner activation size, in pixels")
    parser.add_argument('-d', flag(KEY_DEACTIVATE_SIZE), type=int, metavar='N',
                        help="hot corner deactivation size, in pixels")
    parser.add_argument('-x', flag(KEY_CORNER), choices=[c.id for c in Corner],
                        help="corner to use")
    parser.add_argument('-v', dest=KEY_VERBOSE, action='count',
                        help="increase verbosity (up to -vvv)")
    parser.add_argument('-s', '--save', action='store_true',
                        help="save this configuration as the new default")
    return parser.parse_args(remaining_argv), path


def config_file_path(parser, argv, app_dirs=APP_DIRS, defaults=DEFAULTS):
    """
    Find the config file path, either from the command line or in the user's config directory.

    If no path was specified on the command line, and the user file doesn't exist yet, create it.

    :param ArgumentParser parser: Argument parser with only the config-file option
    :param argv: Argument list to parse
    :param app_dirs: The AppDirs object containing the user's config path
    :param defaults: The defaults to write, if the user's config file doesn't exist yet
    :return: a tuple of (file path, remaining args to parse)
    """
    # Use the commandline argument if it exists.
    args, remaining_argv = parser.parse_known_args(argv)
    if args.config_file:
        _log.debug("Using config path from command line %s", args.config_file)
        return args.config_file, remaining_argv

    # Otherwise use the default.
    path = _user_config_file_path(app_dirs)
    if not os.path.exists(path):
        create_default_config(path, defaults)
    return path, remaining_argv


def create_default_config(path, defaults):
    """
    Attempt to create the default config file at this path.  Do nothing if it fails.

    :param path: the path to the new file
    :param defaults: dictionary of defaults to write to the Defaults section.
    """
    # Make the directory.
    directory, filename = os.path.split(path)
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError:
        _log.error("Failed to make config directory %s", directory, exc_info=True)
        return

    # Write out the defaults.
    config = configparser.ConfigParser()
    config[SECTION_DEFAULTS] = defaults
    try:
        with open(path, 'w') as config_file:
            config.write(config_file)
    except OSError:
        _log.error("Failed to write default config file %s", path, exc_info=True)


def read_config_file(path):
    """
    Read the dictionary of defaults from a config file.

    :param path: path to the config file
    :return: dictionary of defaults, or None if unable to read it
    """
    config = configparser.ConfigParser()
    try:
        config.read(path)
    except (OSError, configparser.Error):
        _log.error("Failed to read config file %s.  Using the defaults.", path, exc_info=True)
        return None

    try:
        return config[SECTION_DEFAULTS]
    except KeyError:
        _log.warning("Ignoring config file %s because it has no %s section.", path,
                     SECTION_DEFAULTS)
        return None


def write_config(config, path):
    """
    Write an argparse Namespace out to a config file.

    :param Namespace config: the configuration Namespace to write
    :param str path: the path to write to
    """
    # Build a dict of the configuration keys and their values
    cvars = vars(config)
    defaults = {k: cvars[k] for k in ALL_KEYS}

    writer = configparser.ConfigParser()
    writer[SECTION_DEFAULTS] = defaults
    with open(path, 'w') as config_file:
        writer.write(config_file)


def log_level_for_verbosity(verbosity):
    """
    Return the python logging level for a verbosity config value.

    :param verbosity: the verbosity argument count
    :return: the logging level
    """
    if verbosity == 0:
        return logging.WARNING
    elif verbosity == 1:
        return logging.INFO
    elif verbosity == 2:
        return logging.DEBUG
    elif verbosity == 3:
        return volcorner.logging.TRACE


def _user_config_file_path(app_dirs=APP_DIRS):
    """Return the full path to the user's version of the config file."""
    return os.path.join(app_dirs.user_config_dir, FILENAME)
