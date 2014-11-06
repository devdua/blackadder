#!/usr/bin/python
from flask import Flask
import os, subprocess, csv, string

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/run', methods=['GET'])
def runface():
    #recogsearch = ['br' ,'-algorithm', 'FaceRecognition', '-compare' ,'/home/acl/cloudlet/faceDB/male1.jpg' ,'/home/acl/cloudlet/faceDB/female1.jpg' ,'/home/acl/cloudlet/Results/results.csv']
    enroll = ['br' ,'-algorithm', 'FaceRecognition', '-enrollAll' ,'-enroll', '/home/acl/cloudlet/faceDB' ,'/home/acl/cloudlet/faceGal.gal']
    recogsearch = ['br' ,'-algorithm', 'FaceRecognition', '-compare' ,'/home/acl/cloudlet/faceGal.gal' ,'/home/acl/cloudlet/faceDB/male1.jpg' ,'/home/acl/cloudlet/Results/faceSearch.csv']
    p = subprocess.Popen(enroll)
    p.wait()
    p = subprocess.Popen(recogsearch)
    p.wait()
    similarity = [0.0,0.0,0.0,0.0]
    with open('/home/acl/cloudlet/Results/faceSearch.csv', 'rb') as f:
        reader = csv.reader(f)
	i = 0
    	for row in reader:
		if i != 0:
        	    for j in range(1, 5):
        	    	similarity[j-1] = 100*float(row[j])
		i = 1
    return str(similarity)
    
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
