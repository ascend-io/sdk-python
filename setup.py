from setuptools import setup, find_packages

setup(
    name='ascend-python-sdk',
    version='0.1.0',
    description='A Python library for accessing and version controlling Ascend resources',
    url='git@github.com:ascend-io/ascend-python-sdk.git',
    author='Ascend R&D Team',
    author_email='andy@ascend.io',
    license='Apache License 2.0',
    packages=find_packages(),
    include_package_data=True,
    scripts=['bin/ascend'],
    install_requires=[
        'jinja2',
        'networkx',
        'protobuf',
        'pyyaml',
        'requests>=2.22.0',
        'urllib3',
    ],
    zip_safe=False
)
