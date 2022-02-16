from turtle import title
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)

#######################
###DB  CONFIGRATIONS###
#######################

#change pw for security
DATABASE_URI = 'postgresql://postgres:password@localhost:5432/flask_todo'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
db = SQLAlchemy(app)

#######################
####### MODELS ########
#######################

class Task(db.Model):
    __table_name__ = 'task'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    status = db.Column(db.String, nullable=False)

#######################
## HELPER FUNCTIONS ###
#######################

def serialize_tasks(queryset):
    serialized_list = []
    for obj in queryset:
        task_dict = serialize_task(obj)
        serialized_list.append(task_dict)
    return serialized_list

def serialize_task(obj):
    task_dict = {}
    task_dict['id'] = obj.id
    task_dict['title'] = obj.title
    task_dict['description'] = obj.description
    task_dict['status'] = obj.status
    return task_dict

def update_task_with_validation(task,data):
    keys = ['title','description','status']
    for key,val in data.items():
        if key in keys:
            setattr(task,key,val)
        else:
            return False

#######################
######## APIS #########
#######################

@app.route('/', methods=['GET'])
def tasks():
    tasks_qs = Task.query.all()
    tasks = serialize_tasks(tasks_qs)
    return jsonify({
        "data":tasks
    })

@app.route('/create_task', methods=['POST'])
def create_task():
    data = json.loads(request.data)
    task = Task(title=data['title'], description=data['description'], status=data['status'])
   
    db.session.add(task)
    db.session.commit()

    return jsonify({
        "data":data,
        "msg":"Task Created Successfully"
    }), 201

@app.route('/update_task/<int:id>', methods=['PUT'])
def update_task(id):

    data = json.loads(request.data)
    task = Task.query.filter_by(id=id).first()

    if not task:
        return jsonify({
            "msg":"Didn't find any tasks with given id"
        })

    if update_task_with_validation(task,data) is not None:
        return jsonify({
                "msg":"There was an error in the sent data"
            }), 400

    db.session.commit()

    return jsonify({
        "data":serialize_task(task),
        "msg":"Updated Task Successfully"
    }), 200

@app.route('/delete_task/<int:id>', methods=['DELETE'])
def delete_task(id):

    task = Task.query.filter_by(id=id).first()

    if not task:
        return jsonify({
            "msg":"Didn't find any tasks with given id"
        })

    db.session.delete(task)
    db.session.commit()

    return jsonify({
        "msg":"Deleted Task Successfully"
    }), 200

db.create_all()
app.run(host='localhost',debug=True)