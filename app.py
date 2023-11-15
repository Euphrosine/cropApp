from flask import Flask, render_template, request, redirect, url_for, flash,session,jsonify
from flask_mysqldb import MySQL
import hashlib
import MySQLdb.cursors
import matplotlib.pyplot as plt
import io
import base64
import json
import re
import pandas as pd
import numpy as np
import sklearn
import os
import pickle
import warnings
import csv

app = Flask(__name__)

#Secure the session data saved in browser
app.secret_key = 'many random bytes'
#Start database connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'crops'
mysql = MySQL(app)
#End database connection

#1 Start login application          
@app.route('/Login',methods=['POST','GET'])
def Login():
    msg=""
    if request.method == "POST" and 'username' in request.form and 'password' in request.form:
        username= request.form['username']
        password= request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM accounts WHERE username = %s AND password= %s", (username, password))
        record=cursor.fetchone()
        if record:
            session['loggedin'] = True
            session['id'] = record[0]
            session['username'] = record[1]
            return redirect(url_for('home'))
            #return render_template('home.html')
        else:
            msg = 'Incorrect username or password. Please try again!'
            return render_template('index.html', display=msg)
#1 End login application 

#2 Start logout application
@app.route('/Logout')
def Logout():
    session.pop('loggedin',None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('index'))
#2End logout application

#3 Start default applicataion
@app.route('/')
def index():
    return render_template('index.html')
#3 End default applicataion

#4 Start user registration application
@app.route('/register', methods = ['POST'])
def registerUser():

    if request.method == "POST":
        flash("User created successfully")
        fullname = request.form['fullname']
        phone = request.form['phone']
        email = request.form['email']
        device = request.form['device']
        username = request.form['username']
        password = request.form['password']
        #encypted_password = hashlib.sha256(password.encode()).hexdigest()
        #image = request.files['image']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO accounts (fullname, phone, email, device, username,password) VALUES (%s, %s, %s, %s, %s, %s)", (fullname, phone, email, device, username,password))
        mysql.connection.commit()
        return redirect(url_for('register'))

@app.route('/register')
def register():
    return render_template('register.html')  
#4 End registration application

