import sqlite3
from flask import Flask, request, Response
from jsonpickle import encode

db_path = 'app.db'  # The path to the SQLite3 database file
app = Flask(__name__)  # The Flask application object


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


@app.route('/hello_world')
def hello_world():
    """
    HTTP GET route which simply returns "Hello, World!"

    Returns:
        str: "Hello, World!"
    """
    return 'Hello, World!'


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
            raise LookupError('Item not found')
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
