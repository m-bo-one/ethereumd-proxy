# -*- coding: utf-8 -*-
from setuptools import find_packages, setup
from functools import reduce


with open('README.rst', 'rb') as f:
    readme = f.read().decode('utf-8')


def get_version():
    import ethereumd
    return reduce(lambda x, y: "{0}.{1}".format(x, y), ethereumd.__version__)


setup(
    name='ethereumd-proxy',
    version=get_version(),
    description='Proxy client-server for Ethereum node using '
                'JSON-RPC interface.',
    long_description=readme,
    py_modules=['ethereum_cli'],
    author='Bogdan Kurinnyi',
    author_email='bogdankurinnyi.dev1@gmail.com',
    url='https://github.com/DeV1doR/ethereumd-proxy',
    license='MIT',
    packages=find_packages(),
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
    ],
    entry_points='''
    [console_scripts]
    ethereum-cli=ethereum_cli:cli
    '''
)
