# Using data access objects

## Table of Contents

* [Introduction](#introduction)
* [Create a method to fetch all items or one item](#create-a-method-to-fetch-all-items-or-one-item)
* [Create a method to create an item](#create-a-method-to-create-an-item)
* [Create a method to update an item](#create-a-method-to-update-an-item)
* [Create a method to delete an item](#create-a-method-to-delete-an-item)
* [Update the fetch all items route](#update-the-fetch-all-items-route)
* [Update the fetch one item route](#update-the-fetch-one-item-route)
* [Update the create item route](#update-the-create-item-route)
* [Update the update item route](#update-the-update-item-route)
* [Update the partial update item route](#update-the-partial-update-item-route)
* [Update the delete item route](#update-the-delete-item-route)

## Introduction

* By this point, we have a class which represents item objects and Flask routes to interact with them. However, the code is not very reusable outside of the Flask application. If we wanted to create a small script which interacts with the `item` table in the database, we would still have to write explicit SQL statements to interact with the database.
* To make our code more flexible, we can use a data access object to interact with the database. In this case, if needed, we can just interact with the `Item` instead of directly interacting with the database.
* We can start by creating methods for the CRUD actions (create, read, update, and delete) for the `Item` class.

## Create a method to fetch all items or one item

* Let's start by creating a method for the `Item` class to fetch all or one item from the database and populate a collection of `Item` objects or one `Item` object.
* We need to make this a class method as this will follow a factory pattern.
* This method is to take an optional `uid` argument which is a unique identifier for an `Item` object.
* As with the previous routes, we need to manage the database connection.
* If the `uid` is provided, then create populate an `Item` object with data fetched from corresponding row in the database.
* If the `uid` is provided, but the corresponding item cannot be found in the database, raise and exception.
* If the `uid` is not provided, then create and populate a collection of `Item` objects with all data fetched from the database.

```python
class Item(object):
    ...

    def __init__(self, uid=None, name=None, description=None, completed=False):
        ...

    @classmethod
    def fetch(cls, uid=None):
        """
        Create one or a collection of items with data populated from the
        `item` table in the database.

        Args:
            uid (int): Optional. Unique identifier of an item

        Returns:
            Item or List[Item]: If the unique identifier of an item is
                provided, fetch and return that item from the `item`
                table in the database. Otherwise, fetch and return a
                collection of all items from the `item` table in the
                database.

        Raises:
            LookupError: Item not found
        """
        # Establish a connection to the database
        connection = sqlite3.Connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        try:
            if uid:
                # Get the row from the `item` table in the database
                # which matches the unique identifier. The `fetchone`
                # method returns `None` if there is no match.
                row = cursor.execute(
                    """
                    SELECT uid, name, description, completed
                    FROM item WHERE uid = ?
                    """,
                    (uid,)
                ).fetchone()

                if row:
                    # The item was found, so create an `Item` object
                    result = cls(
                        uid=row[0],
                        name=row[1],
                        description=row[2],
                        completed=True if row[3] else False
                    )
                else:
                    # The item was not found, raise an exception
                    raise LookupError('Item not found')

            else:
                # Get all of the rows from the `item` table in the
                # database
                rows = cursor.execute(
                    'SELECT uid, name, description, completed FROM item'
                )

                # For each row, create an `Item` object
                result = []
                for row in rows.fetchall():
                    item = cls(
                        uid=row[0],
                        name=row[1],
                        description=row[2],
                        completed=True if row[3] else False
                    )
                    result.append(item)

        except Exception:
            # If any error occurred, rollback the database connection
            # and re-raise the exception.
            connection.rollback()
            raise

        finally:
            # Close the database connection
            cursor.close()
            connection.close()

        return result

    ...
```

## Create a method to create an item

* Next, we should create a method for the `Item` class to create the item in the database.
* This method should be an instance method and take no arguments, as it should add a row in the database based on the attributes of the current object.
* As with the previous method, we need to manage the database connection.
* After inserting a new row in the database, we need to populate the `uid` attribute of the current object with the extracted auto-generated unique identifier.
* Any exceptions which occur during the operation is to cause a rollback on the database connection and the exception re-raised.

```python
class Item(object):
    ...

    def __init__(self, uid=None, name=None, description=None, completed=False):
        ...

    @classmethod
    def fetch(cls, uid=None):
        ...

    def create(self):
        """
        Create the item in the database.

        Returns:
            Item: Allow for method chaining of self

        Raises:
            Exception: Any errors encountered when inserting a new row
                to the database
        """
        # Establish a connection to the database
        connection = sqlite3.Connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        try:
            # Insert a new row to the database with the values from the
            # the current object and get the auto-generated unique
            # identifier to populate the `uid` attribute
            cursor.execute(
                """
                INSERT INTO item (name, description, completed)
                VALUES (?, ?, ?)
                """,
                (self.name, self.description, self.completed)
            )
            self.uid = cursor.lastrowid
            connection.commit()

        except Exception:
            # If any error occurred, rollback the database connection
            # and re-raise the exception.
            connection.rollback()
            raise

        finally:
            # Close the database connection
            cursor.close()
            connection.close()

        return self

    ...
```

## Create a method to update an item

* Next, we should create a method for the `Item` class to update the item in the database.
* This method should be an instance method which takes no arguments, as it should update the row in the database based on the attributes of the current object.
* As with the previous method, we need to manage the database connection.
* After updating the row in the database (based on the `uid` attribute`), we need to check if any row was actually updated.
* If no row was updated, we should raise a lookup error, as the item was not found.
* Any exceptions which occur during the operation is to cause a rollback on the database connection and the exception re-raised.

```python
class Item(object):
    ...

    def __init__(self, uid=None, name=None, description=None, completed=False):
        ...

    @classmethod
    def fetch(cls, uid=None):
        ...

    def create(self):
        ...

    def update(self):
        """
        Update the item in the database.

        Returns:
            Item: Allow for method chaining of self

        Raises:
            LookupError: Item not found
            Exception: Any errors encountered when inserting a new row
                to the database
        """
        # Establish a connection to the database
        connection = sqlite3.Connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        try:
            # Update the matching row in the database with the values
            # from the current object. If no row was updated, then the
            # item was not found, so raise an exception.
            cursor.execute(
                """
                UPDATE item SET name = ?, description = ?, completed = ?
                WHERE uid = ?
                """,
                (self.name, self.description, self.completed, self.uid)
            )
            if not cursor.rowcount:
                raise LookupError('Item not found')
            connection.commit()

        except Exception:
            # If any error occurred, rollback the database connection
            # and re-raise the exception.
            connection.rollback()
            raise

        finally:
            # Close the database connection
            cursor.close()
            connection.close()

        return self

    ...
```

## Create a method to delete an item

* Next, we should create a method for the `Item` class to delete the item from the database.
* This method should be an instance method which takes not arguments, as it should delete the row in the database based on the attributes of the current object.
* As with the previous method, we need to manage the database connection.
* After deleting the row in the database (based on the `uid` attribute`), we need to check if any row was actually deleted.
* If no row was deleted, we should raise a lookup error, as the item was not found.
* Any exceptions which occur during the operation is to cause a rollback on the database connection and the exception re-raised.
* The `uid` attribute needs to be cleared, as it has been removed from the database and is no longer valid.

```python
class Item(object):
    ...

    def __init__(self, uid=None, name=None, description=None, completed=False):
        ...

    @classmethod
    def fetch(cls, uid=None):
        ...

    def create(self):
        ...

    def update(self):
        ...

    def delete(self):
        """
        Delete the item from the database.

        Returns:
            Item: Allow for method chaining of self

        Raises:
            LookupError: Item not found
            Exception: Any errors encountered when inserting a new row
                to the database
        """
        # Establish a connection to the database
        connection = sqlite3.Connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        try:
            # Delete the matching row from the database. If no row was
            # deleted, then the item was not found, so raise an
            # exception.
            cursor.execute('DELETE FROM item WHERE uid = ?', (self.uid,))

            if not cursor.rowcount:
                raise LookupError('Item not found')
            connection.commit()

        except Exception:
            # If any error occurred, rollback the database connection
            # and re-raise the exception.
            connection.rollback()
            raise

        finally:
            # Close the database connection
            cursor.close()
            connection.close()

        # Clear the uid as it has been removed from the database
        self.uid = 0

        return self

    ...
```

## Update the fetch all items route

* For the route to fetch all items, we can greatly simplify it.
* All of the logic pertaining to directly interacting with the database can be removed.
* The response logic can directly serialize the data returned from the `Item.fetch_all` method, as that will return a collection of all `Item` objects populated from the database.

```python
@app.route('/items', methods=['GET'])
def fetch_all_items():
    """
    HTTP GET route to fetch all To-Do items from the database.

    Returns:
        Response: HTTP response object with a payload of a JSON encoded
            string of a collection of all the items retrieved from the
            database
    """
    # Create the HTTP response object using jsonpickle to serialize the
    # response data which is a list of all the items obtained by using
    # the `Item.fetch` method.
    return Response(
        response=encode(value=Item.fetch(), unpicklable=False),
        status=200,
        mimetype='application/json'
    )
```

## Update the fetch one item route

* For the route to fetch one item, we can greatly simplify it.
* All of the logic pertaining to directly interacting with the database can removed.
* We can use the `Item.fetch` method to get the item from the database.
* Since that method can raise exceptions, we need to account for them and create a an appropriate response.

```python
@app.route('/items/<int:uid>')
def fetch_one_item(uid):
    """
    HTTP GET route to fetch a single To-Do item from the database by its
    unique identifier.

    Args:
        uid (int): Unique identifier of the item

    Returns:
        Response: HTTP response object with a payload of a JSON encoded
            string of the item retrieved from the database. If the item
            is not found, a 404 response object is returned with a
            message to the user.
    """
    try:
        # Create the HTTP response object using jsonpickle to serialize
        # the response data which is an instance of `item` obtained by
        # using the `Item.fetch` method.
        response = Response(
            response=encode(value=Item.fetch(uid=uid), unpicklable=False),
            status=200,
            mimetype='application/json'
        )
    except Exception as error:
        # If any errors occurred, create the HTTP response object using
        # jsonpickle to serialize an error message for the user. If the
        # raised exception is a lookup error, then set the response
        # status code to 404.
        message = {'message': str(error)}
        response = Response(
            response=encode(value=message, unpicklable=False),
            status=404 if isinstance(error, LookupError) else 400,
            mimetype='application/json'
        )

    return response
```

## Update the create item route

* For the route to create an item, we can greatly simplify it.
* All of the logic pertaining to directly interacting with the database can be removed.
* After getting the deserialized JSON data from the HTTP request, we simply need to create an `Item` object, use the `from_dict` method to populate it, and use the `create` method to create it in the database.
* Since those methods can raise exceptions, we need to account for them and create an appropriate response.

```python
@app.route('/items', methods=['POST'])
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
        Response: HTTP response object with a payload of a JSON encoded
            string of the newly created item in the database. If any
            errors occurred during the operation, a response object is
            returned with the error message.
    """
    # Get the deserialized JSON data from the HTTP request
    data = request.json

    try:
        # Extract the required `name` attribute and optional
        # `description` and `completed` attributes and create a new
        # record in the database.
        item = Item().from_dict(data=data).create()

        # Create the HTTP response object using jsonpickle to serialize
        # the response data
        response = Response(
            response=encode(value=item, unpicklable=False),
            status=200,
            mimetype='application/json'
        )
    except Exception as error:
        # If any errors occurred, create the HTTP response object using
        # jsonpickle to serialize an error message for the user
        message = {'message': str(error)}
        response = Response(
            response=encode(value=message, unpicklable=False),
            status=400,
            mimetype='application/json'
        )

    return response
```

## Update the update item route

* For the route to update an item, we can greatly simplify it.
* All of the logic pertaining to directly interacting with the database can be removed.
* We can fetch the item from the database by using the `Item.fetch_one` method.
* After getting the deserialized JSON data from the HTTP request, we can populate the item with the updated data by using the `from_dict` method, and use the `update` method to update it in the database.
* Since those methods can raise exceptions, we need to account for them and create an appropriate response.

```python
@app.route('/items/<int:uid>', methods=['PUT'])
def update_item(uid):
    """
    HTTP PUT route to update an item by replacing its attributes with
    those supplied by the payload of the HTTP request.

    Args:
        uid (int): Unique identifier of the item

    JSON Payload:
        {
            "name": string,         <-- Required name of the item
            "description": string,  <-- Optional description of the item
            "completed": boolean    <-- Optional status of the item
        }

    Returns:
        Response: HTTP response object with a payload of a JSON encoded
            string of the updated item in the database. If any errors
            occurred during the operation, a response object is returned
            with the error message.
    """
    # Get the deserialized JSON data from the HTTP request
    data = request.json

    try:
        # Extract the required `name` attribute and optional
        # `description` and `completed` attributes and update the
        # record in the database.
        item = Item.fetch(uid=uid).from_dict(data=data).update()

        # Create the HTTP response object using jsonpickle to serialize
        # the response data
        response = Response(
            response=encode(value=item, unpicklable=False),
            status=200,
            mimetype='application/json'
        )
    except Exception as error:
        # If any errors occurred, create the HTTP response object using
        # jsonpickle to serialize an error message for the user
        message = {'message': str(error)}
        response = Response(
            response=encode(value=message, unpicklable=False),
            status=400,
            mimetype='application/json'
        )

    return response
```

## Update the partial update item route

* For the route to partially update an item, we can greatly simplify it.
* All of the logic pertaining to directly interacting with the database can be removed.
* We can fetch the item from the database by using the `Item.fetch_one` method.
* After getting the deserialized JSON data from the HTTP request, we can populate the item with the updated data by using the `from_dict` method, and use the `update` method to update it in the database.
* Since those methods can raise exceptions, we need to account for them and create an appropriate response.

```python
@app.route('/items/<int:uid>', methods=['PATCH'])
def partial_update_item(uid):
    """
    HTTP PATCH route to partially update an item with attributes
    supplied by the payload of the HTTP request.

    Args:
        uid (int): Unique identifier of the item

    Returns:
        Response: HTTP response object with a payload of a JSON encoded
            string of the updated item in the database. If any errors
            occurred during the operation, a response object is returned
            with the error message.
    """
    # Get the deserialized JSON data from the HTTP request
    data = request.json

    try:
        # Extract the required `name` attribute and optional
        # `description` and `completed` attributes and update the
        # record in the database.
        item = Item.fetch(uid=uid).from_dict(data=data).update()

        # Create the HTTP response object using jsonpickle to serialize
        # the response data
        response = Response(
            response=encode(value=item, unpicklable=False),
            status=200,
            mimetype='application/json'
        )
    except Exception as error:
        # If any errors occurred, create the HTTP response object using
        # jsonpickle to serialize an error message for the user
        message = {'message': str(error)}
        response = Response(
            response=encode(value=message, unpicklable=False),
            status=400,
            mimetype='application/json'
        )

    return response
```

## Update the delete item route

* For the route to delete an item, we can greatly simplify it.
* All of the logic pertaining to directly interacting with the database can be removed.
* We can fetch the item from the database by using the `Item.fetch_one` method.
* We can delete the item from the database by using the `delete` method.
* Since those methods can raise exceptions, we need to account for them and create an appropriate response.

```python
@app.route('/items/<int:uid>', methods=['DELETE'])
def delete_item(uid):
    """
    HTTP DELETE route to delete an item from the database.

    Args:
        uid (int): Unique identifier of the item

    Returns:
        Response: HTTP response object with no payload but a successful
            status code. If any errors occurred during the operation, a
            response object is returned with the error message.
    """
    try:
        # Delete the item from the database and create the HTTP response
        # object with no payload
        Item.fetch(uid=uid).delete()
        response = Response(status=200)
    except Exception as error:
        # If any errors occurred, create the HTTP response object using
        # jsonpickle to serialize an error message for the user
        message = {'message': str(error)}
        response = Response(
            response=encode(value=message, unpicklable=False),
            status=400,
            mimetype='application/json'
        )

    return response
```
