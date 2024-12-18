 	
<?php	 	 
	// turn on error reporting
	error_reporting(E_ALL ^ E_NOTICE);
	ini_set('display_errors', true); 

	
	include 'includes/utils.php';			// utils.php: database connection/disconnect functiosn
		
	// is this a POST if so, grab the POST varibales which are used to populate the search parameters.
	$isPost = ($_SERVER['REQUEST_METHOD'] == 'POST');
 	

	if ($isPost) {
                $ssid = $_POST["SSID"];
                $password = $_POST["PASSWORD"];
                echo 'sudo ./setwifi.sh "' . $ssid . '" "' .$password . '"<br>';
                exec('sudo ./setwifi.sh "' . $ssid . '" "' .$password . '"', $rets, $ret);
                echo "Setting wifi to " . $ssid. " returned " . $ret . "<br>";
                foreach ($rets as $r) {
                    echo $r;
                }

	}

?>


<!DOCTYPE html>
<html>
	<head>
		<meta charset="UTF-8">
		<title>Configure El3ktra Wifi</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
	</head>

	<body>


		<form action="" method="POST">
			<table>
                        <tr><td>WIFI Network:</td><td><select name="SSID">'
<?php 

               exec("sudo ./listwifi.sh", $networks, $ret);
               $wifis = [];
               foreach ($networks as $line) {
                   if (preg_match('/SSID: ([^"]+)/', $line, $ssid)) {
                       echo $ssid[0];
                       echo $ssid[1];
                       array_push($wifis, $ssid[1]);
                }
               }
               sort($wifis);
               $wifis = array_unique($wifis);
		foreach ($wifis as $wifi) {
                	echo '<option value="'.$wifi.'">'.$wifi. '</option>';
 		}
?>
                </select></td></tr>
                <tr><td>Password:</td><td><input type="passwordd" name="PASSWORD"></td></tr>
                </table>
		<input type="submit" value="Set"/>
		</form>
	</body>
</html>
