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

//                $trainingFile = (isset($_POST) and array_key_exists($_POST["train_file"]))? $_POST["train_file"]: TRAINING_PATH . "AI_El3ktra_convo.dat";
                $trainingFile = TRAINING_PATH . "AI_El3ktra_convo.dat";

		if (isset($_POST)) {
//                        if (array_key_exists("train_file", $_POST)) {
//				$trainingFile = $_POST["train_file"];
//			} else {
				WriteTrainingData($_POST, $trainingFile);
//			}
		}

		echo "<body>";
		echo "<center><b><h1>Train ".gethostname()."</b></h1></center>";
		echo '<form action="" method="POST">';

                echo "<table><tr><td><b>Conversation File: </b></td>";
                echo "<td><select name='training_file'>";
                foreach (scandir(TRAINING_PATH) as $file) {
                        if (preg_match_all("/^AI_([A-Za-z1-9 ]*)_convo.dat$/", $file, $matches)) {
                                $ai_name = $matches[1][0];
                                $filepath = TRAINING_PATH.$file;
                                echo "<option value='" . $filepath  . "' >" . $ai_name . "</option>";
                        }
                }
                echo "</select></td></tr>";
                echo "<tr><td><i>Current File:</i></td><td>" . $trainingFile . "</td></tr></table>";
		echo '<input type="submit" value="Set"/><p></form>';


		echo '<form action="" method="POST">';
		echo "<table><tr><td width='50%'><center><b>User Input</b></center></td><td width='50%'><center><b>AI Response</b></center></td><td><center><b>Delete?</b></center></td></tr>";



		PrintTrainingData($trainingFile);

		echo "</table>";
		echo '<input type="submit" value="Set"/></form>';
		echo '<p><a href="../index.php">Back to main page</a></body>';
	}

	function PrintTrainingData($trainingPath) {
		$myfile = file($trainingPath) ;
		for ($linenum = count($myfile) - 1; $linenum >= 0; $linenum--) {
			$line = $myfile[$linenum];
			//$line = fgets($myfile);
			$atts = explode('|', $line);
			if (sizeof($atts)>=2) {
				$prompt= $atts[0];
				$resp = $atts[1];
				echo '<td word-break: break-all  >'.$prompt.'</td>';
				echo '<td ><textarea cols="100" rows="5" name="Line'.$linenum.'" />'.$resp.'</textarea></td>';
				echo '<td align="center" ><input type="checkbox" id="vehicle1" name="Del'.$linenum.'" ></td></tr>';
			}

		}
//		fclose($myfile);
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
				} else {
					echo "ERR: line ".$lineNum." not set!";
				}
			} else if (preg_match_all("/Del(.*)/", $key, $matches)) {
		  		$lineNum = (int)$matches[1][0];
				if (isset($myfile[$lineNum])) {
					unset($myfile[$lineNum]);
				} else {
					echo "ERR: line ".$lineNum." not set!";
				}
			}
		}
                file_put_contents($trainingPath, $myfile);
		chmod($trainingPath, 0664);
	}


?>