#5 Start home application
@app.route('/home')
def home():
    username = session.get('username')
    logged_in = username is not None
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM readings")
    data = cursor.fetchall()
    cursor.close()
    num_readings = len(data)
    averages = []
    total_average = {  # Initialize total_average with default values
        'average_temperature': 0.0,
        'average_humidity': 0.0,
        'average_nitrogen': 0.0,
        'average_phosphorous': 0.0,
        'average_potassium': 0.0,
        'average_pH': 0.0,
        'reading_time': None,
    }
    sub_averages = []  # Store sub-averages

    for i in range(0, num_readings, 3):
        average_date = data[i][6]
        sum_temperature = sum(float(row[1]) for row in data[i:i+3])
        sum_humidity = sum(float(row[2]) for row in data[i:i+3])
        sum_nitrogen = sum(float(row[3]) for row in data[i:i+3])
        sum_phosphorous = sum(float(row[4]) for row in data[i:i+3])
        sum_potassium = sum(float(row[5]) for row in data[i:i+3])
        sum_pH = sum(float(row[6]) for row in data[i:i+3])

        average_temperature = sum_temperature / 3
        average_humidity = sum_humidity / 3
        average_nitrogen = sum_nitrogen / 3
        average_phosphorous = sum_phosphorous / 3
        average_potassium = sum_potassium / 3
        average_pH = sum_pH / 3

        averages.append({
            'average_temperature': average_temperature,
            'average_humidity': average_humidity,
            'average_nitrogen': average_nitrogen,
            'average_phosphorous': average_phosphorous,
            'average_potassium': average_potassium,
            'average_pH': average_pH,
            'reading_time': average_date
        })

        # Check if we have accumulated seven sub-averages
        if len(averages) == 7:
            # Calculate the total average for the seven sub-averages
            total_average = {
                'average_temperature': round(sum(average['average_temperature'] for average in averages) / 7, 3),
                'average_humidity': round(sum(average['average_humidity'] for average in averages) / 7, 3),
                'average_nitrogen': round(sum(average['average_nitrogen'] for average in averages) / 7, 3),
                'average_phosphorous': round(sum(average['average_phosphorous'] for average in averages) / 7, 3),
                'average_potassium': round(sum(average['average_potassium'] for average in averages) / 7, 3),
                'average_pH': round(sum(average['average_pH'] for average in averages) / 7, 3),
                'reading_time': average_date,
            }
            
            # Insert sub-averages into the subaverage table
            for sub_average in averages:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO subaverage(temperature, humidity,nitrogen, phosphorous, potassium,  pH) VALUES (%s, %s, %s, %s, %s, %s)",
                               (sub_average['average_temperature'], sub_average['average_humidity'], sub_average['average_nitrogen'],sub_average['average_phosphorous'], sub_average['average_potassium'],  sub_average['average_pH']))
                conn.commit()
                cursor.close()

            # Insert total average into the average_readings table
            cursor = conn.cursor()
            cursor.execute("INSERT INTO average_readings(temperature, humidity,nitrogen, phosphorous, potassium,  pH) VALUES (%s, %s, %s, %s, %s, %s)",
                           (total_average['average_temperature'], total_average['average_humidity'], round(float(total_average['average_nitrogen'])/1000000*2000000,3), round(float(total_average['average_phosphorous'])/1000000*2000000,3), round(float(total_average['average_potassium'])/1000000*2000000,3),  total_average['average_pH']))
            conn.commit()
            cursor.close()

            sub_averages.append(averages)
            averages = []  # Reset the sub-averages for the next group of seven

    # Application to insert Total average into the database/average_readings table
    if 'loggedin' in session:
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT reading_time, temperature, humidity,nitrogen, phosphorous, potassium,  pH FROM average_readings ORDER BY reading_time DESC limit 1 ")
        avg = cursor.fetchall()
        mysql.connection.commit()

    # Fetch recommendation data from the database
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT crop_name, rank, probability, rec_time FROM recommendation ORDER BY rec_time DESC limit 8 ")
        recommendation_data = cursor.fetchall()
        cursor.close()

        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM average_readings ORDER by reading_time DESC limit 1")
        average_temperature = cursor.fetchone()[1]
        cursor.close()

        return render_template('home.html', recommendation_data=recommendation_data,  averages=averages, total_average=total_average,date=average_date,username=username, logged_in=logged_in, avg=avg, average_temperature=average_temperature,)
    else:
        return redirect(url_for('index'))
# End home application

#6 Application to delete average_readings
@app.route('/delete_avg/<string:id_data>', methods = ['GET'])
def delete_avg(id_data):
    flash("Record has been successfully deleted ")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM average_readings WHERE id=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('display_average'))
#6 Application to delete average_readings in database

#7 Application to display total average into prediction pannel       
@app.route('/predict')
def display_average():
    if 'loggedin' in session:
         username = session.get('username')
         logged_in = username is not None
         conn = mysql.connection
         cursor = conn.cursor()
         cursor.execute("SELECT * FROM average_readings ORDER by reading_time DESC limit 4")
         data = cursor.fetchall()
         cursor.close()
         return render_template('prediction.html', username=username, logged_in=logged_in,total_average=data)
    else:
        return redirect(url_for('index')) 

#7 End application to display total average into prediction pannel 

#8 Sart prediction application

# Load the ML model
model_path = 'MymodelRF_Rank.pkl'
with open(model_path, 'rb') as model_file:
    rdf_model = pickle.load(model_file)
# End model loading

