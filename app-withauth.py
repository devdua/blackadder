#!/usr/bin/python
import datetime
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from pymongo import MongoClient
import os, subprocess, csv, string, collections
from flask import Flask, abort, jsonify, render_template, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename

app = Flask(__name__,static_folder='static')

app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])
client = MongoClient('mongodb://dev-blackadder:blackadder1234@ds056727.mongolab.com:56727/blackadder?authMechanism=MONGODB-CR')
db = client.blackadder
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
@auth.login_required
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
    enroll = ['br' ,'-algorithm', 'FaceRecognition', '-enrollAll' ,'-enroll', '/home/acl/cloudlet/static/faceDB' ,'/home/acl/cloudlet/faceGal.gal']
    recogsearch = ['br' ,'-algorithm', 'FaceRecognition', '-compare' ,'/home/acl/cloudlet/static/uploads/'+filename , '/home/acl/cloudlet/faceGal.gal', '/home/acl/cloudlet/Results/faceSearch.csv']
    p = subprocess.Popen(enroll)
    p.wait()
    p = subprocess.Popen(recogsearch)
    p.wait()
    similarity = [0.0]*10
    files = []
    f = open('/home/acl/cloudlet/Results/faceSearch.csv', 'rb')
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
    for x in xrange(1,11):
        files.append("/static/faceDB/"+str(x)+".jpg")
    result_data = {}
    for i,j in zip(similarity,files):
        result_data[i] = j
    result_data = collections.OrderedDict(sorted(result_data.items(), reverse=True))
    return render_template('results.html', r = result_data, uploaded = filename)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',threaded=True)
