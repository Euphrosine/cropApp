<?php
session_start();
// Connection credentials.
$DATABASE_HOST = 'mysql-153418-0.cloudclusters.net';
$DATABASE_USER = 'admin';
$DATABASE_PASS = 'admin123';
$DATABASE_NAME = 'crop';
// Try and connect using the info above.
$conn = new mysqli($DATABASE_HOST, $DATABASE_USER, $DATABASE_PASS, $DATABASE_NAME);
// Check connection
// 'ENGINE': 'django.db.backends.mysql',
// 'NAME': 'kitchenproject',
// 'USER': 'admin',
// 'PASSWORD': 'admin123',
// 'HOST': 'mysql-153418-0.cloudclusters.net',
// 'PORT': '19069',
if ($conn->connect_errno) {
    die("Connection failed: " . $conn->connect_error);
}

//Arduino variables";

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    //$deviceNo = $_POST['deviceNo'];
    $temperature = $_POST['temperature'];
    $humidity = $_POST['humidity'];
    $nitrogen = $_POST['nitrogen'];
    $phosphorous = $_POST['phosphorous'];
    $potassium = $_POST['potassium'];
    $pH = $_POST['pH'];
// Insert the data into your MySQL database here
    $sql = "INSERT INTO readings (temperature,humidity, nitrogen, phosphorous, potassium, pH) VALUES ($temperature, $humidity, $nitrogen, $phosphorous, $potassium, $pH )";

    if ($conn->query($sql) === TRUE) {
        echo "Data has been uploaded into the server successfully";
    } else {
        echo "Error: " . $sql . "<br>" . $conn->error;
    }

    $conn->close();
} else {
    echo "Invalid request method";
}

?>