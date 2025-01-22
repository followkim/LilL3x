<?php 	
	// turn on error reporting
	error_reporting(E_ALL ^ E_NOTICE);
	ini_set('display_errors', true);

	const TRAINING_PATH =  "/home/el3ktra/LilL3x/training/";


	function HTMLHead() {
	  echo "<head>";
	  echo " <title>".gethostname()."</title>";
	  echo '  <meta name="viewport" content="width=device-width, initial-scale=1">';
	  echo "</head>";
	}

	function PrintTraining() {
		$trainingFile =sizeof(array_keys($_GET))>0?array_keys($_GET)[0]:"AI_ChatGPT_trn.dat";
//		$trainingFile = file_exists($configFile)?$configFile:CONFIG_FILE;

//		if (isset($_POST)) {
//			if (count($_POST) > 0 ) {
//		            WriteConfig($_POST, $configFile);
//			}
//		}

		echo "<body><table>";
                echo "<center><b><h1>Train ".gethostname()."</b></h1></center>";
                echo '<form action="" method="POST">';

		PrintTrainingData(TRAINING_PATH . $trainingFile);

		echo "</table>";
                echo '<input type="submit" value="Set"/></form>';
                echo '<p><a href="index.php">Back to main page</a></body>';
	}

	function PrintTrainingData($trainingPath) {
		$myfile = fopen($trainingPath, "r") or die("Unable to open file!");
		while(!feof($myfile)) {
			$line = fgets($myfile);
			$atts = explode('|', $line);
			if (sizeof($atts)>=3) {
	                        $dt= $atts[0];
				$prompt = $atts[1];
				$resp = $atts[2];
				echo "<tr><td id=\"righthand\"><b>" . $dt . ":</b></td>";
				echo '<td word-break: break-all width=30%  id="lefthand">'.$prompt.'</td>';
				echo '<td id="rightHand"><textarea cols="40" rows="5" name="TBD" />'.$resp.'</textarea></td></tr>';
			}

		}
		fclose($myfile);
	}

?>
