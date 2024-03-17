from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200

@app.route("/count")
def count():
    """return length of data"""
    if songs_list:
        return jsonify(length=len(songs_list)), 200

    return {"message": "Internal server error"}, 500

@app.route("/song",methods=["GET"])
def songs():
    list_songs = list(db.songs.find({}))  # Convert Cursor object to list of dictionaries
    for song in list_songs:
        song['_id'] = str(song['_id'])
    return jsonify({"songs": list_songs}), 200

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    song=db.songs.find_one({"id":id})

    if not song:
        return {"message":"song with id not found"},404
    song['_id']=str(song['_id'])
    return jsonify(song),200

@app.route("/song",methods=["POST"])
def create_song():
    song_data=request.json
    for song in songs_list:
        if song['id']==song_data['id']:
            return {'Message':f"song with id {song['id']} already present"}
    
    songs_list.append(song_data)
    query_out=db.songs.insert_one(song_data)
    inserted_id_str = str(query_out.inserted_id)
    response_data = {"inserted id": {"$oid": inserted_id_str}}
    return jsonify(response_data)

@app.route("/song/<int:id>",methods=["PUT"])
def update_song(id):
    song_data=request.json
    old_song=db.songs.find_one({"id":id})

    if not old_song:
        return {"message":"song not found"},404

    if old_song['lyrics'] == song_data['lyrics'] and old_song['title']==song_data['title']:
        return jsonify({"message": "song found, but nothing updated"}), 200
    
    query_out=db.songs.update_one({"id":id},{"$set":song_data})
    song=db.songs.find_one({"id":id})

    if not song:
        return {"message":"song with id not found"},404

    song['_id']=str(song['_id'])
    return jsonify(song),200

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    result=db.songs.delete_one({"id":id})
    if result.deleted_count == 0:
        return jsonify({"message": "song not found"}), 404
    else:
        return '', 204



       
