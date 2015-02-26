from setuptools import setup

requires = [
        'cffi',
]

tests_require = [
        'nose',
]

setup(name='fastvol',
      description='Volume hot corner utility',
      author_email='kvance@kvance.com',
      version='0.1',
      packages=['fastvol'],
      scripts=[],
      install_requires=requires,
      tests_require=tests_require,
      test_suite='nose.collector')
