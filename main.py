from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import os


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("key")
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL1", "sqlite:///todos.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Table(db.Model):
    __tablename__ = "table"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    todo_lists = db.relationship("TodoList", back_populates="table")


class TodoList(db.Model):
    __tablename__ = "todo_list"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey("table.id"))
    table = db.relationship("Table", back_populates="todo_lists")
    tasks = db.relationship("Task", back_populates="todo_list")


class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(150), nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey("todo_list.id"))
    todo_list = db.relationship("TodoList", back_populates="tasks")


class NewForm(FlaskForm):
    task = StringField("name", validators=[DataRequired()])
    submit = SubmitField("Submit")


class EditForm(FlaskForm):
    edit_task = StringField("edit", validators=[DataRequired()])
    submit = SubmitField("Submit")


@app.route("/")
def my_tables():
    tables = Table.query.all()
    return render_template("index.html", tables=tables)


@app.route("/todo/<int:table_id>")
def my_todos(table_id):
    table = Table.query.get(table_id)
    return render_template("container.html", table=table)


@app.route("/add/<name>/<int:id_parent>", methods=["GET", "POST"])
def add(name, id_parent):
    form = NewForm()
    if form.validate_on_submit():
        if name == "Table":
            new = Table(title=form.task.data)
        elif name == "TodoList":
            parent = Table.query.get(id_parent)
            new = TodoList(title=form.task.data, table=parent)
        else:
            parent = TodoList.query.get(id_parent)
            new = Task(task=form.task.data, todo_list=parent)
        db.session.add(new)
        db.session.commit()
        if name == "Table":
            return redirect(url_for("my_tables"))
        elif name == "TodoList":
            table_id = id_parent
            return redirect(url_for("my_todos", table_id=table_id))
        else:
            task = new
            table_id = task.todo_list.table.id
            return redirect(url_for("my_todos", table_id=table_id))
    return render_template("add.html", form=form, name=name)


@app.route("/edit/<name>/<int:name_id>", methods=["GET", "POST"])
def edit(name, name_id):
    form = EditForm()
    if form.validate_on_submit():
        if name == "Table":
            table_to_edit = Table.query.get(name_id)
            table_to_edit.title = form.edit_task.data
            db.session.commit()
            return redirect(url_for("my_tables"))
        elif name == "TodoList":
            list_to_edit = TodoList.query.get(name_id)
            list_to_edit.title = form.edit_task.data
            db.session.commit()
            return redirect(url_for("my_todos", table_id=list_to_edit.table_id))
        else:
            task_to_edit = Task.query.get(name_id)
            task_to_edit.task = form.edit_task.data
            db.session.commit()
            return redirect(url_for("my_todos", table_id=task_to_edit.todo_list.table_id))
    return render_template("edit-task.html", form=form, name=name)


@app.route("/delete/<name>/<int:name_id>")
def delete(name, name_id):
    if name == "Task":
        to_delete = Task.query.get(name_id)
        table_id = to_delete.todo_list.table_id
        db.session.delete(to_delete)
        db.session.commit()
        return redirect(url_for("my_todos", table_id=table_id))
    elif name == "Table":
        to_delete = Table.query.get(name_id)
        for todo_list in to_delete.todo_lists:
            for task in todo_list.tasks:
                db.session.delete(task)
                db.session.commit()
            db.session.delete(todo_list)
        db.session.delete(to_delete)
        db.session.commit()
        return redirect(url_for("my_tables"))
    else:
        to_delete = TodoList.query.get(name_id)
        table_id = to_delete.table_id
        for task in to_delete.tasks:
            db.session.delete(task)
        db.session.delete(to_delete)
        db.session.commit()
    return redirect(url_for("my_todos", table_id=table_id))


if __name__ == "__main__":
    app.run(debug=True)

