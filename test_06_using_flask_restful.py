import sqlite3
import unittest
from deepdiff import DeepDiff
import tutorial_06_using_flask_restful as todo_app


class TestToDoApp(unittest.TestCase):
    """
    Unit tests for the To-Do API.

    Before each unit test, keep track of the existing rows in the
    database. After each unit test, any newly added rows are deleted.

    Class Attributes:
        app (flask.testing.FlaskClient): Flask test client to invoke
            HTTP methods for the To-Do API
        existing_uids (set): Collection of unique identifiers of the
            existing rows in the `item` table in the database
    """

    app = None
    existing_uids = set()

    @classmethod
    def setUpClass(cls):
        """
        Before any unit tests, create the Flask test client and make
        sure the tables are created in the database.
        """
        cls.app = todo_app.app.test_client()
        todo_app.create_tables()

    def setUp(self):
        """
        Before each unit test, keep track of the existing rows in the
        `item` table in the database.
        """
        # Establish a connection to the database
        connection = sqlite3.Connection = sqlite3.connect(todo_app.db_path)
        cursor = connection.cursor()

        # Get all the current records from the `item` table in the
        # database and store them to the `existing_uids` set
        rows = cursor.execute('SELECT uid FROM item').fetchall()
        self.existing_uids.update([row[0] for row in rows])

        # Close the database connection
        cursor.close()
        connection.close()

    def tearDown(self):
        """
        After each unit test, delete any newly created rows in the
        `item` table in the database.
        """
        # Establish a connection to the database
        connection = sqlite3.Connection = sqlite3.connect(todo_app.db_path)
        cursor = connection.cursor()

        # Get all the current records from the `item` table in the
        # database. If any of them are not in the `existing_uids` set,
        # then delete them from the database.
        rows = cursor.execute('SELECT uid FROM item').fetchall()
        for row in rows:
            if row[0] not in self.existing_uids:
                cursor.execute('DELETE FROM item WHERE uid = ?', (row[0],))

        connection.commit()

        # Close the database connection
        cursor.close()
        connection.close()

        self.existing_uids.clear()

    def test_items_crud_actions(self):
        """
        Unit test for CRUD actions for the `item` resource.
            - Create the item
            - Fetch the item by its unique identifier
            - Fetch all items and make sure the item is in the returned
              list
            - Update the item
            - Fetch the item by its unique identifier to check the update
            - Partially update the item
            - Fetch the item by its unique identifier to check the update
            - Delete the item
            - Fetch the item by its unique identifier to check the update
        """
        # Create the item
        item_data = {
            'name': 'Create API',
            'description': 'Create a To-Do API'
        }
        response = self.app.post('/items', json=item_data)
        expected = {
            'name': 'Create API',
            'description': 'Create a To-Do API',
            'completed': False
        }
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        item_uid = data.pop('uid')
        self.assertTrue(item_uid)
        self.assertFalse(DeepDiff(data, expected, ignore_order=True))

        # Fetch the item by its unique identifier
        response = self.app.get(f'/items/{item_uid}')
        expected = {
            'uid': item_uid,
            'name': 'Create API',
            'description': 'Create a To-Do API',
            'completed': False
        }
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertFalse(DeepDiff(data, expected, ignore_order=True))

        # Fetch all items - make sure the item is in the returned list
        response = self.app.get('/items')
        expected = {
            'uid': item_uid,
            'name': 'Create API',
            'description': 'Create a To-Do API',
            'completed': False
        }
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, list)
        found_item = False
        for item in data:
            self.assertIsInstance(item, dict)
            if item.get('uid') == item_uid:
                self.assertFalse(DeepDiff(item, expected, ignore_order=True))
                found_item = True
        self.assertTrue(found_item)

        # Update the item
        update_data = {
            'name': 'Update API',
            'description': 'Update the To-Do API'
        }
        response = self.app.put(f'/items/{item_uid}', json=update_data)
        expected = {
            'uid': item_uid,
            'name': 'Update API',
            'description': 'Update the To-Do API',
            'completed': False
        }
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertFalse(DeepDiff(data, expected, ignore_order=True))

        # Fetch the item by its unique identifier to check the update
        response = self.app.get(f'/items/{item_uid}')
        expected = {
            'uid': item_uid,
            'name': 'Update API',
            'description': 'Update the To-Do API',
            'completed': False
        }
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertFalse(DeepDiff(data, expected, ignore_order=True))

        # Partially update the item
        update_data = {'completed': True}
        response = self.app.patch(f'/items/{item_uid}', json=update_data)
        expected = {
            'uid': item_uid,
            'name': 'Update API',
            'description': 'Update the To-Do API',
            'completed': True
        }
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertFalse(DeepDiff(data, expected, ignore_order=True))

        # Fetch the item by its unique identifier to check the update
        response = self.app.get(f'/items/{item_uid}')
        expected = {
            'uid': item_uid,
            'name': 'Update API',
            'description': 'Update the To-Do API',
            'completed': True
        }
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertFalse(DeepDiff(data, expected, ignore_order=True))

        # Delete the item
        response = self.app.delete(f'/items/{item_uid}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'')

        # Fetch the item by its unique identifier to check the delete
        response = self.app.get(f'/items/{item_uid}')
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
