#!/usr/bin/python
import os, subprocess, csv, string, collections
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename

app = Flask(__name__,static_folder='static')

app.config['UPLOAD_FOLDER'] = 'static/uploads/'
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