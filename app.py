#!/usr/bin/python
import os, subprocess, csv, string
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['GET','POST'])
def runface():
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    enroll = ['br' ,'-algorithm', 'FaceRecognition', '-enrollAll' ,'-enroll', '/home/acl/cloudlet/faceDB' ,'/home/acl/cloudlet/faceGal.gal']
    recogsearch = ['br' ,'-algorithm', 'FaceRecognition', '-compare' ,'/home/acl/cloudlet/uploads/'+filename , '/home/acl/cloudlet/faceGal.gal', '/home/acl/cloudlet/Results/faceSearch.csv']
    p = subprocess.Popen(enroll)
    p.wait()
    p = subprocess.Popen(recogsearch)
    p.wait()
    similarity = [0.0,0.0,0.0,0.0]
    with open('/home/acl/cloudlet/Results/faceSearch.csv', 'rb') as f:
    	reader = csv.reader(f)
	i = 0
	j = 0
	for row in reader:
		if i == 0:
			i = 1
		else:
			similarity[j] = 100*float(row[1])
			j += 1

    return str(similarity)
    
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')