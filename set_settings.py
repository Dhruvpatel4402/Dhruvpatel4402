import os.path
from flask import Flask, render_template, url_for, request, redirect, flash
import json
import subprocess
import sys
from flask import Response
from flask import Flask, request, Response
from flask import Flask, request, jsonify

from flask_sqlalchemy import SQLAlchemy
import subprocess
from sqlalchemy import Date, Time, VARCHAR
import csv  # Adding the 'csv' module import


app = Flask(__name__)


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:dhruvpatel123@localhost:3306/python' # give another db user name,password,host(server),databasename to store data.
app.secret_key = "DIVtaI3pedN0g0OP5Gt9FXviXnVI1DF1"

db = SQLAlchemy(app)

class CsvTable(db.Model):
    __tablename__ = 'data'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(Date)
    time = db.Column(Time)
    img_path = db.Column(VARCHAR(255))

default_settings = {
    "Model": "auto detection",
    "RTSP": "192.168.3.1",
    "Output Folder": "data",
    "CSV": "data/CSV/",
}
final_settings = {}


model_references = {
    "auto detection": "autorickshaw/detect.py",# auto rickshaw only detection when this model run.
    "all detection": "object/detect.py",#car,bus ,motercycle,bicycle etc detection  run when this model run.
    "annotation tool":"labelimg\labelImg-master\labelImg.py", # Anotation tool open when this model run.
    "split folder":"split_yolo.py" # set image and label path and also set class name 
         
}

def check_if_empty(settings):
    flag = 1
    for key, value in settings.items():
        if settings[key] == "":
            flag = 0
            settings[key] = default_settings[key]
    return settings, flag


@app.route("/",methods = ['GET','POST'])
def index():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        with open("users.json",'r') as f:
            data = json.load(f)
            if data["users"][username] == password:
                return render_template("settings.html")
            else:
                flash("Credentials don't match, Check Username and Password")
                return render_template("index.html")
    else:
        return render_template("index.html")# username= admin and password= admin

        

@app.route("/login", methods=["GET", "POST"]) # the parameter giving model, rtsp,output folder and csv path
def set_settings():
    if request.method == "POST":
        settings = request.form
        settings = settings.to_dict()
        settings, flag = check_if_empty(settings)
        if os.path.exists(settings["Output Folder"]) and os.path.exists(
            settings["CSV"]
        ):
            globals()["final_settings"] = settings
            if not flag:
                flash("Empty Parameters! Setting Default Values for them")
            return render_template("success.html", settings=settings)
        else:
            flash("Error in Setting Parameters")
            return render_template("settings.html")

    else:
        return render_template("settings.html") 


@app.route("/default") #set Default parameter if you want
def default():
    globals()["final_settings"] = default_settings
    flash("Setting Default Values")
    return render_template("success.html", settings=default_settings)


@app.route("/back")
def back():
    return render_template("settings.html", settings=final_settings)


@app.route("/confirm") #confirm the script 
def confirm():
    with open("config.json", "w") as f:
        json.dump(final_settings, f)

    return render_template("confirm.html", settings=final_settings)



@app.route("/run/")
def run():  
    if final_settings["Model"] in model_references:
        subprocess.call([sys.executable, model_references[final_settings["Model"]]])
    return render_template("confirm.html", settings=final_settings) # showing output and store data to their folder
    

    
@app.route("/get_csv/<db_name>/")
def get_csv(db_name):
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://root:dhruvpatel123@localhost:3306/csv{db_name}'
    db.create_all()

    try:
        with open("data/CSV/file.csv", "r") as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  

            for row in csv_reader:
                if len(row) >= 3:  
                    date = row[0]
                    time = row[1].replace('_', ':')  
                    img_path = row[2]
                    new_entry = CsvTable(date=date, time=time, img_path=img_path)
                    db.session.add(new_entry)
                else:
                    print(f"Issue with row: {row}")  

            db.session.commit()

        return "CSV data inserted into the database successfully"
    except Exception as e:
        return f"Error occurred: {str(e)}"
    

data_yaml = "data.yaml"
cfg_yaml = "yolov5s.yaml"
weights = "yolov5s.pt"
train_script = "train.py" 
detect_script="detect.py"


@app.route('/train', methods=['POST'])
def train_model():
    img_size = request.json.get('img_size', 640)
    batch_size = request.json.get('batch_size', 10)
    epochs = request.json.get('epochs', 20)

    command = f"python train.py --img {img_size} --batch {batch_size} --epochs {epochs}"

    p1= subprocess.Popen(command, shell=True)
    p1.wait()
    
    return "Training started"


@app.route('/detect', methods=['POST'])
def detect_objects():
    image_source = request.json.get('source', 'validation_folder\images')  

    command = f"python detect.py --weights yolov5s.pt --source {image_source}"

    subprocess.Popen(command, shell=True)

    return "Object detection started"


if __name__ == "__main__":
    app.run(debug=True)  #default port is 5000
    


    # app.run(host='127.0.0.1', port=8080, threaded=True)
    


