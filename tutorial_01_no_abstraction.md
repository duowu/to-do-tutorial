
# Creating a simple To-Do API with no abstraction

## Table of Contents

* [Create a simple flask application](#create-a-simple-flask-application)
* [Set up the database](#set-up-the-database)
* [Create a route to fetch all items](#create-a-route-to-fetch-all-items)
* [Create a route to create an item](#create-a-route-to-create-an-item)
* [Create a route to delete an item](#create-a-route-to-delete-an-item)
* [Create a route to fetch a single item](#create-a-route-to-fetch-a-single-item)
* [Create a route to update an item](#create-a-route-to-update-an-item)
* [Create a route to partially update an item](#create-a-route-to-partially-update-an-item)

## Create a simple flask application

* Start by importing the `Flask` class from the `flask` module and creating a new instance which we will call `app`. This will serve as our flask application.
* Let's also add a simple route to test the application.
* And finally, we will add a statement to start the flask application on a specific port in debug mode when the file is run.

```python
from flask import Flask

app = Flask(__name__)  # The Flask application object


@app.route('/hello_world')
def hello_world():
    """
    HTTP GET route which simply returns "Hello, World!"

    Returns:
        str: "Hello, World!"
    """
    return 'Hello, World!'


if __name__ == '__main__':
    app.run(port=8002, debug=True)
```

* If we run the python file, we should have a simple web application with a single route which can be accessed using the HTTP GET method.

```bash
$ curl -s http://127.0.0.1:8002/hello_world

Hello, World!
```

## Set up the database

* We'll use a simple SQLite3 database to store data for the application. SQLite3 support is built into python, so we can simply import the corresponding module.
* Because we will be connecting to the database in multiple places in the file, we should create a string which contains the path to the database file.
* And finally, let's create a function to create any tables used in the application before the application start. We will have to connect to the database before executing the SQL statement and make sure to close the connection afterwards. Note the try-except block which will rollback if there are any errors, and we can ignore any errors where the table already exists.

```python
import sqlite3
from flask import Flask

db_path = 'app.db'  # The path to the SQLite3 database file
app = Flask(__name__)


@app.route('/hello_world')
def hello_world():
    ...


def create_tables():
    """
    Create any table needed for the application.
    """
    # Establish a connection to the database
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        # Create the `item` table in the database
        cursor.execute(
            """
            CREATE TABLE item
            (
                uid INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                completed BOOLEAN,
                PRIMARY KEY (uid),
                CHECK (completed IN (0, 1))
            )
            """
        )
        connection.commit()

    except sqlite3.OperationalError as error:
        # If any errors occurred, rollback the database connection. If
        # the error is because the table already exists, ignore it.
        # Otherwise, print the error, close the database connection, and
        # re-raise the exception.
        connection.rollback()
        if 'already exists' not in str(error):
            print(f'error creating `item` table - {str(error)}')
            cursor.close()
            connection.close()
            raise

    # Close the database connection
    cursor.close()
    connection.close()


if __name__ == '__main__':
    # Make sure all the tables are created in the database before
    # running the Flask application
    create_tables()
    app.run(port=8002, debug=True)
```

## Create a route to fetch all items

* With the database setup, we can now create a route to fetch all of the to-do items from the database using the HTTP GET method.
* As with the `create_tables` function from earlier, we need to establish a connection to the database before executing any SQL statement and make sure to close the connection afterwards.
* A simple `SELECT` statement will get us all of the records from the database, which we only then need to create a dictionary for each record returned.
* Unlike the simple `hello_world` route from earlier, we will need to create a more complex response with serialized data.
* After importing the `Response` class from the `flask` module, this route is to return an instance of a `Response` object.
* We can use the `encode` function from the `jsonpickle` module to help with the serialization to a return a JSON encoded string in the response payload.

```python
import sqlite3
from flask import Flask, Response
from jsonpickle import encode

db_path = 'app.db'
app = Flask(__name__)


@app.route('/hello_world')
def hello_world():
    ...


@app.route('/items', methods=['GET'])
def fetch_all_items():
    """
    HTTP GET route to fetch all To-Do items from the database.

    Returns:
        Response: HTTP response object with a payload of a JSON encoded
            string of a collection of all the items from the database
    """
    items = []  # Contains all of the items to return

    # Establish a connection to the database
    connection = sqlite3.Connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Get all of the rows from the `item` table in the database
    rows = cursor.execute('SELECT uid, name, description, completed FROM item')

    # For each row, create a dictionary which represents the item
    for row in rows.fetchall():
        item = {
            'uid': row[0],
            'name': row[1],
            'description': row[2],
            'completed': True if row[3] else False
        }
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


def create_tables():
    ...


if __name__ == '__main__':
    create_tables()
    app.run(port=8002, debug=True)

```

* We now have a route to fetch all items from the database.

```bash
$ curl -s http://127.0.0.1:8002/items

[]
```

## Create a route to create an item

* Now that we have a way to fetch all of the to-do items from the database, let's build a route to add a to-do item to the database using the HTTP POST method.
* We will expect the user of the API to submit a JSON encoded string as part of the payload of the request. This data can be retrieved from the request by using the `request` object from the `flask` module.
* `request.json` will give us the JSON encoded payload already deserialized into a dictionary, which we can then extract the required `name` and optional `description` and `completed` properties.
* As usual, we need to mind the database connection. This time we are catching any raised exception and returning back to the user a response with the error message.
* After a simple `INSERT` statement, we can retrieve the unique identifier auto-generated by the database to pack into a dictionary to be returned to the user.
* Again, we will use the `encode` function to convert our data for the response into a JSON encoded string.

```python
import sqlite3
from flask import Flask, request, Response
from jsonpickle import encode

db_path = 'app.db'
app = Flask(__name__)


@app.route('/hello_world')
def hello_world():
    ...


@app.route('/items', methods=['GET'])
def fetch_all_items():
    ...


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
        name = data['name']
        description = data.get('description')
        completed = data.get('completed', False)
    except (AttributeError, KeyError, TypeError):
        name = None
        description = None
        completed = False

    # Establish a connection to the database
    connection = sqlite3.Connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        # Insert a new row to the database with the values supplied by
        # the user and get the auto-generated unique identifier
        cursor.execute(
            'INSERT INTO item (name, description, completed) VALUES (?, ?, ?)',
            (name, description, completed)
        )
        uid = cursor.lastrowid
        connection.commit()

        # Create a dictionary which represents the newly created item
        item = {
            'uid': uid,
            'name': name,
            'description': description,
            'completed': completed
        }

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


def create_tables():
    ...


if __name__ == '__main__':
    ...
```

* We now have a route to add an item to the database.

```bash
$ curl -X POST -s http://127.0.0.1:8002/items
      -H 'Content-Type: application/json'
      -d '{"name": "Create API", "description": "Create a To-Do API"}'

{
    "uid": 1,
    "name": "Create API",
    "description": "Create a To-Do API",
    "completed": false
}
```

```bash
$ curl -X POST -s http://127.0.0.1:8002/items
      -H 'Content-Type: application/json'
      -d '{"name": "Document API", "description": "Document the API"}'

{
    "uid": 2,
    "name": "Document API",
    "description": "Document the API",
    "completed": false
}
```

* The GET route which we created earlier should now return all the created items.

```bash
$ curl -s http://127.0.0.1:8002/items

[
    {
        "uid": 1,
        "name": "Create API",
        "description": "Create a To-Do API",
        "completed": false
    },
    {
        "uid": 2,
        "name": "Document API",
        "description": "Document the API",
        "completed": false
    }
]
```

## Create a route to delete an item

* Now that we have a way to create an item in the database, we should build a route to delete an item from the database using the HTTP DELETE method.
* As part of the route, the user should supply the unique identifier of the item to delete.
* As with the HTTP POST method, we need to mind the database connection and catch any raised exception to return back to the user.
* After a simple `DELETE` statement, we should check if anything was actually removed from the database. If it isn't we should return not found error back to the user. Otherwise, we simply return a response with no content but with a success status code.

```python
import sqlite3
from flask import Flask, request, Response
from jsonpickle import encode

db_path = 'app.db'
app = Flask(__name__)


@app.route('/hello_world')
def hello_world():
    ...


@app.route('/items', methods=['GET'])
def fetch_all_items():
    ...


@app.route('/items', methods=['POST'])
def create_item():
    ...


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
    # Establish a connection to the database
    connection = sqlite3.Connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        # Delete the matching row from the database. If no row was
        # deleted, then the item was not found, so raise an exception.
        cursor.execute('DELETE FROM item WHERE uid = ?', (uid,))

        if not cursor.rowcount:
            raise LookupError('item not found')
        connection.commit()

        # Create the HTTP response object with no payload
        response = Response(status=200)

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


def create_tables():
    ...


if __name__ == '__main__':
    ...
```

* Now we have a route to remove an item from the database.

```bash
$ curl -X DELETE -s http://127.0.0.1:8002/items/2


```

## Create a route to fetch a single item

* While we have a route to fetch all items from the database, we should also create a route which allows the user to fetch a single item from the database by the unique identifier using the HTTP GET method.
* As with the DELETE route, the user should supply the unique identifier as part of the route.
* As usual, we need to mind the database connection and after a SELECT statement return the matching item back to the user.
* If the unique identifier cannot be found, we should return an error back to the user.

```python
import sqlite3
from flask import Flask, request, Response
from jsonpickle import encode

db_path = 'app.db'
app = Flask(__name__)


@app.route('/hello_world')
def hello_world():
    ...


@app.route('/items', methods=['GET'])
def fetch_all_items():
    ...


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
        # The item was found, so create a dictionary which represents
        # the item
        item = {
            'uid': row[0],
            'name': row[1],
            'description': row[2],
            'completed': True if row[3] else False
        }

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
        message = {'message': 'item not found'}
        response = Response(
            response=encode(value=message, unpicklable=False),
            status=404,
            mimetype='application/json'
        )

    # Close the database connection
    cursor.close()
    connection.close()

    return response


@app.route('/items', methods=['POST'])
def create_item():
    ...


@app.route('/items/<int:uid>', methods=['DELETE'])
def delete_item(uid):
    ...


def create_tables():
    ...


if __name__ == '__main__':
    ...
```

* We now have a route to fetch a single item from the database by its unique identifier.

```bash
$ curl -s http://127.0.0.1:8002/items/1

{
    "uid": 1,
    "name": "Create API",
    "description": "Create a To-Do API",
    "completed": false
}
```

## Create a route to update an item

* After creating items, the user will need to be able to update the item. Let's create a route which will allow an item to be updated by its unique identifier using the HTTP PUT method.
* As with the DELETE route, the user should supply the unique identifier as part of the route.
* As with the POST route, we will expect the user to submit a JSON encoded string as part of the payload of the request.
* We can then extract the required `name` and optional `description` and `completed` properties from the data supplied by the user.
* As usual, we need to mind the database connection and after an UPDATE statement, return the updated item back to the user.
* If the unique identifier cannot be found, we should return an error back to the user.

```python
import sqlite3
from flask import Flask, request, Response
from jsonpickle import encode

db_path = 'app.db'
app = Flask(__name__)


@app.route('/hello_world')
def hello_world():
    ...


@app.route('/items', methods=['GET'])
def fetch_all_items():
    ...


@app.route('/items/<int:uid>')
def fetch_one_item(uid):
    ...


@app.route('/items', methods=['POST'])
def create_item():
    ...


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
        name = data['name']
        description = data.get('description')
        completed = data.get('completed', False)
    except (AttributeError, KeyError, TypeError):
        name = None
        description = None
        completed = False

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
            (name, description, completed, uid)
        )
        if not cursor.rowcount:
            raise LookupError('item not found')
        connection.commit()

        # Create a dictionary which represents the updated item
        item = {
            'uid': uid,
            'name': name,
            'description': description,
            'completed': completed
        }

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


@app.route('/items/<int:uid>', methods=['DELETE'])
def delete_item(uid):
    ...


def create_tables():
    ...


if __name__ == '__main__':
    ...
```

* We now have a route to update an item in the database.

```bash
$ curl -X PUT -s http://127.0.0.1:8002/items/2
      -H 'Content-Type: application/json'
      -d '{"name": "Document API", "description": "A new description"}'

{
    "uid": 2,
    "name": "Document API",
    "description": "A new description",
    "completed": false
}
```

## Create a route to partially update an item

* The user can update an item, but the POST route which we created requires the user to specify all of the desired attributes. It really replaces the entire item with data supplied from the user.
* Let's create a route which allows the user to only partially update a item in the database by its unique identifier using the HTTP PATCH method.
* As with the PUT route, the user should supply the unique identifier as part  of the route.
* As with the PUT route, we expect the user to submit a JSON encoded string as part of the payload of the request. However, this time, all of the properties are optional and only those specified will be updated.
* As usual, we need to mind the database connection and after an UPDATE statement, return the updated item back to the user.
* If the unique identifier cannot be found, we should return an error back to the user.

```python
import sqlite3
from flask import Flask, request, Response
from jsonpickle import encode

db_path = 'app.db'
app = Flask(__name__)


@app.route('/hello_world')
def hello_world():
    ...


@app.route('/items', methods=['GET'])
def fetch_all_items():
    ...


@app.route('/items/<int:uid>')
def fetch_one_item(uid):
    ...


@app.route('/items', methods=['POST'])
def create_item():
    ...


@app.route('/items/<int:uid>', methods=['PUT'])
def update_item(uid):
    ...


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

    # Extract the optional `name`, `description`, and `completed`
    # attributes
    try:
        name = data.get('name')
        description = data.get('description')
        completed = data.get('completed')
    except (AttributeError, TypeError):
        name = None
        description = None
        completed = None

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
        # The item was found, so create a dictionary which represents
        # the item
        item = {
            'uid': row[0],
            'name': row[1],
            'description': row[2],
            'completed': True if row[3] else False
        }

        # If the `name`, `description`, or `completed` attributes are
        # `None`, then it was not supplied by the user, so the current
        # values from the database should be used.
        if name is None:
            name = item['name']
        if description is None:
            description = item['description']
        if completed is None:
            completed = item['completed']

        try:
            # Update the matching row in the database with the updated
            # values
            cursor.execute(
                """
                UPDATE item SET name = ?, description = ?, completed = ?
                WHERE uid = ?
                """,
                (name, description, completed, uid)
            )
            connection.commit()

            # Create a dictionary which represents the updated item
            item = {
                'uid': uid,
                'name': name,
                'description': description,
                'completed': completed
            }

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
        message = {'message': 'item not found'}
        response = Response(
            response=encode(value=message, unpicklable=False),
            status=404,
            mimetype='application/json'
        )

    # Close the database connection
    cursor.close()
    connection.close()

    return response


@app.route('/items/<int:uid>', methods=['DELETE'])
def delete_item(uid):
    ...


def create_tables():
    ...


if __name__ == '__main__':
    ...
```

* We now have a route to partially update an item in the database.

```bash
$ curl -X PATCH -s http://127.0.0.1:8002/items/2
      -H 'Content-Type: application/json'
      -d '{"completed": true}'

{
    "uid": 2,
    "name": "Document API",
    "description": "A new description",
    "completed": true
}
```
