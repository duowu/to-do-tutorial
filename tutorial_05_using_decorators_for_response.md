# Using decorators for response

## Table of Contents

* [Introduction](#introduction)
* [Create a wrapper decorator to create responses](#create-a-wrapper-decorator-to-create-responses)
* [Update the fetch all items route](#update-the-fetch-all-items-route)
* [Update the fetch one item route](#update-the-fetch-one-item-route)
* [Update the create item route](#update-the-create-item-route)
* [Update the update item route](#update-the-update-item-route)
* [Update the partial update item route](#update-the-partial-update-item-route)
* [Update the delete item route](#update-the-delete-item-route)

## Introduction

* By this point, we have duplicated a lot of logic in the Flask routes.
* Take note that every route creates a Flask response object based on the results of an action (or any exceptions raised) and may contain some data which has been serialized to a JSON encoded string.
* With the help of decorators in Python, we can abstract a lot of the logic to simplify and clean the code.

## Create a wrapper decorator to create responses

* We can start by creating a wrapper decorator function which wraps a function and create a Flask response object from the results.
* This function is to use the `wraps` decorator from the `functools` module, so it needs to be imported.
* The wrapper simply needs to execute the wrapped function and save the results.
* We can wrap that in a try-except block to catch any raised exceptions and create a message.
* After we have the result from the execution of the wrapped function or a message resulting from a raised exception, we can create a response with the serialized data as the payload.
* We should set the response status code based on success or error.
* With this decorator, we can now update all of the route functions. There is no longer a need to catch exceptions within the routes, create responses, nor serialize the data. We can simply return the data and the decorator will take care of the rest for us.

```python
import sqlite3
from flask import Flask, request, Response
from functools import wraps
from jsonpickle import encode

...


class Item(object):
    ...


def create_response(function):
    """
    Wrapper decorator which wraps a function and creates a response from
    the results.

    The wrapped function is called with all the passed arguments and
    keyword arguments and returned data is saved. All exceptions are
    caught and an error message is created from the exception.

    A Flask response object is created where the payload is a JSON
    serialized string of the results (or error message) created with
    the `encode` function of the `jsonpickle` package. The status code
    is 200 if no exceptions are raised, 404 if a lookup exception was
    raise, and 400 for all other exceptions.

    Args:
        function (Callable function): Function to wrap

    Returns:
        Callable function: Wrapped function
    """

    @wraps(wrapped=function)
    def wrapper(*args, **kwargs):
        """
        Wrap a function. See above for details.

        Args:
            *args: Arguments to pass through to the wrapped function
            **kwargs: Keyword arguments to pass through to the wrapped
                function

        Returns:
            Response: Flask response object
        """
        try:
            # Execute the function and store any returned data
            data = function(*args, **kwargs)
            status_code = 200

        except Exception as error:
            # Create a message for the user on any raised exceptions and
            # change the status code based on the exception type
            data = {'message': str(error)}
            status_code = 404 if isinstance(error, LookupError) else 400

        # Create the response object with serialized data. The payload
        # is set to `None` if there was no result from the called
        # function, this is to ensure an empty payload.
        return Response(
            response=encode(value=data, unpicklable=False) if data else None,
            status=status_code,
            mimetype='application/json'
        )

    return wrapper

...
```

## Update the fetch all items route

* For the route to fetch all items, we simply need to return all items from the database after applying the decorator.
* Note the changes in the docstring, as the return type of the function itself is different, although the decorator will change that by creating the response for us.

```python
@app.route('/items', methods=['GET'])
@create_response
def fetch_all_items():
    """
    HTTP GET route to fetch all To-Do items from the database.

    Returns:
        List[Item]: Collection of all items retrieved from the database
    """
    # Fetch all items from the database
    return Item.fetch()
```

## Update the fetch one item route

* For the route to fetch one item, we simply need to return that item from the database after applying the decorator.

```python
@app.route('/items/<int:uid>')
@create_response
def fetch_one_item(uid):
    """
    HTTP GET route to fetch a single To-Do item from the database by its
    unique identifier.

    Args:
        uid (int): Unique identifier of the item

    Returns:
        Item: Item retrieved from the database
    """
    # Fetch one item from the database
    return Item.fetch(uid=uid)
```

## Update the create item route

* For the route to create an item, we simply need to return the created item after applying the decorator.
* Because of method chaining in most of the methods of the `Item` class, this can actually be done in a single line: create a new instance of `Item`, populate it with the data from the request, save it to the database, and return that result.

```python
@app.route('/items', methods=['POST'])
@create_response
def create_item():
    """
    HTTP POST route to create a To-Do item in the database based on
    data supplied from the user.

    JSON Payload:
        {
            "name": string,         <-- Required name of the item
            "description": string,  <-- Optional description of the item
            "completed": boolean    <-- Optional status of the item
        }

    Returns:
        Item: Created item
    """
    # Get the deserialized JSON data from the HTTP request, extract the
    # required and optional attributes, and create a new item in the
    # database.
    return Item().from_dict(data=request.json).create()
```

## Update the update item route

* For the route to update an item, we simply need to return the updated item after applying the decorator.
* Like the create route, this can also be done in a single line: get an instance of the item from the database based on the unique identifier, populate it with data from the request, update it in the database, and return that result.

```python
@app.route('/items/<int:uid>', methods=['PUT'])
@create_response
def update_item(uid):
    """
    HTTP PUT route to update an item by replacing its attributes with
    those supplied by the payload of the HTTP request.

    Args:
        uid (uid): Unique identifier of the item

    JSON Payload:
        {
            "name": string,         <-- Required name of the item
            "description": string,  <-- Optional description of the item
            "completed": boolean    <-- Optional status of the item
        }

    Returns:
        Item: Updated item
    """
    # Get the deserialized JSON data from the HTTP request, extract the
    # required and optional attributes, and update the item in the
    # database.
    return Item.fetch(uid=uid).from_dict(data=request.json).update()
```

## Update the partial update item route

* For the route to partially update an item, we simply need to return the updated item after applying the decorator.

```python
@app.route('/items/<int:uid>', methods=['PATCH'])
@create_response
def partial_update_item(uid):
    """
    HTTP PATCH route to partially update an item with attributes
    supplied by the payload of the HTTP request.

    Args:
        uid (int): Unique identifier of the item

    Returns:
        Item: Updated item
    """
    # Get the deserialized JSON data from the HTTP request, extract the
    # required and optional attributes, and update the item in the
    # database.
    return Item.fetch(uid=uid).from_dict(data=request.json).update()
```

## Update the delete item route

* For the route to delete an item, we simply need to fetch and delete the item from the database based on the unique identifier.
* Nothing else needs to be done, as we are not returning anything for the payload of the response.

```python
@app.route('/items/<int:uid>', methods=['DELETE'])
@create_response
def delete_item(uid):
    """
    HTTP DELETE route to delete an item from the database.

    Args:
        uid (int): Unique identifier of the item
    """
    # Fetch and delete the item from the database
    Item.fetch(uid=uid).delete()
```
