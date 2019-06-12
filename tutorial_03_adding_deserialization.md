# Adding deserialization

## Table of Contents

* [Create a method for item deserialization](#create-a-method-for-item-deserialization)
* [Update the create item route](#update-the-create-item-route)
* [Update the update item route](#update-the-update-item-route)
* [Update the partial update item route](#update-the-partial-update-item-route)

## Create a method for item deserialization

* Now that we have a class to represent an item, we can expand on it to make the code a bit cleaner by reducing some repeated logic.
* Notice that some of the routes extract JSON data from the payload of a request and populates the attributes of an `Item` object.
* We can create an instance method for the `Item` class which takes in a dictionary and populates the attributes of the current object with it.

```python
class Item(object):
    ...

    def __init__(self, uid=None, name=None, description=None, completed=False):
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
```

## Update the create item route

* For the route to create an item, we can replace the logic which extracts data from the payload of the request with a call to the new `from_dict` method.


```python
@app.route('/items', methods=['POST'])
def create_item():
    ...
    # Get the deserialized JSON data from the HTTP request
    data = request.json

    # Extract the required `name` attribute and optional `description`
    # and `completed` attributes
    item = Item().from_dict(data=data)

    # Establish a connection to the database
    connection = sqlite3.Connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    ...
```

## Update the update item route

* For the route to update an item, we can also replace the logic which extracts data from the payload with a call to the `from_dict` method.

```python
@app.route('/items/<int:uid>', methods=['PUT'])
def update_item(uid):
    ...
    # Get the deserialized JSON data from the HTTP request
    data = request.json

    # Extract the required `name` attribute and optional `description`
    # and `completed` attributes
    item = Item(uid=uid).from_dict(data=data)

    # Establish a connection to the database
    connection = sqlite3.Connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    ...
```

## Update the partial update item route

* For the route to partially update an item, we can also replace the logic which extracts data from the payload with a call to the `from_dict` method.

```python
@app.route('/items/<int:uid>', methods=['PATCH'])
def partial_update_item(uid):
    ...

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
        item.from_dict(data=data)

        try:
            ...
        except Exception as error:
            ...
    ...
```
