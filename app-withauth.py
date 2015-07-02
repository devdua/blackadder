#!/usr/bin/python
import datetime
import time
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from pymongo import MongoClient
import os, subprocess, csv, string, collections
import json
from bson import json_util
from flask import Flask, abort, jsonify, render_template, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename

app = Flask(__name__,static_folder='static')

app.config['UPLOAD_FOLDER'] = '/home/dev/blackadder/static/uploads/'
app.config['FACE_DB'] = '/home/dev/blackadder/static/faceDB/UserFaces/'
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])
client = MongoClient('mongodb://dev-blackadder:blackadder1234@ds056727.mongolab.com:56727/blackadder?authMechanism=MONGODB-CR')
db = client.blackadder
faces = db.faces
auth = HTTPBasicAuth()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

def hash_password(password):
        return pwd_context.encrypt(password)

def verifypassword(username,password):
    users = db.users
    user = users.find_one({"username": username})
    pwd = user['password']    
    return pwd_context.verify(password, pwd)

def get_user(username):
    users = db.users
    user = users.find_one({"username": username})
    return user

@auth.verify_password
def verify_password(username, password):
    user = get_user(username)
    if not user or not verifypassword(username,password):
        return False
    d = datetime.datetime.now()
    print 'User '+username+' logged in at ',d
    return True

@app.route('/api/add_user', methods = ['POST'])
def new_user():
    root_user = request.json.get('admin')
    root_password = request.json.get('secret-key')
    username = request.json.get('username')
    password = request.json.get('password')
    print root_user + ' ' + root_password
    print username + ' ' + password
    if root_user is None or root_password is None:
        abort(400)
    elif root_user == 'capt_quirk':
        if root_password != 'black-adder':
            return jsonify({"error":"Unauthorized!"})
    else:
        return jsonify({"error":"Unauthorized!"})
    if username is None or password is None:
        abort(400) # missing arguments
    if get_user(username) is not None:
        return jsonify({"error":"user exists!"}) # existing user
    #user = User(username = username)
    password = hash_password(password)
    users = db.users
    user = {"username" : username, "password" : password}
    id = users.insert(user)
    return jsonify({ 'username': username , "status" : "User added!"})

@app.route('/')
#@auth.login_required
def index():
    return render_template('index.html')

@app.route('/run', methods=['GET','POST'])
def runface():
    file = request.files['file']
    if file.filename=='' :
        return render_template('error.html')
    elif file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    enroll = ['br' ,'-algorithm', 'FaceRecognition', '-enrollAll' ,'-enroll', 'static/faceDB' ,'faceGal.gal']
    recogsearch = ['br' ,'-algorithm', 'FaceRecognition', '-compare' ,'static/uploads/'+filename , 'faceGal.gal', 'Results/faceSearch.csv']
    p = subprocess.Popen(enroll)
    p.wait()
    p = subprocess.Popen(recogsearch)
    p.wait()
    similarity = [0.0]*11
    files = []
    f = open('Results/faceSearch.csv', 'rb')
    reader = csv.reader(f)
    i = 0
    j = 0
    k = 0
    for row in reader:
        if i == 0:
            i = 1
        elif i!=0:
            similarity[j] = 100*float(row[1])
            j += 1
    for x in xrange(1,12):
        files.append("/static/faceDB/"+str(x)+".jpg")
    result_data = {}
    for i,j in zip(similarity,files):
        result_data[i] = j
    result_data = collections.OrderedDict(sorted(result_data.items(), reverse=True))
    return render_template('results.html', r = result_data, uploaded = filename)

@app.route('/enroll', methods=['PUT'])
def enroll_person():
    FaceName = request.headers.get('Who')
    print FaceName
    FaceList = []
    Base64Image = request.data.split(',')
    for n in range(0,3):
	#filename = (app.config['FACE_DB']+FaceName+"_"+str(n)+".jpg")
	filename = (app.config['FACE_DB'].replace("/home/dev/blackadder/","")+FaceName+"_"+str(n)+".jpg")

	FaceList.append(filename)
	file = open(filename, 'wb')
    	file.write(Base64Image[n].decode('base64'))
    	file.close()
    enroll = ['br' ,'-algorithm', 'FaceRecognition', '-enrollAll' ,'-enroll', app.config['FACE_DB'] ,'faceGal.gal']
    p = subprocess.Popen(enroll)
    p.wait()
    
    for face in FaceList:
    	face.replace("/home/dev/blackadder/","")
   	print FaceList
    faces = db.faces
    FaceRecord = {"Name" : FaceName, "FaceList" : FaceList}
    id = faces.insert(FaceRecord)
    return str(id)

@app.route('/recog', methods=['PUT'])
def recogface():
    #print request.data
    startTime = int(round(time.time() * 1000))
    Base64Image = request.data
    file = open(app.config['UPLOAD_FOLDER']+"imageuploaded.jpg", 'wb')
    file.write(Base64Image.decode('base64'))
    file.close()
    file = open(app.config['UPLOAD_FOLDER']+"imageuploaded.jpg", "rb")
    filename = "imageuploaded.jpg"
    #if file.filename=='' :
    #    return render_template('error.html')
    #elif file and allowed_file(file.filename):
    #    filename = secure_filename(file.filename)
    #    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    enroll = ['br' ,'-algorithm', 'FaceRecognition', '-enrollAll' ,'-enroll', app.config['FACE_DB'] ,'faceGal.gal']
    recogsearch = ['br' ,'-algorithm', 'FaceRecognition', '-compare' ,app.config['UPLOAD_FOLDER']+filename , 'faceGal.gal', 'Results/faceSearch.csv']
    p = subprocess.Popen(enroll)
    p.wait()
    p = subprocess.Popen(recogsearch)
    p.wait()
    similarity = []
    files = []
    fields = ("File","Similarity")
    f = open('Results/faceSearch.csv', 'rb')
    reader = csv.DictReader(f, fields)
    i = 0
    j = 0
    k = 0
    #result_data = []
    for row in reader:
#        if i == 0:
#	    i == 1
#	elif i != 0:    
 #       print row
#	result_data.append(row)
#	print row
	if i == 0:
            i = 1
        elif i!=0:
            similarity.append(100*float(row["Similarity"]))
	    files.append(row["File"].replace("/home/dev/blackadder/",""))
            #j += 1
    #for x in xrange(1,15):
    #    files.append("/static/faceDB/"+str(x)+".jpg")
    result_data = []
    for i,j in zip(similarity,files):
        result_data.append({"Similarity":i,"File":j})
    #result_data = collections.OrderedDict(sorted(result_data.items(), reverse=True))
    #return render_template('results.html', r = result_data, uploaded = filename)
    def extract_similarity(json):
	try:
	    return float(json['Similarity'])
	except KeyError:
	    return 0

    result_data.sort(key=extract_similarity, reverse=True)
    #print result_data
    RecogResults = json.dumps(result_data)
    TopResult = json.loads(RecogResults)[0]
    MaxHitImage = TopResult["File"]
    print MaxHitImage
    #faces = db.faces
    user = faces.find_one({ "FaceList" :  MaxHitImage})
    if(user):
	print int(round(time.time() * 1000)) - startTime 
	print user["Name"]
        return json.dumps(user, default = json_util.default)
    print int(round(time.time() * 1000)) - startTime
    return ""

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',threaded=True,use_reloader=True)
