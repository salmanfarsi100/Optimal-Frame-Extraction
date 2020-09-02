from flask import Flask 
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vehicle_database.db'
db = SQLAlchemy(app)

class VehicleModel(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	frame_number = db.Column(db.String(10), nullable=False)
	lane = db.Column(db.String(10), nullable=False)
	datetime = db.Column(db.String(30), nullable=False)
	image_path = db.Column(db.String(100), nullable=False)

	def __repr__(self):
		return f"Vehicle(frame_number = {frame_number}, lane = {lane}, datetime = {datetime}, image_path = {image_path})"

class ALPRModel(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	prediction = db.Column(db.String(10), nullable=False)
	confidence = db.Column(db.String(10), nullable=False)

	def __repr__(self):
		return f"ALPR(prediction = {prediction}, confidence = {confidence})"

class RadarModel(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	speed = db.Column(db.String(10), nullable=False)
	location = db.Column(db.String(10), nullable=False)

	def __repr__(self):
		return f"Radar(speed = {speed}, location = {location})"

class RoadModel(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	x11 = db.Column(db.String(10), nullable=False)
	x12 = db.Column(db.String(10), nullable=False)
	x13 = db.Column(db.String(10), nullable=False)
	x14 = db.Column(db.String(10), nullable=False)
	x21 = db.Column(db.String(10), nullable=False)
	x22 = db.Column(db.String(10), nullable=False)
	x23 = db.Column(db.String(10), nullable=False)
	x24 = db.Column(db.String(10), nullable=False)
	y11 = db.Column(db.String(10), nullable=False)
	y22 = db.Column(db.String(10), nullable=False)
	y1 = db.Column(db.String(10), nullable=False)
	y2 = db.Column(db.String(10), nullable=False)

	def __repr__(self):
		return f"Road(x11 = {x11}, x12 = {x12}, x13 = {x13}, x14 = {x14}, x21 = {x21}, x22 = {x22}, x23 = {x23}, x24 = {x24}, y11 = {y11}, y22 = {y22}, y1 = {y1}, y2 = {y2})"

db.create_all()

vehicle_put_args = reqparse.RequestParser()
vehicle_put_args.add_argument("frame_number", type=str, help="Frame number required", required=True)
vehicle_put_args.add_argument("lane", type=str, help="Lane required", required=True)
vehicle_put_args.add_argument("datetime", type=str, help="Date and time required", required=True)
vehicle_put_args.add_argument("image_path", type=str, help="Image path required", required=True)

alpr_put_args = reqparse.RequestParser()
alpr_put_args.add_argument("prediction", type=str, help="Prediction required", required=True)
alpr_put_args.add_argument("confidence", type=str, help="Confidence required", required=True)

radar_put_args = reqparse.RequestParser()
radar_put_args.add_argument("speed", type=str, help="Speed required", required=True)
radar_put_args.add_argument("location", type=str, help="location required", required=True)

road_put_args = reqparse.RequestParser()
road_put_args.add_argument("x11", type=str, help="x11 required", required=True)
road_put_args.add_argument("x12", type=str, help="x12 required", required=True)
road_put_args.add_argument("x13", type=str, help="x13 required", required=True)
road_put_args.add_argument("x14", type=str, help="x14 required", required=True)
road_put_args.add_argument("x21", type=str, help="x21 required", required=True)
road_put_args.add_argument("x22", type=str, help="x22 required", required=True)
road_put_args.add_argument("x23", type=str, help="x23 required", required=True)
road_put_args.add_argument("x24", type=str, help="x24 required", required=True)
road_put_args.add_argument("y11", type=str, help="y11 required", required=True)
road_put_args.add_argument("y22", type=str, help="y22 required", required=True)
road_put_args.add_argument("y1", type=str, help="y1 required", required=True)
road_put_args.add_argument("y2", type=str, help="y2 required", required=True)

vehicle_resource_fields = {
	'id': fields.Integer,
	'frame_number': fields.String,
	'lane': fields.String,
	'datetime': fields.String,
	'image_path': fields.String
}

alpr_resource_fields = {
	'id': fields.Integer,
	'prediction': fields.String,
	'confidence': fields.String
}

radar_resource_fields = {
	'id': fields.Integer,
	'speed': fields.String,
	'location': fields.String
}

road_resource_fields = {
	'id': fields.Integer,
	'x11': fields.String,
	'x12': fields.String,
	'x13': fields.String,
	'x14': fields.String,
	'x21': fields.String,
	'x22': fields.String,
	'x23': fields.String,
	'x24': fields.String,
	'y11': fields.String,
	'y22': fields.String,
	'y1': fields.String,
	'y2': fields.String
}

class Vehicle(Resource):
	@marshal_with(vehicle_resource_fields)
	def get(self, vehicle_id):
		result = VehicleModel.query.filter_by(id=vehicle_id).first()
		if not result:
			abort(404, message="Could not find vehicle with that id")
		return result

	@marshal_with(vehicle_resource_fields)
	def put(self, vehicle_id):
		args = vehicle_put_args.parse_args()
		result = VehicleModel.query.filter_by(id=vehicle_id).first()
		if result:
			abort(409, message="Vehicle id taken...")
		vehicle = VehicleModel(id=vehicle_id, frame_number=args['frame_number'], lane=args['lane'], datetime=args['datetime'], image_path=args['image_path'])
		db.session.add(vehicle)
		db.session.commit()
		return vehicle, 201	

class ALPR(Resource):
	@marshal_with(alpr_resource_fields)
	def get(self, plate_id):
		result = ALPRModel.query.filter_by(id=plate_id).first()
		if not result:
			abort(404, message="Could not find number plate with that id")
		return result

	@marshal_with(alpr_resource_fields)
	def put(self, plate_id):
		args = alpr_put_args.parse_args()
		result = ALPRModel.query.filter_by(id=plate_id).first()
		if result:
			abort(409, message="Number plate id taken...")
		plate = ALPRModel(id=plate_id, prediction=args['prediction'], confidence=args['confidence'])
		db.session.add(plate)
		db.session.commit()
		return plate, 201	

class Radar(Resource):
	@marshal_with(radar_resource_fields)
	def get(self, radar_id):
		result = RadarModel.query.filter_by(id=radar_id).first()
		if not result:
			abort(404, message="Could not find radar reading with that id")
		return result

	@marshal_with(radar_resource_fields)
	def put(self, radar_id):
		args = radar_put_args.parse_args()
		result = RadarModel.query.filter_by(id=radar_id).first()
		if result:
			abort(409, message="Radar reading id taken...")
		radar = RadarModel(id=radar_id, speed=args['speed'], location=args['location'])
		db.session.add(radar)
		db.session.commit()
		return radar, 201	

class Road(Resource):
	@marshal_with(road_resource_fields)
	def get(self, road_id):
		result = RoadModel.query.filter_by(id=road_id).first()
		if not result:
			abort(404, message="Could not find road configurations with that id")
		return result

	@marshal_with(road_resource_fields)
	def put(self, road_id):
		args = road_put_args.parse_args()
		result = RoadModel.query.filter_by(id=road_id).first()
		if result:
			abort(409, message="Road configurations id taken...")
		road = RoadModel(id=road_id, x11=args['x11'], x12=args['x12'], x13=args['x13'], x14=args['x14'], x21=args['x21'], x22=args['x22'], x23=args['x23'], x24=args['x24'], y11=args['y11'], 			y22=args['y22'], y1=args['y1'], y2=args['y2'])
		db.session.add(road)
		db.session.commit()
		return road, 201	

	@marshal_with(road_resource_fields)
	def patch(self, road_id):
		args = road_put_args.parse_args()
		result = RoadModel.query.filter_by(id=road_id).first()
		if not result:
			abort(404, message="Configuration does not exist, cannot update...")

		if args['x11']:
			result.x11 = args['x11']
		if args['x12']:
			result.x12 = args['x12']
		if args['x13']:
			result.x13 = args['x13']
		if args['x14']:
			result.x14 = args['x14']
		if args['x21']:
			result.x21 = args['x21']
		if args['x22']:
			result.x22 = args['x22']
		if args['x23']:
			result.x23 = args['x23']
		if args['x24']:
			result.x24 = args['x24']
		if args['y11']:
			result.y11 = args['y11']
		if args['y22']:
			result.y22 = args['y22']
		if args['y1']:
			result.y1 = args['y1']
		if args['y2']:
			result.y2 = args['y2']		

		db.session.commit()
		return result

api.add_resource(Vehicle, "/vehicle/<int:vehicle_id>")
api.add_resource(ALPR, "/plate/<int:plate_id>")
api.add_resource(Radar, "/radar/<int:radar_id>")
api.add_resource(Road, "/road/<int:road_id>")

if __name__ == "__main__":
	app.run(debug=True)
