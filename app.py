from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os

app = Flask(__name__)

# Use PostgreSQL in production (Render provides a PostgreSQL database)
if 'DATABASE_URL' in os.environ:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'

db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    todos = Todo.query.order_by(Todo.created_at.desc()).all()
    return render_template('index.html', todos=todos)

@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title', '').strip()
    if title and len(title) <= 200:
        new_todo = Todo(title=title)
        db.session.add(new_todo)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    todo = Todo.query.get_or_404(id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/toggle/<int:id>')
def toggle(id):
    todo = Todo.query.get_or_404(id)
    todo.completed = not todo.completed
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    todo = Todo.query.get_or_404(id)
    new_title = request.form.get('title', '').strip()
    if new_title and len(new_title) <= 200:
        todo.title = new_title
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
