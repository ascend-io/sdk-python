# Ascend SDK for Python

This repo contains the Ascend SDK for Python.
With this SDK, you can operate on Ascend resources (i.e. Data Feeds, Data Services, Dataflows, Read Connectors, Transforms, and Write Connectors).
The SDK supports create/read/update/delete operations on all aformentioned resources.

If you are not yet an Ascend customer, you can [request a trial](https://www.ascend.io/get-started/).

## Documentation

Read our [Documentation](https://developer.ascend.io/reference).

## Installation

Install the Ascend SDK using `pip` directly from this repo:

```sh
pip install git+https://github.com/ascend-io/sdk-python.git
```

## Authorization

### Developer Access

Developer Access Keys allow user access to all data integrations.
These keys inherit the permission of the user that created them.

More documentation around deverloper access keys can be found [here](https://developer.ascend.io/docs/developer-keys).

### Service Account Access

For third party and application level integration, we encourage the use of service accounts to isolate access points and permission levels.
You should create a Service Account in an Ascend Data Service to obtain SDK Client access.
Service accounts are currently restricted to read-only access for all resources.

* To access Data Feeds, the Service Account will need at least `Data Feed Read Only` access.
* To access Dataflow metadata and Component data, the Service Account will need at least `Read Only` access.

More documentation around service accounts can be found [here](https://developer.ascend.io/docs/service-accounts).

## Examples

There are some examples in the Jupyter notebooks in the [examples directory](./examples)
