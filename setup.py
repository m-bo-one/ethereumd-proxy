import os
import sys
import re

from setuptools import find_packages, setup


if sys.version_info >= (3, 5):
    pass
else:
    raise RuntimeError("ethereumd doesn't support Python version prior 3.5")


def read(*parts):
    with open(os.path.join(*parts), 'rt') as f:
        return f.read().strip()


def read_version():
    regexp = re.compile(r"^__version__\W*=\W*'([\d.abrc]+)'")
    init_py = os.path.join(os.path.dirname(__file__),
                           'ethereumd', '__init__.py')
    with open(init_py) as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1)
        else:
            raise RuntimeError('Cannot find version in '
                               'ethereumd/__init__.py')


setup(
    name='ethereumd-proxy',
    version=read_version(),
    description='Proxy client-server for Ethereum node using '
                'JSON-RPC interface.',
    long_description="\n\n".join((read('README.rst'), read('CHANGES.rst'))),
    py_modules=['ethereum_cli'],
    author='Bogdan Kurinnyi',
    author_email='bogdankurinniy.dev1@gmail.com',
    url='https://github.com/DeV1doR/ethereumd-proxy',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
        'sanic==0.5.4',
        'aiohttp==2.2.3',
        'APScheduler==3.3.1',
        'colorlog==2.10.0',
        'click==6.7',
        'requests==2.9.1',
        'ujson==1.35',
        'aioethereum==0.1.0',
    ],
    entry_points='''
    [console_scripts]
    ethereum-cli=ethereum_cli:cli
    '''
)
