from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(name='Reto Legacy',
      version='1.7 LTS',
      description='Vote-handling Discord bot! React on messages, give points to the best commenters, and Star stuff to put it in the Best Of channel.',
      long_description=long_description,
      url='http://github.com/honiemun/reto-legacy',
      author='honiemun',
      author_email='honiemun@protonmail.com',
      license='Apache License 2.0',
      install_requires=[
          'discord.py',
          'pyfiglet',
          'tinydb',
          'aiofiles',
          'tinydb-encrypted-jsonstorage',
          'colorama',
          'yaspin'
      ],
      zip_safe=False)