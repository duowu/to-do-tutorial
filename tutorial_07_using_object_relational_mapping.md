# Using object-relational mapping

## Table of Contents

* [Introduction](#introduction)
* [Create an SQLAlchemy object](#create-an-sqlalchemy-object)
* [Create a database model](#create-a-database-model)
* [Add custom serialization](#add-custom-serialization)
* [Add custom deserialization](#add-custom-deserialization)
* [Update Item resource GET method](#update-item-resource-get-method)
* [Update Item resource POST method](#update-item-resource-post-method)
* [Update Item resource PUT method](#update-item-resource-put-method)
* [Update Item resource PATCH method](#update-item-resource-patch-method)
* [Update Item resource DELETE method](#update-item-resource-delete-method)
* [Create database tables](#create-database-tables)

## Introduction

* So far, we have been manually interacting with the database. Even after creating the data access object, we still manually manage the database connection and write and directly execute SQL statements with the database.
* However, after we created the data access object, the interactions have been relatively simple, just the standard CRUD operations on rows in the database.
* In the future, we may create more tables in the database and we can create data access objects for them in the same way, abstracting the database connection to class and instance methods, and only using those to interact with the database.
* Since the interactions are so similar for most data access objects, they can be abstracted further.
* Object-relational mapping (ORM) allows us to more easily abstract and use object-oriented programming patterns to easily create data access objects.
* SQLAlchemy is an ORM engine which will handle the abstraction and database interaction for us.
* This also allows us to easily change the database backend in the future, or interact with multiple database backends in the same fashion.
* We can use Flask-SQLAlchemy, a Flask extension which will manage the database connections in SQLAlchemy for us.

## Create an SQLAlchemy object

* Let's start by importing `SQLAlchemy` from `flask_sqlalchemy`.
* After adding a few entries to the configuration of our Flask application `app`, including the database URI, we can create the `SQLAlchemy` object `db`.

```python
from flask import Flask, request, Response
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from jsonpickle import encode

db_path = 'app.db'  # The path to the SQLite3 database file
app = Flask(__name__)  # The Flask application object
api = Api(app)  # The API object for Flask-RESTful

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
db = SQLAlchemy(app=app)  # The SQLAlchemy object for ORM

...
```

## Create a database model

* A database model class represents the corresponding table in the database, and instances of the class represents corresponding rows in the table.
* Now that we have the ORM object created, we can create a database model class `Item` which replaces the `Item` class we created earlier as a data access object.
* The new `Item` class should extend from `db.Model`.
* This the declarative base model class which all of the database models for our database is to extend from (only one at this time).
* Each column is represented as a class attribute which is defined from a `db.Column` object.

```python
...

db = SQLAlchemy(app=app)  # The SQLAlchemy object for ORM


class Item(db.Model):
    """
    This class represents a To-Do item.

    Columns:
        uid (int): Unique identifier for the item
        name (str): Name of the item
        description (str): Description of the item
        completed (bool): Whether or not the item is completed. The
            default value is `False`.
    """
    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(length=100), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)

...
```

## Add custom serialization

* In the earlier `Item` data access object, it was a simple object with simple attributes. `jsonpickle` could automatically serialize instance of that class.
* However, since we are extending from `db.Model`, the the new `Item` database model is much more complicated, and `jsonpickle` will not be able to serialize instances automatically the way we want.
* This means we will need to create a method to help `jsonpickle`.
* The magic method `__getstate__` is an instance method which `jsonpickle` can use for custom serialization.
* We simply need to return a dictionary which represents the current object.

```python
class Item(db.Model):
    ...

    def __getstate__(self):
        """
        Get the state of the object serialization.

        Returns:
            dict: State of the object in dictionary form
        """
        return {
            'uid': self.uid,
            'name': self.name,
            'description': self.description,
            'completed': self.completed
        }

...
```

## Add custom deserialization

* As with the earlier `Item` data access object, we can create a method for deserialization from a dictionary.
* Since we kept the column and attribute names the same, this instance method has the same logic as the previous one.

```python
class Item(db.Model):
    ...

    def __getstate__(self):
        ...

    def from_dict(self, data):
        """
        Deserialize a dictionary to populate the attributes of the
        current object.

        Only attributes of the current object which are in the
        dictionary are updated. The unique identifier is not updated.

        Args:
            data (dict): Dictionary containing all or partial attributes
                to deserialize.

        Returns:
            Item: Allow for method chaining of self
        """
        try:
            if 'name' in data:
                self.name = data['name']
            if 'description' in data:
                self.description = data['description']
            if 'completed' in data:
                self.completed = data['completed']
        except TypeError:
            pass

        return self

...
```

## Update Item resource GET method

* For the item resource GET method, we need to add logic to fetch one or all items from the database.
* `Item.query.filter_by` allows us to add any filter we need for the query, which in this case is simply `uid=uid`.
* The `first` method for queries returns the first item from the query results, and `None` if there were no results.
* This means we need to manually check if nothing was returned and raise a lookup exception if the item was not found.
* In the case where we need fetch all items, we simply use the `all` method on the base query which will return a collection of all rows from the table in the database.

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
        # The unique identifier is provided, so fetch that one item
        if uid:
            # The `first` method for queries returns `None` if there is
            # nothing in the returned query
            item = Item.query.filter_by(uid=uid).first()
            if item is None:
                raise LookupError('Item not found')
            return item
        else:
            return Item.query.all()

...
```

## Update Item resource POST method

* For the item resource POST method, we still need to create a new instance of `Item` and populate it with the data from the payload of the request.
* We simply need to add the `Item` object to the session and commit it.

```python
class ItemResource(Resource):
    ...

    @create_response
    def get(self, uid=None):
        ...
            return Item.query.all()

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
        item = Item().from_dict(data=request.json)
        db.session.add(item)
        db.session.commit()
        return item

...
```

## Update Item resource PUT method

* For the item resource PUT method, we need to fetch the `Item` object by its unique identifier in the same way as the GET method.
* After we have the item, we can now populate it with data from the payload of the request and commit the changes in the session.

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
        # the database. The `first` method for queries returns `None` if
        # there is nothing in the returned query.
        item = Item.query.filter_by(uid=uid).first()
        if item is None:
            raise LookupError('Item not found')
        item.from_dict(data=request.json)
        db.session.commit()
        return item

...
```

## Update Item resource PATCH method

* For the item resource PATCH method, we need to fetch the `Item` object by its unique identifier in the same way as the GET method.
* After we have the item, we can now populate it with data from the payload of the request and commit the changes in the session.

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
        # the database. The `first` method for queries returns `None` if
        # there is nothing in the returned query.
        item = Item.query.filter_by(uid=uid).first()
        if item is None:
            raise LookupError('Item not found')
        item.from_dict(data=request.json)
        db.session.commit()
        return item

...
```

## Update Item resource DELETE method

* For the item resource PUT method, we need to fetch the `Item` object by its unique identifier in the same way as the GET method.
* After we have the item, we can now delete it from the session and commit it.

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
        # Fetch and delete the item from the database. The `first`
        # method for queries returns `None` if there is nothing in
        # the returned query.
        item = Item.query.filter_by(uid=uid).first()
        if item is None:
            raise LookupError('Item not found')
        db.session.delete(item)
        db.session.commit()
```

## Create database tables

* The ORM can also manage the creation of the tables for us.
* We can remove the function `create_tables` which manually created the tables using SQL.
* This is the last of the direct usages of `sqlite3`, which we can remove the import statement.
* Instead, we simply need to execute the `db.create_all` method, which tells `SQLAlchemy` to create all the tables based on all the database models which we created (extend from `db.Model`). 

```python
...


class Item(db.Model):
    ...


def create_response(function):
    ...


class ItemResource(Resource):
    ...


api.add_resource(ItemResource, '/items', '/items/<int:uid>')

if __name__ == '__main__':
    # Make sure all the tables are created in the database before
    # running the Flask application
    db.create_all()
    app.run(port=8002, debug=True)

```
