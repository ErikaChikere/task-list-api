from app import db 
from flask import Blueprint, request, make_response, jsonify
from app.models.task import Task 
from app.models.goal import Goal
from datetime import datetime
import os 
import requests



task_list_bp = Blueprint("Task",__name__)

@task_list_bp.route("/tasks", methods=["POST"])
def create_a_task(): 
    request_body = request.get_json()

    if not ("title" in request_body
            and "description" in request_body
            and "completed_at" in request_body):
    
       
         return make_response(jsonify({
            "details": "Invalid data"
        }), 400)
        

    new_task = Task.from_json(request_body)
    # new_task = Task(title=request_body["title"],
    #             description=request_body["description"],
    #             completed_at=request_body["completed_at"])

    db.session.add(new_task)
    db.session.commit()

  

    response = {
            "task": new_task.as_json()
            
               }
    return make_response(jsonify(response), 201)




@task_list_bp.route("/tasks", methods=["GET"])
def retrieve_all_tasks(): 
    if "filter" in request.args: 
        # tasks = Task.query.all()
        # [task for task in tasks]
        # tasks = [task for task in tasks if task.title == request.args["filter"]]
        tasks = Task.query.filter_by(title = request.args["filter"]).all() 
    elif "sort" in request.args:
        if request.args["sort"] == "desc":
            tasks = Task.query.order_by(Task.title.desc()).all()
        elif request.args["sort"] == "id": 
            tasks = Task.query.order_by(Task.id.asc()).all()
        else:
            tasks = Task.query.order_by(Task.title.asc()).all()
    else:
        tasks = Task.query.all()
    

    # return jsonify([
    #     {
    #         "id": q.id,
    #         "title": q.title,
    #         "description": q.description,
    #         "is_complete": q.is_complete()
    #     } for q in tasks
    # ])

    return jsonify([
        task.as_json() for task in tasks
    ])


@task_list_bp.route("/tasks/<task_id>", methods=["GET", "PUT", "DELETE"])
def retrieve_one_task(task_id): 
    task = Task.query.filter_by(id = task_id).first()

    if task is None: 
        return make_response("", 404)

    if request.method == "GET":   
        return jsonify({
                "task": task.as_json()
        }) 



       
    elif request.method == "PUT": 
        form_data = request.get_json()

        task.title = form_data["title"]
        task.description = form_data["description"]
        task.completed_at = form_data["completed_at"]


        db.session.commit()
        
        return jsonify({
            "task": task.as_json()
        })

    elif request.method == "DELETE":
        db.session.delete(task)
        db.session.commit()
        return jsonify (
        {
            "details": (f'Task {task.id} "{task.title}" successfully deleted')
        })
                

@task_list_bp.route("/tasks/<task_id>/mark_complete", methods=["PATCH"])
def mark_complete(task_id): 
    task = Task.query.filter_by(id = task_id).first()
    if task is None: 
        return make_response("", 404)

    access_token = os.environ.get("SLACK_BOT_TOKEN")
    path = "https://slack.com/api/chat.postMessage"
    response = requests.post(path, data = {
        "channel": "task-notifications",
        "text": f"Someone just completed the task {task.title}",
    }, headers = {
        "Authorization": access_token,
    })
    

    if task.is_complete(): 
        task.completed_at = datetime.now() 
        db.session.commit()
        return jsonify({
            "task": task.as_json()
        })
    else: 
        task.completed_at = datetime.now()
        db.session.commit() 
        return jsonify({
            "task": task.as_json()
        })
        

@task_list_bp.route("/tasks/<task_id>/mark_incomplete", methods=["PATCH"])
def mark_incomplete(task_id): 
    task = Task.query.filter_by(id = task_id).first()

    if task is None: 
        return make_response("", 404)


    if task.is_complete(): 
        task.completed_at = None
        db.session.commit()

    return jsonify({
        "task": task.as_json()
    })
    

    

#Routes for Goals

goals_bp = Blueprint("goals", __name__, url_prefix="/goals")
@goals_bp.route("", methods=["POST"])
def create_a_goal(): 
    request_body = request.get_json()

    if not ("title" in request_body):        
         return make_response(jsonify({
            "details": "Invalid data"
        }), 400)
        

    new_goal = Goal(title=request_body["title"])
        
    db.session.add(new_goal)
    db.session.commit()


    response = {
            "goal": new_goal.to_json()
        }
    return make_response(jsonify(response), 201)

@goals_bp.route("", methods=["GET"])
def retrieve_all_goals():
  
    if "sort" in request.args and request.args["sort"] == "title": 
    # if "sort" in request.args == "title": # always false, because it reduces to `if True == "title"`
        goals = Goal.query.order_by(Goal.title.asc()).all()
    
    else: 
        goals = Goal.query.all()

    return jsonify([goal.to_json() for goal in goals])




@goals_bp.route("/<goal_id>", methods=["GET", "PUT", "DELETE"])
def retrieve_one_goals_tasks(goal_id): 
    goal = Goal.query.filter_by(goal_id=goal_id).first()

    if goal is None: 
        return make_response("", 404)
    
    if request.method == "GET":
       return jsonify(
            {"goal":goal.to_json() }
        )

    elif request.method == "PUT": 
        form_data = request.get_json()

        goal.title = form_data["title"]
    
        db.session.commit()
        
        return jsonify({ "goal": goal.to_json() })

    elif request.method == "DELETE":
        db.session.delete(goal)
        db.session.commit()
        return jsonify (
        {
            "details": (f'Goal {goal.goal_id} "{goal.title}" successfully deleted')
        })


@goals_bp.route("/<goal_id>/tasks", methods=["POST"])
def send_task_ids_goal(goal_id): 
  

    request_body = request.get_json()
    task_ids = request_body['task_ids']
    for task_id in task_ids:
        task = Task.query.filter_by(id = task_id).first()
        task.goal_id = goal_id

    db.session.commit()
    response = {
                "id": int(goal_id),
                "task_ids": task_ids,
            }
    return make_response(jsonify(response), 200)

@goals_bp.route("/<goal_id>/tasks", methods=["GET"])
def retrieve_one_task(goal_id): 
    goal = Goal.query.filter_by(goal_id=goal_id).first()
    tasks = Task.query.filter_by(goal_id=goal_id).all()
    
    if goal is None: 
        return make_response("", 404)


    response = goal.to_json() # creates a dictionary with id and title entries
    response["tasks"] = [task.as_json() for task in tasks] # adds a third entry to that dictionary



    return make_response(jsonify(response), 200)
    