# Start create the crop dictionary
my_dict = {
    'rice': 1,
    'maize': 2,
    'coconut': 3,
    'papaya': 4,
    'orange': 5,
    'watermelon': 6,
    'mango': 7,
    'banana': 8,
}
# End creating the crop dictionary
#prediction app
def select_crops(N, P, K, temperature, humidity, ph):
    input_values = np.array([[N, P, K, temperature, humidity, ph]])
    predictions = rdf_model.predict_proba(input_values)[0]
    return predictions
@app.route('/predict', methods=['POST'])
def predict():
    if 'loggedin' in session:
         username = session.get('username')
         logged_in = username is not None
         #Get soil and weather features by post method
         N = float(request.form['Nitrogen'])
         P = float(request.form['Phosporus'])
         K = float(request.form['Potassium'])
         temperature = float(request.form['Temperature'])
         humidity = float(request.form['Humidity'])
         ph = float(request.form['pH'])
        # Get predicted probabilities for all crops
         predictions = select_crops(N, P, K, temperature, humidity, ph)
        # Create a list of crops and their predicted probabilities
         crops = list(my_dict.keys())
         crop_probabilities = list(zip(crops, predictions))
        # Sort crops by probability in descending order
         sorted_crops = sorted(crop_probabilities, key=lambda x: x[1], reverse=True)
        # Prepare recommendation rank data for insertion
         recommendation_data = [(crop_name, rank + 1, probability) for rank, (crop_name, probability) in enumerate(sorted_crops[:8])]
        # Insert recommendation ranks into the database
         conn = mysql.connection
         cursor = conn.cursor()
         cursor.executemany("INSERT INTO recommendation (crop_name, rank, probability) VALUES (%s, %s, %s)", recommendation_data)
         conn.commit()
         cursor.close()
         conn = mysql.connection
         cursor = conn.cursor()
         cursor.execute("SELECT * FROM average_readings ORDER by reading_time ASC limit 2")
         data = cursor.fetchall()
         cursor.close()

         # Fetch recommendation data from the database
         conn = mysql.connection
         cursor = conn.cursor()
         cursor.execute("SELECT crop_name, rank, probability, rec_time FROM recommendation ORDER BY rec_time DESC limit 8 ")
         recommendation_data = cursor.fetchall()
         cursor.close()
         return render_template('prediction.html', sorted_crops=sorted_crops[:8],username=username, logged_in=logged_in,total_average=data,recommendation_data= recommendation_data)
    else:
        return redirect(url_for('index')) 
#8 End prediction application

#9 Start tabular data view application
@app.route('/sensor_table')
def sensor_table():
     if 'loggedin' in session:
         username = session.get('username')
         logged_in = username is not None
         cur = mysql.connection.cursor()
         query = "SELECT * FROM readings;"
         cur.execute(query)
         data = cur.fetchall()
         cur.close()
    
         return render_template('sensor_data.html',data=data,username=username, logged_in=logged_in, )
     else:
        return redirect(url_for('index'))
#9 End tabular data view application

#9 Start tabular data view application
@app.route('/sub_average')
def sub_average():
     if 'loggedin' in session:
         username = session.get('username')
         logged_in = username is not None
         cur = mysql.connection.cursor()
         query = "SELECT * FROM subaverage;"
         cur.execute(query)
         data = cur.fetchall()
         cur.close()
         # Convert the data to floats
         data = [tuple(float(val) if val is not None and str(val).replace(".", "", 1).isdigit() else val for val in row) for row in data]
         return render_template('sub_average.html',data=data,username=username, logged_in=logged_in, )
     else:
        return redirect(url_for('index'))
#9 End tabular data view application

#9 Start tabular data view application
@app.route('/total_average')
def total_average():
     if 'loggedin' in session:
         username = session.get('username')
         logged_in = username is not None
         cur = mysql.connection.cursor()
         query = "SELECT * FROM  average_readings;"
         cur.execute(query)
         data = cur.fetchall()
         cur.close()
    
         return render_template('total_average.html',data=data,username=username, logged_in=logged_in, )
     else:
        return redirect(url_for('index'))
