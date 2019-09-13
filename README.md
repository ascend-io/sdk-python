# Ascend SDK for Python

This repo contains the Ascend SDK for Python.
With this SDK, you can
read data from Ascend Components and Data Feeds,
and examine some Dataflow metadata.

Future versions of the SDK will permit full read/write access to Ascend Dataflows.

If you are not yet an Ascend customer, you can
[request a trial](https://www.ascend.io/get-started/).

## Installation

Install the Ascend SDK using `pip` directly from this repo:

```sh
pip install git+https://github.com/ascend-io/ascend-python-sdk.git
```

## Authorization

Using the SDK requires that you create a Service Account in an Ascend Data Service
to give an SDK Client access.

* To access Data Feeds, the Service Account will need at least `Data Feed Read Only` access.
* To access Dataflow metadata and Component data, the Service Account will need at least `Read Only` access.

## Documentation

Read the [SDK Documentation](./docs/markdown/ascend).

## Examples

There are some examples in the Jupyter notebooks in the [examples directory](./examples)
