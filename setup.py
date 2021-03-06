# Copyright (c) 2018 Stephen Bunn (stephen@bunn.io)
# MIT License <https://opensource.org/licenses/MIT>

import os
import sys
import shutil
import setuptools


CURDIR = os.path.abspath(os.path.dirname(__file__))
REQUIRES = [
    'furl',
    'ujson',
    'attrs',
    'blinker',
    'requests-html',
    'click',
    'click-completion',
    'yaspin',
    'plumbum',
    'tqdm',
    'log-symbols'
]
TEST_REQUIRES = [
    'pytest',
]
SETUP_REQUIRES = [
    'pytest-runner',
]
PACKAGE = {}

# NOTE: important dumb setup for complete segregation of module info
with open(os.path.join(CURDIR, 'qetch', '__version__.py'), 'r') as fp:
    exec(fp.read(), PACKAGE)


class UploadCommand(setuptools.Command):

    description = 'Build and publish package'
    user_options = []

    @staticmethod
    def status(status):
        print(('... {status}').format(**locals()))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('removing previous builds')
            shutil.rmtree(os.path.join(CURDIR, 'dist'))
        except FileNotFoundError:
            pass

        self.status('building distribution')
        os.system(('{exe} setup.py sdist').format(exe=sys.executable))

        self.status('uploading distribution')
        os.system('twine upload dist/*')

        self.status('pushing git tags')
        os.system(('git tag v{ver}').format(ver=PACKAGE['__version__']))
        os.system('git push --tags')

        sys.exit()

setuptools.setup(
    name=PACKAGE['__name__'],
    version=PACKAGE['__version__'],
    description=PACKAGE['__description__'],
    long_description=open(os.path.join(CURDIR, 'README.rst'), 'r').read(),
    license=PACKAGE['__license__'],
    author=PACKAGE['__author__'],
    author_email=PACKAGE['__contact__'],
    url='https://github.com/stephen-bunn/qetch',
    include_package_data=True,
    install_requires=REQUIRES,
    packages=setuptools.find_packages(),
    keywords=['qetch'],
    entry_points={
        'console_scripts': ['qetch=qetch.cli:cli']
    },
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Natural Language :: English',
    ],
    test_suite='tests',
    tests_require=TEST_REQUIRES,
    setup_requires=SETUP_REQUIRES,
    cmdclass={
        'upload': UploadCommand,
    },
)
