import unittest
from app import app, db, Todo
import json
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

class TodoTests(unittest.TestCase):
    def setUp(self):
        """Set up test client and create new database for testing"""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_route(self):
        """Test the main page loads correctly"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Self List', response.data)

    def test_add_todo(self):
        """Test adding a new todo item"""
        response = self.client.post('/add', data={'title': 'Test Todo'})
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        with app.app_context():
            todo = db.session.execute(db.select(Todo).filter_by(title='Test Todo')).scalar_one()
            self.assertIsNotNone(todo)
            self.assertEqual(todo.title, 'Test Todo')
            self.assertFalse(todo.completed)

    def test_add_empty_todo(self):
        """Test adding a todo with empty title"""
        response = self.client.post('/add', data={'title': ''})
        self.assertEqual(response.status_code, 302)
        
        with app.app_context():
            todos = db.session.execute(db.select(Todo)).scalars().all()
            self.assertEqual(len(todos), 0)

    def test_add_long_title_todo(self):
        """Test adding a todo with a title exceeding max length"""
        long_title = 'x' * 201  # More than 200 characters
        response = self.client.post('/add', data={'title': long_title})
        self.assertEqual(response.status_code, 302)
        
        with app.app_context():
            todos = db.session.execute(db.select(Todo)).scalars().all()
            self.assertEqual(len(todos), 0)

    def test_delete_todo(self):
        """Test deleting a todo item"""
        with app.app_context():
            todo = Todo(title='Test Todo')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = self.client.get(f'/delete/{todo_id}')
        self.assertEqual(response.status_code, 302)

        with app.app_context():
            todo = db.session.get(Todo, todo_id)
            self.assertIsNone(todo)

    def test_toggle_todo(self):
        """Test toggling a todo item's completion status"""
        with app.app_context():
            todo = Todo(title='Test Todo')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        # Toggle it
        response = self.client.get(f'/toggle/{todo_id}')
        self.assertEqual(response.status_code, 302)

        with app.app_context():
            todo = db.session.get(Todo, todo_id)
            self.assertTrue(todo.completed)

        # Toggle it back
        self.client.get(f'/toggle/{todo_id}')
        with app.app_context():
            todo = db.session.get(Todo, todo_id)
            self.assertFalse(todo.completed)

    def test_update_todo(self):
        """Test updating a todo item's title"""
        with app.app_context():
            todo = Todo(title='Original Title')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = self.client.post(
            f'/update/{todo_id}',
            data={'title': 'Updated Title'}
        )
        self.assertEqual(response.status_code, 302)

        with app.app_context():
            todo = db.session.get(Todo, todo_id)
            self.assertEqual(todo.title, 'Updated Title')

    def test_update_todo_empty_title(self):
        """Test updating a todo with empty title"""
        with app.app_context():
            todo = Todo(title='Original Title')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        response = self.client.post(
            f'/update/{todo_id}',
            data={'title': ''}
        )
        self.assertEqual(response.status_code, 302)

        with app.app_context():
            todo = db.session.get(Todo, todo_id)
            self.assertEqual(todo.title, 'Original Title')  # Title should not change

    def test_invalid_todo_id(self):
        """Test accessing invalid todo IDs"""
        invalid_id = 9999
        response = self.client.get(f'/delete/{invalid_id}')
        self.assertEqual(response.status_code, 404)

        response = self.client.get(f'/toggle/{invalid_id}')
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            f'/update/{invalid_id}',
            data={'title': 'Updated Title'}
        )
        self.assertEqual(response.status_code, 404)

    def test_todo_creation_time(self):
        """Test that todos are created with the correct timestamp"""
        with app.app_context():
            before = datetime.now(timezone.utc)
            todo = Todo(title='Test Todo')
            db.session.add(todo)
            db.session.commit()
            after = datetime.now(timezone.utc)
            
            self.assertIsNotNone(todo.created_at)
            # Convert naive datetime to UTC if needed
            if todo.created_at.tzinfo is None:
                created_at = todo.created_at.replace(tzinfo=timezone.utc)
            else:
                created_at = todo.created_at
                
            self.assertTrue(before <= created_at <= after)

if __name__ == '__main__':
    unittest.main()
