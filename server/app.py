#!/usr/bin/env python3

from models import db, Activity, Camper, Signup
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask import Flask, make_response, jsonify, request, abort
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api( app )


@app.route('/')
def home():
    return ''

@app.route( '/signups', methods = ['GET', 'POST'] )
def signups ( ) :
    if request.method == 'GET' :
        return make_response( jsonify( Signup.all() ), 200 )
    
    if request.method == 'POST' :
        rq = request.get_json()
        new_signup = Signup(
            activity_id = rq[ 'activity_id' ],
            time = rq[ 'time' ],
            camper_id = rq[ 'camper_id' ]
        )

        errors = new_signup.validation_errors
        if errors :
            new_signup.clear_validation_errors()
            return validation_errors_found( errors )
        else :
            db.session.add( new_signup )
            db.session.commit()

            activity = new_signup.activity.to_dict()
            return make_response( jsonify( activity ), 201 )
        

@app.route( '/activities' )
def activities ( ) :
    return make_response( jsonify( Activity.all() ), 200 )

@app.route( '/activities/<int:id>', methods = ['GET', 'DELETE'] )
def activity ( id ) :
    activity = Activity.find_by_id( id )
    if activity :

        if request.method.upper() == 'GET' :
            return make_response( jsonify( activity.to_dict() ), 200 )
        
        elif request.method.upper() == "DELETE" :
            for signup in activity.signups :
                db.session.delete( signup )

            db.session.delete( activity )
            db.session.commit()
            return make_response( {}, 204 )
    else :
        return resource_not_found( 'Activity' )


class Campers ( Resource ) :
    def get ( self ) :
        return make_response( Camper.all(), 200 )
    
    def post ( self ) :
        rq = request.get_json()
        new_camper = Camper(
            name = rq[ 'name' ],
            age = rq[ 'age' ]
        )

        errors = new_camper.validation_errors
        if errors :
            new_camper.clear_validation_errors()
            return validation_errors_found( errors )
        else :
            db.session.add( new_camper )
            db.session.commit()
            return make_response( jsonify( new_camper.to_dict() ), 201 )

api.add_resource( Campers, '/campers', endpoint = 'campers' )

class CamperById ( Resource ) :
    def camper_not_found ( self ) :
        return make_response( { 'errors': ['Camper not found.'] }, 404 )
    
    def get ( self, id ) :
        camper = Camper.find_by_id( id )
        if camper :
            return make_response( jsonify( camper.to_dict() ), 200 )
        else :
            return resource_not_found( 'Camper' )

    def patch ( self, id ) :
        camper = Camper.find_by_id( id )
        if camper :
            rq = request.get_json()
            for attr in rq :
                setattr( camper, attr, rq[ attr ] )

            errors = camper.validation_errors
            if errors :
                camper.clear_validation_errors()
                return validation_errors_found( errors )
            else :
                db.session.add( camper )
                db.session.commit()
                return make_response( jsonify( camper.to_dict() ), 200 )
        else :
            return resource_not_found( 'Camper' )
        
api.add_resource( CamperById, '/campers/<int:id>', endpoint = 'camper' )

def resource_not_found ( resource ) :
    return make_response( { 'errors': [f"{ resource } was not found." ] }, 404 )

def validation_errors_found( errors ) :
    return make_response( { 'errors': errors }, 422 )

if __name__ == '__main__':
    app.run(port=5555, debug=True)
