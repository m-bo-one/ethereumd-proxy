# -*- coding: utf-8 -*-
from setuptools import find_packages, setup
from pip.req import parse_requirements


VERSION = '0.1.dev'

with open('README.rst', 'rb') as f:
    readme = f.read().decode('utf-8')


install_reqs = parse_requirements('requirements.txt', session='hack')
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='ethereumd-proxy',
    version=VERSION,
    description='Ethereum proxy to geth node',
    long_description=readme,
    py_modules=['ethereumd_cli'],
    author='Bogdan Kurinnyi',
    author_email='bogdankurinnyi.dev1@gmail.com',
    url='https://github.com/DeV1doR/ethereumd-proxy',
    license='MIT',
    packages=find_packages(),
    install_requires=reqs,
    entry_points='''
    [console_scripts]
    ethereumd-cli=ethereumd_cli:cli
    '''
)
