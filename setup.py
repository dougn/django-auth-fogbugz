#!/usr/bin/env python
from setuptools import setup, find_packages
import django_auth_fogbugz

setup(
    name="django-auth-fogbugz",
    version=django_auth_fogbugz.version_string,
    description="Django FogBugz authentication backend",
    long_description=open('README.rst').read(),
    url="https://github.com/dougn/django-auth-fogbugz/",
    author="Doug Napoleone",
    author_email="doug.napoleone+django-auth-fogbugz@gmail.com",
    license="BSD",
    packages=["django_auth_fogbugz"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Systems Administration :: Authentication/Directory",
        #"Topic :: System :: Systems Administration :: Authentication/Directory :: FogBugz",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=['fogbugz',],
    keywords=["django", "fogbugz", "authentication", "auth"],
)