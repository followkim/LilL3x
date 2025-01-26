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
		$trainingFile =sizeof(array_keys($_GET))>0?"AI_".array_keys($_GET)[0]."_convo.dat":"AI_El3ktra_convo.dat";

		if (isset($_POST)) {
			WriteTrainingData($_POST, TRAINING_PATH . $trainingFile);
		}

		echo "<body><table >";
		echo "<center><b><h1>Train ".gethostname()."</b></h1></center>";
		echo '<form action="" method="POST">';
		echo "<tr><td width='50%'><center><b>User Input</b></center></td><td width='50%'><center><b>AI Response</b></center></td><td><center><b>Delete?</b></center></td></tr>";
		PrintTrainingData(TRAINING_PATH . $trainingFile);

		echo "</table>";
		echo '<input type="submit" value="Set"/></form>';
		echo '<p><a href="../index.php">Back to main page</a></body>';
	}

	function PrintTrainingData($trainingPath) {
		$myfile = fopen($trainingPath, "r") or die("Unable to open file!");
		$lineNum = 0;
		while(!feof($myfile)) {
			$line = fgets($myfile);
			$atts = explode('|', $line);
			if (sizeof($atts)>=2) {
				$prompt= $atts[0];
				$resp = $atts[1];
				
//				$dt = $atts[2];
				echo '<td word-break: break-all  >'.$prompt.'</td>';
				echo '<td ><textarea cols="100" rows="5" name="Line'.$lineNum.'" />'.$resp.'</textarea></td>';
				echo '<td align="center" ><input type="checkbox" id="vehicle1" name="Del'.$lineNum.'" ></td></tr>';
			}
			$lineNum = $lineNum + 1;

		}
		fclose($myfile);
	}

	function WriteTrainingData($post, $trainingPath) {

		// read current train file
		$myfile = file($trainingPath) ;

		foreach($post as $key => $value) {
			if (preg_match_all("/Line(.*)/", $key, $matches)) {
		  		$lineNum = (int)$matches[1][0];
				if (isset($myfile[$lineNum])) {
					$user = explode("|", $myfile[$lineNum]);
	                                $value = preg_replace('/\s+/', ' ', trim($value));
	                                $myfile[$lineNum] = $user[0] . "|" . $value."\n";
					echo "Set line " . $lineNum . "\n";
				} else {
					echo "ERR: line ".$lineNum." not set!";
				}
			} else if (preg_match_all("/Del(.*)/", $key, $matches)) {
		  		$lineNum = (int)$matches[1][0];
				if (isset($myfile[$lineNum])) {
					unset($myfile[$lineNum]);
					echo "Deleted line " . $lineNum . "\n";
				} else {
					echo "ERR: line ".$lineNum." not set!";
				}
			}
		}
                file_put_contents($trainingPath, $myfile);
	}


?>
