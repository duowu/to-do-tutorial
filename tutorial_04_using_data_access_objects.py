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
                    result = Item(
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
                    item = Item(
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
    # Create the HTTP response object using jsonpickle to serialize the
    # response data which is a list of all the items obtained by using
    # the `Item.fetch` method.
    return Response(
        response=encode(value=Item.fetch(), unpicklable=False),
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
