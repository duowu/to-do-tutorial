# Enhancing ORM session management

## Table of Contents

* [Introduction](#introduction)
* [Create fetch method for Item model](#create-fetch-method-for-item-model)
* [Create save method for Item model](#create-save-method-for-item-model)
* [Create delete method for Item model](#create-delete-method-for-item-model)
* [Update Item resource GET method](#update-item-resource-get-method)
* [Update Item resource POST method](#update-item-resource-post-method)
* [Update Item resource PUT method](#update-item-resource-put-method)
* [Update Item resource PATCH method](#update-item-resource-patch-method)
* [Update Item resource DELETE method](#update-item-resource-delete-method)

## Introduction

* Using SQLAlchemy as an ORM engine greatly simplified the code, as it took care of all of the database interactions.
* However, using the database mode `Item` did require us to use `db.session` when creating, updating, or deleting from the database.
* This is a slight step backwards from the `Item` data access object class we had previously.
* This requires us to constantly drag around the `db` object. While this is not much of an issue here, as we create more database models, split the code to multiple files, or create separate scripts which use the database models, this becomes more cumbersome.
* We can add the simple session operations back into the model class, and then other dependencies only need to use the model class.

## Create fetch method for Item model

* We can start by creating a class method for fetching one or all items.
* This logic is basically the same as the `get` method for the item resource class.
* Note that we can use `cls` instead of `Item`, since this is class method for `Item`.

```python
class Item(db.Model):
    ...

    def __getstate__(self):
        ...

    def from_dict(self, data):
        ...

    @classmethod
    def fetch(cls, uid=None):
        """
        Fetch one or a collection of items from the database.

        Args:
            uid (int): Optional. Unique identifier of an item

        Returns:
            Item or List[Item]: If `uid` is provided, fetch that item.
                Otherwise, fetch all items.

        Raises:
            LookupError: Item not found
        """
        # The unique identifier is provided, so fetch that one item
        if uid:
            # The `first` method for queries returns `None` if there is
            # nothing in the returned query
            item = cls.query.filter_by(uid=uid).first()
            if item is None:
                raise LookupError('Item not found')
            return item
        else:
            return cls.query.all()
```

## Create save method for Item model

* This time, we can actually combine the `create` and `update` methods from the old `Item` data access object class to a single `save` instance method.
* The logic is similar to that found in the `post`, `put`, and `patch` methods of the item resource class.
* We simply need to add the current object to the session for creating (`self.uid` is not populated).
* Then commit the session for creating or updating.

```python
class Item(db.Model):
    ...

    def __getstate__(self):
        ...

    def from_dict(self, data):
        ...

    @classmethod
    def fetch(cls, uid=None):
        ...

    def save(self):
        """
        Create or update the item in the database.

        If the item has a unique identifier, then update the item by
        committing the session. Otherwise, create the item by adding it
        to the session before committing it.

        Returns:
            Item: Allow for method chaining of self
        """
        if not self.uid:
            db.session.add(self)
        db.session.commit()
        return self
```

## Create delete method for Item model

* The logic for the method for deleting an item is also similar to that of the `delete` method of the item resource class.
* We simply need to mark the current object for deletion in the session and commit it.

```python
class Item(db.Model):
    ...

    def __getstate__(self):
        ...

    def from_dict(self, data):
        ...

    @classmethod
    def fetch(cls, uid=None):
        ...

    def save(self):
        ...

    def delete(self):
        """
        Delete the item from the database.

        Returns:
            Item: Allow for method chaining of self
        """
        db.session.delete(self)
        db.session.commit()
        return self
```

## Update Item resource GET method

* Now that we have CRUD methods built into the `Item` database model class, the item resource methods return to being very simple (just like before we switched to using ORM).
* The `get` method of the item resource class simply needs to call `Item.fetch`.

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
        return Item.fetch(uid=uid)

...
```

## Update Item resource POST method

* For the `post` method of the item resource class, we return to the simplicity of what it was just before we used ORM.
* Note that we use the `save` method instead of `create`.

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
        return Item().from_dict(data=request.json).save()

...
```

## Update Item resource PUT method

* For the `put` method of the item resource class, we also return to the simplicity of what it was just before we used ORM.
* Note that we use the `save` method instead of `create`.

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
        return Item.fetch(uid=uid).from_dict(data=request.json).save()

...
```

## Update Item resource PATCH method

* For the `patch` method of the item resource class, we also return to the simplicity of what it was just before we used ORM.
* Note that we use the `save` method instead of `create`.

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
        return Item.fetch(uid=uid).from_dict(data=request.json).save()

...
```

## Update Item resource DELETE method

* For the `delete` method of the item resource class, we also return to the simplicity of what it was just before we used ORM.

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
        # Fetch and delete the item from the database.
        Item.fetch(uid=uid).delete()
```
