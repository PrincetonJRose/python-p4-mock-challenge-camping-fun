from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(metadata=metadata)


class Activity(db.Model, SerializerMixin):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    difficulty = db.Column(db.Integer)
    created_at = db.Column( db.DateTime, server_default = db.func.now() )
    updated_at = db.Column( db.DateTime, onupdate = db.func.now() )

    # Add relationship
    signups = db.relationship( 'Signup', backref = 'activity' )
    campers = association_proxy( 'signups', 'camper' )

    @classmethod
    def all ( cls ) :
        return [ activity.to_dict() for activity in Activity.query.all() ]
    
    @classmethod
    def find_by_id ( cls, id ) :
        return Activity.query.filter_by( id = id ).first()
    
    # Add serialization rules
    def to_dict ( self ) :
        return {
            'id': self.id,
            'name': self.name,
            'difficulty': self.difficulty
        }
    
    def to_dict_with_campers ( self ) :
        activity = self.to_dict()
        activity[ 'campers' ] = [ camper.to_dict() for camper in self.campers ]
        return activity
    
    def __repr__(self):
        return f'<Activity {self.id}: {self.name}>'


class Camper(db.Model, SerializerMixin):
    __tablename__ = 'campers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer)
    created_at = db.Column( db.DateTime, server_default = db.func.now() )
    updated_at = db.Column( db.DateTime, onupdate = db.func.now() )

    # Add relationship
    signups = db.relationship( 'Signup', backref = 'camper' )
    activities = association_proxy( 'signups', 'activity' )

    @classmethod
    def all ( cls ) :
        return [ camper.to_dict() for camper in Camper.query.all() ]
    
    @classmethod
    def find_by_id ( cls, id ) :
        return Camper.query.filter( Camper.id == id ).first()
    
    # Add serialization rules
    def to_dict( self ) :
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
        }
    
    def to_dict_with_activities ( self ) :
        camper = self.to_dict()
        camper[ 'activities' ] = [ activity.to_dict() for activity in self.activities ]
        return camper
    
    # Add validation
    validation_errors = []

    @classmethod
    def clear_validation_errors ( cls ) :
        cls.validation_errors = []

    @validates( 'name' )
    def validate_name ( self, db_column, name ) :
        if type( name ) is str and name :
            return name
        else : self.validation_errors.append( 'Camper must have a name.' )

    @validates( 'age' )
    def validate_age ( self, db_column, age ) :
        if type( age ) is int :
            if age in range( 8, 19 ) :
                return age
            else :
                self.validation_errors.append( 'Age must be between 8 and 18.' )
        else :
            self.validation_errors.append( 'Age must be an integer.' )
    
    
    def __repr__(self):
        return f'<Camper {self.id}: {self.name}>'


class Signup(db.Model, SerializerMixin):
    __tablename__ = 'signups'

    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Integer)
    created_at = db.Column( db.DateTime, server_default = db.func.now() )
    updated_at = db.Column( db.DateTime, onupdate = db.func.now() )

    # Add relationships
    activity_id = db.Column( db.Integer, db.ForeignKey( 'activities.id' ) )
    camper_id = db.Column( db.Integer, db.ForeignKey( 'campers.id' ) )

    @classmethod
    def all ( cls ) :
        return [ signup.to_dict() for signup in Signup.query.all() ]
    
    # Add serialization rules
    def to_dict( self ) :
        return {
            'id': self.id,
            'time': self.time,
            'activity': self.activity.name,
            'camper': self.camper.name
        }
    
    # Add validation
    validation_errors = []

    @classmethod
    def clear_validation_errors ( cls ) :
        cls.validation_errors = []

    @validates( 'time' )
    def validate_time ( self, db_column, time ) :
        if type( time ) is int :
            if time in range( 0, 24 ) :
                return time
            else :
                self.validation_errors.append( 'Time must be between 0 and 23.' )
        else :
            self.validation_errors.append( 'Time must be an integer.' )

    @validates( 'camper_id' )
    def validate_camper ( self, db_column, camper_id ) :
        camper = Camper.find_by_id( camper_id )
        if camper :
            return camper_id
        else:
            self.validation_errors.append( 'Camper was not found.' )

    @validates( 'activity_id' )
    def validate_activity ( self, db_column, activity_id ) :
        activity = Activity.find_by_id( activity_id )
        if activity :
            return activity_id
        else :
            self.validation_errors.append( 'Activity was not found.' )
    
    def __repr__(self):
        return f'<Signup {self.id}>'


# add any models you may need.
