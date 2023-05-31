import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
app.app_context().push()
setup_db(app)
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add(
        "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
    )
    response.headers.add(
        "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
    )
    return response
    
'''
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
#db_drop_and_create_all()

# ROUTES
'''
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks')
def drinks():
    drinks = Drink.query.all()
    list = [item.short() for item in drinks]
    return jsonify({
        "success": True,
        "drinks": list,
        "total": len(list)
    })

'''
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def drinks_detail(jwt):
    drinks = Drink.query.all()
    list = [item.long() for item in drinks]
    return jsonify({
        "success": True,
        "drinks": list,
        "total": len(list)
    })

'''
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(jwt):
    body = request.get_json()
    try:
        drink = Drink(
            title=body.get('title', None),
            recipe=json.dumps(body.get('recipe', None))
        )
        drink.insert()
    except:
        abort(422)

    return jsonify({
        "success": True,
        "drinks": [item.short() for item in Drink.query.all()]
    })

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(jwt, id):
    body = request.get_json()
    drink = Drink.query.get(id)
    if drink == None:
        abort(404)
    
    try:
        drink.title = body.get('title', None)
        drink.recipe = json.dumps(body.get('recipe', None))
        drink.update()
    except:
        abort(422)

    return jsonify({
        "success": True,
        "drinks": body
    })

'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(jwt, id):
    drink = Drink.query.get(id)
    if drink == None:
        abort(404)

    try:
        if drink != None:
            drink.delete()
    except:
        abort(422)

    return jsonify({
        "success": True,
        "drinks": [item.short() for item in Drink.query.all()]
    })


# Error Handling
'''
Example error handling for unprocessable entity
'''

@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({"success": False, "error": 404, "message": "resource not found"}),
        404,
    )

@app.errorhandler(422)
def unprocessable(error):
    return (
        jsonify({"success": False, "error": 422, "message": "unprocessable"}),
        422,
    )

@app.errorhandler(400)
def bad_request(error):
    return (
        jsonify({"success": False, "error": 400, "message": "bad request"}),
        400,
    )

@app.errorhandler(405)
def not_found(error):
    return (
        jsonify({"success": False, "error": 405, "message": "method not allowed"}),
        405,
    )
'''
error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def handle_auth_error(ex):
    return (
        jsonify({"success": False, "error": ex.status_code, "message": ex.error})
    )