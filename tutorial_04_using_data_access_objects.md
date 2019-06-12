# Using data access objects

## Table of Contents

* [Introduction](#introduction)
* [Create a method to fetch all items or one item](#create-a-method-to-fetch-all-items-or-one-item)

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
```
