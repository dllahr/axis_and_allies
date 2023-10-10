from setuptools import setup

name = "axis_and_allies"
version = "0.1.0"
author = "Dave Lahr"
author_email = "axisalli.20.dllahr@xoxy.net"
description = "combat simulator for axis and allies"

install_requires = [
    "numpy",
    "pandas",
]

setup(
    name=name,
    version=version,
    author=author,
    author_email=author_email,
    description=description,
    install_requires=install_requires,
)