#9 End tabular data view application

#10 Application to delete sensor data
@app.route('/delete/<string:id_data>', methods = ['GET'])
def delete(id_data):
    flash("Record has been successfully deleted ")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM readings WHERE id=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('predict'))
#10 End pplication to delete sensor data 

#11 Start user profile pplication 
@app.route('/profile')
def profile():
    if 'loggedin' in session:
         username = session.get('username')
         logged_in = username is not None
    if 'loggedin' in session:
         conn = mysql.connection
         cursor = conn.cursor()
         cursor.execute('SELECT * FROM accounts WHERE id = % s', (session['id'], ))
         account = cursor.fetchone()
         return render_template('profile.html',username=username, logged_in=logged_in,account=account)
    else:
         return redirect(url_for('index'))  
#11 End user profile pplication

#Application to update data in database
@app.route('/update',methods=['POST','GET'])
def update():

    if request.method == 'POST':
        id_data = request.form['id']
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        device = request.form['device']
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute(""" UPDATE accounts SET fullname=%s, phone=%s, email=%s, device =%s, username=%s, password=%s WHERE id=%s
            """, (name, phone, email, device, username, password,  id_data))
        flash("Data Updated Successfully")
        mysql.connection.commit()
        return redirect(url_for('profile'))
 #Excute main application

#9 Start tabular data view application
@app.route('/device')
def device():
     if 'loggedin' in session:
         username = session.get('username')
         logged_in = username is not None
         return render_template('device_info.html',username=username, logged_in=logged_in,)
     else:
        return redirect(url_for('index'))
#9 End tabular data view application

#9 Start tabular data view application
@app.route('/field')
def field():
     if 'loggedin' in session:
         username = session.get('username')
         logged_in = username is not None
         return render_template('field_info.html',username=username, logged_in=logged_in,)
     else:
        return redirect(url_for('index'))
#9 End tabular data view 


@app.route('/data_insertion', methods=['POST'])
def insert_data():
    if 'loggedin' in session:
        username = session.get('username')
        logged_in = username is not None
    if request.method == "POST":
        flash("Data inserted successfully")
        temperature = request.form['temperature']
        humidity = request.form['humidity']
        nitrogen = request.form['nitrogen']
        phosphorous = request.form['phosphorous']
        potassium = request.form['potassium']
        pH = request.form['pH']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO testing (temperature, humidity, nitrogen, phosphorous, potassium,pH) VALUES (%s, %s, %s, %s, %s, %s)", (temperature, humidity, int(nitrogen)/1000000*4200000, int(phosphorous)/1000000*4200000, int(potassium)/1000000*4200000, pH))
        mysql.connection.commit()
        return redirect(url_for('data_insertion'))
    else:
        return redirect(url_for('index'))

@app.route('/data_insertion')
def data_insertion():
     if 'loggedin' in session:
         username = session.get('username')
         logged_in = username is not None

         return render_template('insert_data.html')
     else:
        return redirect(url_for('index'))    
        
        
@app.route('/insert_sensor_data', methods=['POST'])
def insert_sensor_data():
    data = request.json

    temperature = data.get('temperature')
    humidity = data.get('humidity')
    nitrogen = data.get('nitrogen')
    phosphorous = data.get('phosphorous')
    potassium = data.get('potassium')
    pH = data.get('pH')

    try:
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("INSERT INTO readings (temperature, humidity, nitrogen, phosphorous, potassium, pH) VALUES (%s, %s, %s, %s, %s, %s)",
                       (temperature, humidity, nitrogen, phosphorous, potassium, pH))
        conn.commit()
        cursor.close()
        return jsonify({"message": "Data inserted successfully"}), 201
    except Exception as e:
        return jsonify({"message": "Error: " + str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)