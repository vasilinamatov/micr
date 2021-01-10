#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, url_for
import argparse
from flask_pymongo import PyMongo
from flask.json import JSONEncoder
from bson import json_util


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj): return json_util.default(obj)


app = Flask(__name__, static_url_path="")
app.config["MONGO_URI"] = "mongodb://ec2-3-122-191-147.eu-central-1.compute.amazonaws.com:27017/todo"
app.json_encoder = CustomJSONEncoder
mongo = PyMongo(app)


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def make_public_task(task):
    new_task = {}

    for field in task:
        if field == '_id':
            new_task['uri'] = url_for('get_task', task_id=task['_id'], _external=True)
            new_task["id"] = str(task["_id"])
        else:
            new_task[field] = task[field]

    return new_task


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/todo/api/v1.0/tasks', methods=['GET'])
def get_tasks():
    tasks = mongo.db.tasks.find()
    return jsonify({'tasks': map(make_public_task, tasks)})


@app.route('/todo/api/v1.0/tasks/<ObjectId:task_id>', methods=['GET'])
def get_task(task_id):
    tasks = list(mongo.db.tasks.find({"_id": task_id}))

    if len(tasks) == 0:
        abort(404)

    return jsonify({'task': make_public_task(tasks[0])})


@app.route('/todo/api/v1.0/tasks', methods=['POST'])
def create_task():
    if not request.json or not 'title' in request.json:
        abort(400)

    task = {
        'title': request.json['title'],
        'description': request.json.get('describe', ""),
        'done': False
    }

    mongo.db.tasks.insert(task)

    return jsonify({'task': make_public_task(task)}), 201


@app.route('/todo/api/v1.0/tasks/<ObjectId:task_id>', methods=['PUT'])
def update_task(task_id):
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != unicode:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not unicode:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)

    update_dict = {}
    fields = ("title", "description", "done")
    for field in fields:
        if field in request.json:
            update_dict[field] = request.json[field]

    if len(update_dict.keys()) == 0:
        # Nothing changed
        return get_task(task_id), 302

    mongo.db.tasks.update({"_id": task_id}, {"$setOnInsert": update_dict}, upsert=True)

    return get_task(task_id)


@app.route('/todo/api/v1.0/tasks/<ObjectId:task_id>', methods=['DELETE'])
def delete_task(task_id):
    return jsonify({'error': "Not implemented"}), 500


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=8080, type=int, help="port to listen to")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    app.run(host='0.0.0.0', port=args.port, debug=True)
