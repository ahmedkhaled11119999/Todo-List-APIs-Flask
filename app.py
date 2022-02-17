from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
import os
from datetime import timedelta
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    create_refresh_token
)
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

#######################
##TOKEN CONFIGRATIONS##
#######################

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

jwt = JWTManager(app)

#######################
###DB  CONFIGRATIONS###
#######################

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
db = SQLAlchemy(app)

#######################
####### MODELS ########
#######################

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String)
    password = db.Column(db.String)

    def __repr__(self):
        return self.username
class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    status = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return self.title + ' - ' + self.status
#######################
## HELPER FUNCTIONS ###
#######################

def serializer_list(queryset, attrs):
    serialized_list = []
    for obj in queryset:
        task_dict = serializer(obj, attrs)
        serialized_list.append(task_dict)
    return serialized_list


#attrs is list of strings representing attributes in object
def serializer(obj , attrs):
    serialized_obj = {}
    for attr in attrs:
        serialized_obj[attr] = getattr(obj,attr)
    return serialized_obj


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

@app.route('/register', methods=['POST'])
def register():
    try:
        data = json.loads(request.data)
        user = User(username=data['username'],password=data['password'])
        db.session.add(user)
        db.session.commit()
        return jsonify({
        'status': 'Success',
        'msg': "user created successfully",
        'data': serializer(user,['id','username','password'])
        }), 201
    except:
        return jsonify({
        'status': 'Fail',
        'msg': "Incorrect user data"
        }), 400


@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    try:
        db_user = User.query.filter_by(username=username).first()
        if db_user.password == password:
            access_token = create_access_token(identity=db_user.id)
            refresh_token = create_refresh_token(identity=db_user.id)

            return jsonify({
                'status': 'success',
                'data': {
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
            }), 200
        return jsonify({
                'status': 'Fail',
                'msg': "username or password is incorrect"
            }), 403
    except:
        return jsonify({
                'status': 'Fail',
                'msg': "No such user with the given username"
            }), 404

@app.route('/', methods=['GET'])
def tasks():
    tasks_qs = Task.query.all()
    tasks = serializer_list(tasks_qs,['id','title','description','status','user_id'])
    return jsonify({
        "data":tasks
    })

@app.route('/create_task', methods=['POST'])
@jwt_required()
def create_task():
    data = json.loads(request.data)
    user_id = get_jwt_identity()
    if User.query.filter_by(id=user_id).first(): 
        try:
            task = Task(title=data['title'], description=data['description'],
            status=data['status'],user_id=user_id)
        
            db.session.add(task)
            db.session.commit()

            serialized_task = serializer(obj=task,attrs=['id','title',
            'description','status','user_id'])
            return jsonify({
                "data": serialized_task,
                "msg":"Task Created Successfully"
            }), 201
        except:
            return jsonify({
            "msg":"Invalid task data was recieved"
        }), 400
    else:
        return jsonify({
            "msg":"wrong user id"
        }), 400


@app.route('/update_task/<int:id>', methods=['PUT'])
@jwt_required()
def update_task(id):

    task = Task.query.filter_by(id=id).first()
    if not task:
        return jsonify({
            "msg":"Didn't find any tasks with given id"
        })

    data = json.loads(request.data)
    user_id = get_jwt_identity()

    if task.user_id != user_id:
        return jsonify({
                "msg":"Your are unauthorized to update this task"
            }), 403
    
    if update_task_with_validation(task,data) is not None:
        return jsonify({
                "msg":"There was an error in the sent data"
            }), 400

    db.session.commit()

    return jsonify({
        "data":serializer(task,['id','title','description','status','user_id']),
        "msg":"Updated Task Successfully"
    }), 200

@app.route('/delete_task/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_task(id):

    task = Task.query.filter_by(id=id).first()
    if not task:
        return jsonify({
            "msg":"Didn't find any tasks with given id"
        })

    user_id = get_jwt_identity()

    if task.user_id != user_id:
        return jsonify({
                "msg":"Your are unauthorized to delete this task"
            }), 403
            
    db.session.delete(task)
    db.session.commit()

    return jsonify({
        "msg":"Deleted Task Successfully"
    }), 200

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)

    return jsonify({
        'access_token': access_token
    }), 200

db.create_all()
app.run(host='localhost',debug=True)