<?php
session_start();
// Connection credentials.
$DATABASE_HOST = 'localhost';
$DATABASE_USER = 'u191905341_crops_user';
$DATABASE_PASS = 'Crops_user27';
$DATABASE_NAME = 'u191905341_crops';
// Try and connect using the info above.
$conn = new mysqli($DATABASE_HOST, $DATABASE_USER, $DATABASE_PASS, $DATABASE_NAME);
// Check connection
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