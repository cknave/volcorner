"""Configuration interface."""

__all__ = [
    # Constants
    'APP_NAME',
    'APP_AUTHOR',
    'APP_DIRS',
    'FILENAME',
    'SECTION_DEFAULTS',
    'DEFAULTS',

    # Functions
    'get_config',
    'config_file_path',
    'create_default_config',
    'read_config_file',
]

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import configparser
import logging
import os.path
import sys

from appdirs import AppDirs

from fastvol.tracking import Corner
from . import keys


# Config file constants
APP_NAME = 'Fastvol'
APP_AUTHOR = 'kvance.com'
APP_DIRS = AppDirs(APP_NAME, APP_AUTHOR)
FILENAME = 'fastvol.conf'

# Config file sections
SECTION_DEFAULTS = 'Defaults'

# Default configuration (non-platform specific)
DEFAULTS = {
    keys.CORNER: 'top-left',
    keys.ACTIVATE_SIZE: 1,
    keys.DEACTIVATE_SIZE: 100,
}

_log = logging.getLogger()


def get_config(argv=sys.argv[1:], app_dirs=APP_DIRS, defaults=DEFAULTS):
    """
    Get the configuration, from the command line and the config file.

    :return: the configuration
    :rtype: argparse.Namespace
    """
    # Get the config file path.
    config_parser = ArgumentParser(add_help=False)  # Help will be added on the real ArgumentParser
    config_parser.add_argument('-c', '--config-file', metavar='FILE',
                               help="specify config file (default: {})".format(_user_config_file_path()))
    path, remaining_argv = config_file_path(config_parser, argv, app_dirs, defaults)

    # Read the defaults from the config file.
    defaults = DEFAULTS.copy()
    config_values = read_config_file(path)
    if config_values:
        defaults.update(config_values)

    # To get a flag name, prefix with '--' and replace '_' with '-'
    flag = lambda s: '--' + s.replace('_', '-')

    # Parse the rest of the command line arguments with the config file as defaults.
    parser = ArgumentParser(parents=[config_parser])
    parser.set_defaults(**defaults)
    parser.add_argument('-a', flag(keys.ACTIVATE_SIZE), type=int, metavar='N',
                        help="hot corner activation size, in pixels")
    parser.add_argument('-d', flag(keys.DEACTIVATE_SIZE), type=int, metavar='N',
                        help="hot corner deactivation size, in pixels")
    parser.add_argument('-x', flag(keys.CORNER), choices=[c.id for c in Corner],
                        help="corner to use")
    return parser.parse_args(remaining_argv)


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
        _log.warn("Ignoring config file %s because it has no %s section.", path, SECTION_DEFAULTS)
        return None


def _user_config_file_path(app_dirs=APP_DIRS):
    """Return the full path to the user's version of the config file."""
    return os.path.join(app_dirs.user_config_dir, FILENAME)
