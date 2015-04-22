"""Config file tests."""

from argparse import ArgumentParser
import configparser

from collections import namedtuple
import os
import random
from tempfile import TemporaryDirectory
import volcorner.config


MockAppDirs = namedtuple("MockAppDirs", "user_config_dir")

TEST_CONFIG = """
[Defaults]
key = value
"""


def test_write_default_config():
    """Test writing the default configuration file."""
    defaults = {'key': 'value'}
    with TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'newdir', 'config')
        volcorner.config.create_default_config(path, defaults)
        config = configparser.ConfigParser()
        config.read(path)
        assert config[volcorner.config.SECTION_DEFAULTS]['key'] == 'value'


def test_write_default_config_existing_dir():
    """Test writing the default configuration file in a directory that already exists."""
    with TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'config')
        volcorner.config.create_default_config(path, {})


def test_write_default_config_ignores_mkdir_error():
    """Test writing the default configuration file ignores mkdir errors."""
    with TemporaryDirectory() as tmpdir:
        os.chmod(tmpdir, 0o500)  # Remove write permission
        path = os.path.join(tmpdir, 'newdir', 'config')
        volcorner.config.create_default_config(path, {})
        assert not os.path.exists(path)


def test_write_default_config_ignores_write_error():
    """Test writing the default configuration file ignores write errors."""
    with TemporaryDirectory() as tmpdir:
        os.chmod(tmpdir, 0o500)  # Remove write permission
        path = os.path.join(tmpdir, 'config')
        volcorner.config.create_default_config(path, {})
        assert not os.path.exists(path)


def test_read_config():
    """Test reading a configuration file."""
    with TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'config')
        with open(path, 'w') as config_file:
            config_file.write(TEST_CONFIG)

        config = volcorner.config.read_config_file(config_file.name)
        assert config['key'] == 'value'


def test_read_malformed_config_returns_none():
    """Test reading a malformed configuration file returns None."""
    with TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'config')
        with open(path, 'w') as config_file:
            config_file.write("[malformed")

        config = volcorner.config.read_config_file(config_file.name)
        assert config is None


def test_read_nonexistent_config_returns_none():
    """Test reading a nonexistent configuration file returns None."""
    path = "/does_not_exist_" + str(random.getrandbits(64))
    config = volcorner.config.read_config_file(path)
    assert config is None


def test_config_file_path_creates_default_config():
    """Test that calling config_file_path for the first time creates a default config file."""
    parser = ArgumentParser()
    parser.add_argument('-c', '--config-file')
    with TemporaryDirectory() as tmpdir:
        app_dirs = MockAppDirs(tmpdir)
        path, _ = volcorner.config.config_file_path(parser, [], app_dirs)
        assert path == os.path.join(tmpdir, volcorner.config.FILENAME)
        assert os.path.exists(path)


def test_override_config_file_path():
    """Test overriding the config file path from the command line."""
    parser = ArgumentParser()
    parser.add_argument('-c', '--config-file')
    args = ['--config-file=/overridden']
    with TemporaryDirectory() as tmpdir:
        app_dirs = MockAppDirs(tmpdir)
        path, _ = volcorner.config.config_file_path(parser, args, app_dirs)
        assert path == "/overridden"
        user_path = os.path.join(tmpdir, volcorner.config.FILENAME)
        assert not os.path.exists(user_path)

