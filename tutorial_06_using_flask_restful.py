import sqlite3
from flask import Flask, request, Response
from flask_restful import Api, Resource
from functools import wraps
from jsonpickle import encode

db_path = 'app.db'  # The path to the SQLite3 database file
app = Flask(__name__)  # The Flask application object
api = Api(app)


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


class ItemRoute(Resource):
    """

    """

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

    @create_response
    def delete(self, uid):
        """
        HTTP DELETE method to delete an item from the database.

        Args:
            uid (int): Unique identifier of the item
        """
        # Fetch and delete the item from the database
        Item.fetch(uid=uid).delete()


api.add_resource(ItemRoute, '/items', '/items/<int:uid>')


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
