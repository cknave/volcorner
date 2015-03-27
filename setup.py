from setuptools import setup, find_packages

import volcorner.audio.alsa.mixercffi

requires = [
    'appdirs',
    'cffi',
    'smokesignal',
    'xcffib',
]

tests_require = [
    'nose',
]

setup(name='volcorner',
      version='0.1.2',
      description='Volume hot corner utility',
      author='kvance',
      author_email='kvance@kvance.com',
      license='GNU General Public License v3 or later (GPLv3+)',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: X11 Applications',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 3',
          'Topic :: Multimedia :: Sound/Audio'
      ],
      keywords='volume hot corner hotcorner',
      packages=find_packages(),
      # CFFI is not zip safe
      zip_safe=False,
      ext_modules=[
          volcorner.audio.alsa.mixercffi.ffi.verifier.get_extension()
      ],
      entry_points={
          'console_scripts': [
              'volcorner = volcorner.scripts.main:main'
          ]
      },
      install_requires=requires,
      tests_require=tests_require,
      test_suite='nose.collector')
