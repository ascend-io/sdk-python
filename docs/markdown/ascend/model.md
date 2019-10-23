# ascend.model

## DataService
```python
DataService(self, data_service_id, raw_json=None, session=None)
```

A Data Service is the highest-level organizational structure in
Ascend, and the primary means of controlling access.
It contains one or more Dataflows and can communicate with other
Data Services via Data Feeds.

__Parameters__

- __data_service_id (str)__:
    The ID of the Data Service to connect to
- __raw_json (dict)__:
    The API's JSON definition of the Data Service.
    Used, if provided, to construct the DataService directly
    and avoid one API request.
    (default is `None`)
- __session (ascend.session.Session)__:
    The client session used for HTTP requests.

__Raises__

- `HTTPError`: on API errors

### apply
```python
DataService.apply(self)
```

Upserts this Data Service.

__Raises__

- `HTTPError`: on API errors

### delete
```python
DataService.delete(self)
```

Deletes this Data Service.

__Raises__

- `HTTPError`: on API errors

### get_dataflow
```python
DataService.get_dataflow(self, dataflow_id, raw=False)
```

Get a Dataflow from within the Data Service

__Parameters__

- __dataflow_id (str)__: the ID of the Dataflow

__Returns__

`Dataflow`: the Dataflow

__Raises__

- `HTTPError`: on API errors

### list_dataflows
```python
DataService.list_dataflows(self, raw=False)
```

List all the Dataflows in the Data Service which are accessible to the Client.

__Returns__

`List<Dataflow>`: the Dataflows

__Raises__

- `HTTPError`: on API errors

## Dataflow
```python
Dataflow(self, data_service_id, dataflow_id, raw_json=None, session=None)
```

A Dataflow is where Connectors and Transforms are defined,
and the dependency graph specified.

__Parameters__

- __data_service_id (str)__:
    The ID of the Data Service which contains this Dataflow
- __dataflow_id (str)__:
    The ID of the Dataflow. Must be unique within the Data Service.
- __raw_json (dict)__:
    The API's JSON definition of the Data Service.
    Used, if provided, to construct the DataService directly
    and avoid one API request.
    (default is `None`)
- __session (ascend.session.Session)__:
    The client session used for HTTP requests.

__Raises__

- `HTTPError`: on API errors

### apply
```python
Dataflow.apply(self)
```

Upserts this Dataflow.

__Raises__

- `HTTPError`: on API errors

### delete
```python
Dataflow.delete(self)
```

Deletes this Dataflow.

__Raises__

- `HTTPError`: on API errors

### list_components
```python
Dataflow.list_components(self, raw=False)
```

List the Components (Connectors and Transforms) in the Dataflow.

__Returns__

`List<Component>`: the Components

__Raises__

- `HTTPError`: on API errors

### get_component
```python
Dataflow.get_component(self, component_id, raw=False)
```

Get a Component from a Dataflow

__Parameters__

- __component_id (str)__: the ID of the Component

__Returns__

`Component`: the Component

__Raises__

- `HTTPError`: on API errors

## DataFeed
```python
DataFeed(self, data_service_id, data_feed_id, raw_json=None, session=None)
```

A Data Feed is a live-updated dataset which is produced by a Dataflow in one
Data Service and can be shared with other Data Services.

__Parameters__

- __data_service_id (str)__:
    The ID of the Data Service producing the Data Feed
- __data_feed_id (str)__:
    The ID of the Data Feed. Must be unique within the Data Service.
- __raw_json (dict)__:
    The API's JSON definition of the Data Feed.
    Used, if provided, to construct the Data Feed directly
    and avoid one API request.
    (default is `None`)
- __session (ascend.session.Session)__:
    The client session used for HTTP requests.

__Raises__

- `HTTPError`: on API errors

### apply
```python
DataFeed.apply(self)
```

Upserts this Data Feed.

__Raises__

- `HTTPError`: on API errors

### delete
```python
DataFeed.delete(self)
```

Deletes this Data Feed.

__Raises__

- `HTTPError`: on API errors

### get_records
```python
DataFeed.get_records(self, offset=0, limit=0)
```

Get the records of data from the Data Feed.

__Parameters__

- __offset (int)__:
    index at which records will start streaming from
- __limit (int)__:
    maximum number of records that should be returned

__Returns__

`Iterator<dict>`:
    An iterator over the records of data.
    Can be read into a Pandas DataFrame using `Pandas.DataFrame.from_records()`.

__Raises__

- `ValueError`: on invalid query parameter inputs
- `HTTPError`:  on API errors

## Component
```python
Component(self, data_service_id, dataflow_id, component_id, raw_json=None, session=None)
```

Components are the functional units in a Dataflow.
There are two main types of Components: Connectors and Transforms.

__Parameters__

- __data_service_id (str)__:
    The ID of the Data Service which contains this Dataflow
- __dataflow_id (str)__:
    The ID of the Dataflow. Must be unique within the Data Service.
- __component_id (str)__:
    The ID of the Component. Must be unique within the Dataflow.
- __raw_json (dict)__:
    The API's JSON definition of the Data Service.
    Used, if provided, to construct the DataService directly and avoid one API request.
    (default is `None`)
- __session (ascend.session.Session)__:
    The client session used for HTTP requests.

__Raises__

- `HTTPError`: on API errors

### apply
```python
Component.apply(self)
```

Upserts this Component.

__Raises__

- `HTTPError`: on API errors

### delete
```python
Component.delete(self)
```

Deletes this Component.

__Raises__

- `HTTPError`: on API errors

### get_records
```python
Component.get_records(self, offset=0, limit=0)
```

Get the records of data produced by the Component.

__Parameters__

- __offset (int)__:
    index at which records will start streaming from
- __limit (int)__:
    maximum number of records that should be returned

__Returns__

`Iterator<dict>`:
    An iterator over the records of data.
    Can be read into a Pandas DataFrame using `Pandas.DataFrame.from_records()`.

__Raises__

- `ValueError`: on invalid query parameter inputs or if record streaming is unavailable for this component
- `HTTPError`:  on API errors

### refresh
```python
Component.refresh(self)
```

Triggers a refresh on Read Connectors.

__Raises__

- `HttpError`: on API errors

