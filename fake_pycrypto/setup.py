# fake_pycrypto/setup.py
from setuptools import setup
setup(
    name='pycrypto',
    version='2.6.1',
    description='Fake meta-package to satisfy flask-user',
    install_requires=['pycryptodome'],
    py_modules=['dummy']  # 空模块，占位即可
)