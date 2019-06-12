# Using basic classes

## Table of Contents

* [Create a class to represent an item](#create-a-class-to-represent-an-item)
* [Update the fetch all items route](#update-the-fetch-all-items-route)
* [Update the fetch one item route](#update-the-fetch-one-item-route)
* [Update the create item route](#update-the-create-item-route)
* [Update the update item route](#update-the-update-item-route)
* [Update the partial update item route](#update-the-partial-update-item-route)
* [Update the delete item route](#update-the-delete-item-route)

## Create a class to represent an item

* Now that we have an application created for the To-Do API, lets start adding abstraction to create cleaner code and also allow for code reuse in the future.
* Notice that we have been using dictionaries to represent an item. Since an all items have the same format, we can start by creating a class to represent that information. This will give us a more structured way to represent the data.
* After we create this class, we should then refactor all of the routes to use the new class. While we will benefit from this, as this cleans the code a bit, we won't see a huge change. However, this paves the way for more abstraction and more benefits later.

```python
class Item(object):
    """
    This class represents a To-Do item.

    Attributes:
        uid (int): Unique identifier for the item
        name (str): Name of the item
        description (str): Description of the item
        completed (bool): Whether or not the item is completed. The
            default value is `False`.
    """

    def __init__(self, uid=None, name=None, description=None, completed=False):
        """
        Initialize an `Item` object.

        Args:
            uid (int): Optional. Unique identifier for the item
            name (str): Optional. Name of the item
            description (str): Optional. Description of the item
            completed (bool): Optional. Whether or not the item is
                completed. The default value is `False`.
        """
        self.uid = uid
        self.name = name
        self.description = description
        self.completed = completed
```

## Update the fetch all items route

* For the route to fetch all items, not much needs to be changed.
* We simply need to create an `Item` object instead of a dictionary for each row returned from the database.

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
    items = []  # Contains all of the items to return

    # Establish a connection to the database
    connection = sqlite3.Connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Get all of the rows from the `item` table in the database
    rows = cursor.execute('SELECT uid, name, description, completed FROM item')

    # For each row, create an `Item` object
    for row in rows.fetchall():
        item = Item(
            uid=row[0],
            name=row[1],
            description=row[2],
            completed=True if row[3] else False
        )
        items.append(item)

    # Close the database connection
    cursor.close()
    connection.close()

    # Create the HTTP response object using jsonpickle to serialize the
    # response data
    return Response(
        response=encode(value=items, unpicklable=False),
        status=200,
        mimetype='application/json'
    )
```

## Update the fetch one item route

* For the route to fetch one item, not much needs to be changed as well.
* As with the previous route, we simply need to create an `Item` object instead of a dictionary when the item is found in the database.

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
    # Establish a connection to the database
    connection = sqlite3.Connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Get the row from the `item` table in the database which matches
    # the unique identifier. The `fetchone` method returns `None` if
    # there is no match.
    row = cursor.execute(
        'SELECT uid, name, description, completed FROM item WHERE uid = ?',
        (uid,)
    ).fetchone()

    if row:
        # The item was found, so create an `Item` object
        item = Item(
            uid=row[0],
            name=row[1],
            description=row[2],
            completed=True if row[3] else False
        )

        # Create the HTTP response object using jsonpickle to serialize
        # the response data
        response = Response(
            response=encode(value=item, unpicklable=False),
            status=200,
            mimetype='application/json'
        )
    else:
        # The item was not found, so create the HTTP response object
        # using jsonpickle to serialize an error message for the user
        message = {'message': 'Item not found'}
        response = Response(
            response=encode(value=message, unpicklable=False),
            status=404,
            mimetype='application/json'
        )

    # Close the database connection
    cursor.close()
    connection.close()

    return response
```

## Update the create item route

* For the route to create an item, we can create an `Item` object instead of a dictionary when extracting data from payload of the request.
* Note that in the `except` block, we simply need to create a new `Item` instance, as it already has the default values.
* We need to update the cursor execute statement to use the values from the `Item` object instead of individual variables.
* After the database insert action, we can directly update the `uid` of the `Item` object.
* We also no longer need to create a dictionary to represent the item, as we already have an up-to-date `Item` object.

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

    # Extract the required `name` attribute and optional `description`
    # and `completed` attributes
    try:
        item = Item(
            name=data['name'],
            description=data.get('description'),
            completed=data.get('completed', False)
        )
    except (AttributeError, KeyError, TypeError):
        item = Item()

    # Establish a connection to the database
    connection = sqlite3.Connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        # Insert a new row to the database with the values supplied by
        # the user and get the auto-generated unique identifier
        cursor.execute(
            'INSERT INTO item (name, description, completed) VALUES (?, ?, ?)',
            (item.name, item.description, item.completed)
        )
        item.uid = cursor.lastrowid
        connection.commit()

        # Create the HTTP response object using jsonpickle to serialize
        # the response data
        response = Response(
            response=encode(value=item, unpicklable=False),
            status=200,
            mimetype='application/json'
        )
    except Exception as error:
        # If any errors occurred, rollback the database connection and
        # create the HTTP response object using jsonpickle to serialize
        # an error message for the user
        connection.rollback()
        message = {'message': str(error)}
        response = Response(
            response=encode(value=message, unpicklable=False),
            status=400,
            mimetype='application/json'
        )

    # Close the database connection
    cursor.close()
    connection.close()

    return response
```

## Update the update item route

* For the route to update an item, the changes are not much different than the changes for the route to create an item.
* As with the create item route, we can create an `Item` object instead of a dictionary when extracting data from the payload of the request.
* Note that since we populate the `uid` attribute since we have it from the request.
* Also, as with the create item route, we need to update the cursor execute statement to use the values form the `Item` object.
* We also no longer need to create a dictionary to represent the item.

```python
@app.route('/items/<int:uid>', methods=['PUT'])
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
        Response: HTTP response object with a payload of a JSON encoded
            string of the updated item in the database. If any errors
            occurred during the operation, a response object is returned
            with the error message.
    """
    # Get the deserialized JSON data from the HTTP request
    data = request.json

    # Extract the required `name` attribute and optional `description`
    # and `completed` attributes
    try:
        item = Item(
            uid=uid,
            name=data['name'],
            description=data.get('description'),
            completed=data.get('completed', False)
        )
    except (AttributeError, KeyError, TypeError):
        item = Item(uid=uid)

    # Establish a connection to the database
    connection = sqlite3.Connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        # Update the matching row in the database with the values
        # supplied by the user. If no row was updated, then the item was
        # not found, so raise an exception.
        cursor.execute(
            """
            UPDATE item SET name = ?, description = ?, completed = ?
            WHERE uid = ?
            """,
            (item.name, item.description, item.completed, item.uid)
        )
        if not cursor.rowcount:
            raise LookupError('Item not found')
        connection.commit()

        # Create the HTTP response object using jsonpickle to serialize
        # the response data
        response = Response(
            response=encode(value=item, unpicklable=False),
            status=200,
            mimetype='application/json'
        )
    except Exception as error:
        # If any errors occurred, rollback the database connection and
        # create the HTTP response object using jsonpickle to serialize
        # an error message for the user. If the raise exception is a
        # lookup error, then set the response status code to 404
        connection.rollback()
        message = {'message': str(error)}
        response = Response(
            response=encode(value=message, unpicklable=False),
            status=404 if isinstance(error, LookupError) else 400,
            mimetype='application/json'
        )

    # Close the database connection
    cursor.close()
    connection.close()

    return response
```

## Update the partial update item route

* For the route to partially update an item, similar changes are needed.
* However, instead of immediately extracting the data from the payload of the request, we will pull the data from the database first.
* We create an `Item` object instead of a dictionary when pulling data from the database.
* Now we can extract the data from the payload of the request. Since not every attribute is required, we only replace the attributes of the `Item` object if needed.
* Also, as with the update item route, we need to update the cursor execute statement to use the values form the `Item` object.
* We also no longer need to create a dictionary to represent the item.

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

    # Establish a connection to the database
    connection = sqlite3.Connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Get the row from the `item` table in the database which matches
    # the unique identifier. The `fetchone` method returns `None` if
    # there is no match.
    row = cursor.execute(
        'SELECT uid, name, description, completed FROM item WHERE uid = ?',
        (uid,)
    ).fetchone()

    if row:
        # The item was found, so create a `Item` object
        item = Item(
            uid=row[0],
            name=row[1],
            description=row[2],
            completed=True if row[3] else False
        )

        # Extract the optional `name`, `description`, and `completed`
        # attributes
        try:
            if 'name' in data:
                item.name = data['name']
            if 'description' in data:
                item.description = data['description']
            if 'completed' in data:
                item.completed = data['completed']
        except TypeError:
            pass

        try:
            # Update the matching row in the database with the updated
            # values
            cursor.execute(
                """
                UPDATE item SET name = ?, description = ?, completed = ?
                WHERE uid = ?
                """,
                (item.name, item.description, item.completed, item.uid)
            )
            connection.commit()

            # Create the HTTP response object using jsonpickle to serialize
            # the response data
            response = Response(
                response=encode(value=item, unpicklable=False),
                status=200,
                mimetype='application/json'
            )
        except Exception as error:
            # If any errors occurred, rollback the database connection and
            # create the HTTP response object using jsonpickle to serialize
            # an error message for the user. If the raise exception is a
            # lookup error, then set the response status code to 404
            connection.rollback()
            message = {'message': str(error)}
            response = Response(
                response=encode(value=message, unpicklable=False),
                status=400,
                mimetype='application/json'
            )
    else:
        # The item was not found, so create the HTTP response object
        # using jsonpickle to serialize an error message for the user
        message = {'message': 'Item not found'}
        response = Response(
            response=encode(value=message, unpicklable=False),
            status=404,
            mimetype='application/json'
        )

    # Close the database connection
    cursor.close()
    connection.close()

    return response
```

## Update the delete item route

* For the route to delete an item, there are no changes, since the route takes the unique identifier of an item directly from the route.
