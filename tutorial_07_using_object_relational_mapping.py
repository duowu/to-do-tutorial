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
        if data is not None:
            data = encode(value=data, unpicklable=False)
        return Response(
            response=data,
            status=status_code,
            mimetype='application/json'
        )

    return wrapper


class ItemResource(Resource):
    """
    This resource class provides create, read, update, and delete (CRUD)
    actions for the item resource using HTTP methods.
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


api.add_resource(ItemResource, '/items', '/items/<int:uid>')

if __name__ == '__main__':
    # Make sure all the tables are created in the database before
    # running the Flask application
    db.create_all()
    app.run(port=8002, debug=True)
