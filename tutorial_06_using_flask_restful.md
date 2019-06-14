# Using Flask-RESTful

## Table of Contents

* [Introduction](#introduction)
* [Create an API object](#create-an-api-object)
* [Create an item resource class](#create-an-item-resource-class)
* [Create a method for GET](#create-a-method-for-get)
* [Create a method for POST](#create-a-method-for-post)
* [Create a method for PUT](#create-a-method-for-put)
* [Create a method for PATCH](#create-a-method-for-patch)
* [Create a method for DELETE](#create-a-method-for-delete)
* [Add item resource to the API](#add-item-resource-to-the-API)

## Introduction

* Since we are creating a RESTful API, all of the routes for the `Item` resource are related. In this simple application, we only have one resource, but in larger applications, you may have more than one.
* Keeping track of all of the routes can become messy and organizing them can take quite the effort, especially when splitting them into their own files.
* We can use Flask-RESTful, an extension created for Flask, to better organize the routes by the resource and HTTP method.

## Create an API object

* Let's start by importing `Api` and `Resource` from `flask_restful` and creating an `Api` object for our Flask application `app`.

```python
import sqlite3
from flask import Flask, request, Response
from flask_restful import Api, Resource
from functools import wraps
from jsonpickle import encode

db_path = 'app.db'  # The path to the SQLite3 database file
app = Flask(__name__)  # The Flask application object
api = Api(app)  # The API object for Flask-RESTful

...
```

## Create an item resource class

* Let's now create a resource class `ItemResource` to provided create, read, update, and delete (CRUD) actions for accessing items by extending from the `Resource` class from `flask_restful`.
* We will define methods for this class will define how the HTTP methods are to be handled.
* The instance methods `get`, `post`, `put`, `patch`, and `delete` correspond with the HTTP methods by the same name.

```python
...


class Item(object):
    ...


def create_response(function):
    ...


class ItemResource(Resource):
    """
    This resource class provides create, read, update, and delete (CRUD)
    actions for the item resource using HTTP methods.
    """
```

## Create a method for GET

* We can now create an instance method for the `ItemRoute` class which defines how HTTP GET method is handled.
* This is combining the route to fetch all and fetch one item.
* The `uid` is an optional argument which will be part of the route's URL.
* Because `Item.fetch` takes an optional `uid` argument, we can simply return the result of that method call as it will either return one item or a collection of all items.
* Note that we can wrap the `get` method with the `create_response` decorator which will catch any exceptions, serialize the results, and create a response for us.

```python
class ItemResource(Resource):
    ...

    @create_response
    def get(self, uid=None):
        """
        HTTP GET method to fetch one To-Do item by its unique identifier
        or a collection of all To-Do items from the database.

        Args:
            uid (int): Optional. Unique identifier of the item

        Returns:
            Item or List[Item]: One item or a collection of all items
                retrieved from the database
        """
        return Item.fetch(uid)
```

## Create a method for POST

* For the HTTP POST method, we can use the same code as the route to create an item.

```python
class ItemResource(Resource):
    ...

    @create_response
    def get(self, uid=None):
        ...

    @create_response
    def post(self):
        """
        HTTP POST method to create a To-Do item in the database based on
        the data supplied from the user.

        JSON Payload:
            {
                "name": string,         <-- Required name of the item
                "description": string,  <-- Optional description of the item
                "completed": boolean    <-- Optional status of the item
            }

        Returns:
            Item: Created item
        """
        # Get the deserialized JSON data from the HTTP request, extract
        # the required and optional attributes, and create a new item in
        # the database.
        return Item().from_dict(data=request.json).create()
```

## Create a method for PUT

* The HTTP PUT method corresponds to the route to update an item.

```python
class ItemResource(Resource):
    ...

    @create_response
    def get(self, uid=None):
        ...

    @create_response
    def post(self):
        ...

    @create_response
    def put(self, uid):
        """
        HTTP PUT method to update an item by replacing its attributes
        with those supplied by the payload of the HTTP request.

        Args:
            uid (int): Unique identifier of the item

        Returns:
            Item: Updated item
        """
        # Get the deserialized JSON data from the HTTP request, extract
        # the required and optional attributes, and update the item in
        # the database.
        return Item.fetch(uid=uid).from_dict(data=request.json).update()
```

## Create a method for PATCH

* The HTTP PATCH method corresponds to the route to partially update an item.

```python
class ItemResource(Resource):
    ...

    @create_response
    def get(self, uid=None):
        ...

    @create_response
    def post(self):
        ...

    @create_response
    def put(self, uid):
        ...

    @create_response
    def patch(self, uid):
        """
        HTTP PATCH method to partially update an item with attributes
        supplied by the payload of the HTTP request.

        Args:
            uid (int): Unique identifier of the item

        Returns:
            Item: Updated item
        """
        # Get the deserialized JSON data from the HTTP request, extract
        # the required and optional attributes, and update the item in
        # the database.
        return Item.fetch(uid=uid).from_dict(data=request.json).update()
```

## Create a method for DELETE

* The HTTP DELETE method corresponds to the route to delete an item.

```python
class ItemResource(Resource):
    ...

    @create_response
    def get(self, uid=None):
        ...

    @create_response
    def post(self):
        ...

    @create_response
    def put(self, uid):
        ...

    @create_response
    def patch(self, uid):
        ...

    @create_response
    def delete(self, uid):
        """
        HTTP DELETE method to delete an item from the database.

        Args:
            uid (int): Unique identifier of the item
        """
        # Fetch and delete the item from the database
        Item.fetch(uid=uid).delete()
```

## Add item resource to the API

* Now that the `ItemResource` class is populated, we can add the resource to the `Api` object we created earlier.
* This is where we define the URL for the route. For this route, there are 2 possible URLs, one with the unique identifier and one without the unique identifier.
* At this point we can now remove all of the routes which we created directly for the application, as all of the functionality is now covered by the `ItemResource` class in the `Api` object.

```python
...

app = Flask(__name__)  # The Flask application object
api = Api(app)  # The API object for Flask-RESTful


class Item(object):
    ...


def create_response(function):
    ...


class ItemResource(Resource):
    ...


api.add_resource(ItemResource, '/items', '/items/<int:uid>')

...
```
