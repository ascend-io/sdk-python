from setuptools import setup

setup(
    name='ascend-python-sdk',
    version='0.0.1',
    description='An SDK for accessing Ascend from Python and Python notebooks',
    url='git@github.com:ascend-io/ascend-python-sdk.git',
    author='Ascend R&D Team',
    author_email='ken@ascend.io',
    license='Apache License 2.0',
    packages=['ascend'],
    install_requires=['requests>=2.22.0'],
    zip_safe=False
)
