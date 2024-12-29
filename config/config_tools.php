<?php 	


	// turn on error reporting
	error_reporting(E_ALL ^ E_NOTICE);
	ini_set('display_errors', true); 

        include '/home/el3ktra/LilL3x/config/html/includes/utils.php';                   // utils.php: database connection/disconnect functiosn
 	

	const CONFIG_FILE =  "/home/el3ktra/LilL3x/config/config.txt";
	const CONFIG_DD =  "/home/el3ktra/LilL3x/config/config_dd.txt";

        function PrintIndex() {
	  echo "<head>";
	  echo " <title>El3ktra</title>";
	  echo '  <meta name="viewport" content="width=device-width, initial-scale=1">';
	  echo "</head>";
	  echo "<body> <p>";
          echo '<h1>Welcome to El3ktra!</h1>';
	  echo ' <a href="wifi.php">Set Wifi</a><br>';
	  echo ' <a href="config.php">configure</a><br>';
	  echo ' <a href="config_dev.php">configure (Developer Version)</a><br>';
	  echo '</body></html>';

        }

	function WriteConfig($post, $configFilePath=CONFIG_FILE) {
		// read current config file
		$myfile = fopen($configFilePath, "r") or die("Unable to open file!");
		$config_new = "";
		while(!feof($myfile)) {
			$line = fgets($myfile);
			$att = explode('|', $line);
	                if (count($att) > 2 ) {
                                $val =  array_key_exists($att[0], $post) ? $post[$att[0]] : $att[1];
     				$config_new = $config_new . $att[0] . '|' . preg_replace("~[\r]~", "", trim($val));
				for($i=2; $i < count($att); $i++) {
					$config_new = $config_new . '|' . $att[$i] ;
				}
			}
		}
		fclose($myfile);

        // write to the new config file
		$myfile = fopen(CONFIG_FILE, "w") or die("Unable to open file!");
		fwrite($myfile, $config_new);
		fclose($myfile);
	}


        function LoadConfig($configFilePath=CONFIG_FILE) {
	        // laod the data dictionary
	        $value_dict = [];
		$configf = fopen($configFilePath, "r") or die("Unable to open file!");
		while(!feof($configf)) {
			$line = fgets($configf);
			$att = explode('|', $line);
			if (count($att) > 2 ) {
				$e = array($att[1], $att[2]);
				$value_dict[$att[0]] = $e;
				// echo $value_dict[$att[0]][0]."|".$value_dict[$att[0]][1] . "";
			}
		}
		fclose($configf);
		return $value_dict;
	}

	function Print_AI_ENGINE($label, $name, $value, $desc="") {
		echo "<tr><td id='leftHand'><b>".$label.":</b></td>";
		echo "<td id='rightHand' >";
		echo "<select name=\"".$name."\" value=".$value.">\n";
	
		foreach (scandir('/home/el3ktra/LilL3x/beings') as $file) {
			if (preg_match("/^AI_[A-Z]/", $file)) {
				$pyfile = fopen('/home/el3ktra/LilL3x/beings/'.$file, "r");
				while(!feof($pyfile)) {
					$line = fgets($pyfile);
					if (preg_match_all("/class AI_([A-Z])(.*)\(/", $line, $matches)) {
						$ai_engine = $matches[1][0].$matches[2][0];
						echo "<option value=\"" . $ai_engine . "\" "  .   (($ai_engine == $value)?"selected":"") . ">" . $ai_engine ."</option>";
					}
				}
				fclose($pyfile);
			} // preg_match filename                                                                      
		}
		if ($desc!="") echo "</select></td></tr><tr><td></td><td><i>".$desc."</i></td></tr>";
		else echo "</select></td></tr>";
	}

	function Print_LISTEN_ENGINE($label, $name, $value, $desc="") {
		echo "<tr><td id='leftHand'><b>".$label.":</b></td>";
		echo "<td id='rightHand' >";
		echo "<select name=\"".$name."\" value=".$value.">";
		$pyfile = fopen('/home/el3ktra/LilL3x/sr.py', "r");
		$engines = [];
		while(!feof($pyfile)) {
			$line = fgets($pyfile);
			if (preg_match_all("/def recognize_(.*)\(self/", $line, $matches)) {
				array_push($engines, $matches[1][0]);
			}
			elseif (preg_match_all("/Recognizer.recognize_(.*) = /", $line, $matches)) {
				array_push($engines, $matches[1][0]);
			}
		}
		sort($engines);
		$engines = array_unique($engines);
		foreach ($engines as $engine) {
			echo "<option value=\"" . $engine . "\" "  .   (($engine == $value)?"selected":"") . ">" . $engine ."</option>";
		}
		if ($desc!="") echo "</select></td></tr><tr><td></td><td><i>".$desc."</i></td></tr>";
		else echo "</select></td></tr>";
	}

	function Print_SPEECH_ENGINE($label, $name, $value, $desc="") {
		echo "<tr><td id='leftHand'><b>".$label.":</b></td>";
		echo "<td id='rightHand' >";
		echo "<select name=\"".$name."\" value=".$value.">";
		$pyfile = fopen('/home/el3ktra/LilL3x/speech_tools.py', "r");
		while(!feof($pyfile)) {
			$line = fgets($pyfile);
			if (preg_match_all("/class (.*)_tts:/", $line, $matches)) {
			$engine = $matches[1][0];
			echo "<option value=\"" . $engine . "\" "  .   (($engine == $value)?"selected":"") . ">" . $engine ."</option>";
			}
		}
		if ($desc!="") echo "</select></td></tr><tr><td></td><td><i>".$desc."</i></td></tr>";
		else echo "</select></td></tr>";

	}

	function Print_DEBUG($label, $name, $value, $desc="") {
		echo "<tr><td id='leftHand'><b>".$label.":</b></td>";
		echo "<td id='rightHand' >";
		echo "<select name=\"".$name."\" value=".$value.">";
		$pyfile = fopen('/home/el3ktra/LilL3x/error_handling.py', "r");
		while(!feof($pyfile)) {
			$line = fgets($pyfile);
			if (preg_match_all("/(.*): \"(.*)\"/", $line, $matches)) {
				$val = $matches[1][0];
				$level = $matches[2][0];
				echo "<option value=\"" . $val . "\" "  .   (($val == $value)?"selected":"") . ">" . $level ."</option>";
			}
		}
		if ($desc!="") echo "</select></td></tr><tr><td></td><td><i>".$desc."</i></td></tr>";
		else echo "</select></td></tr>";
	}

	function Print_AINAMEP($label, $name, $value, $desc="") {
		echo "<tr><td id='leftHand'><b>".$label.":</b></td>\n";
		echo "<td id='rightHand' >\n";
		echo "<select name=\"".$name."\" value=".$value.">\n";
		foreach (scandir('/home/el3ktra/LilL3x/wake') as $file) {
			if (preg_match_all("/^([a-z ]*)_.*\.ppn/", str_replace('-', ' ', $file), $matches)) {
				$wake_word = ucwords($matches[1][0]);
				$filepath = '/home/el3ktra/LilL3x/wake/'.$file;
				echo "<option value=\"" . $filepath  . "\" " . (($filepath == $value)?"selected":"") . ">" . $wake_word . "</option>";
	} 
		}
  		if ($desc!="") echo "</select></td></tr><tr><td></td><td><i>".$desc."</i></td></tr>";
		else echo "</select></td></tr>";
	}

	function PrintConfig($configFilePath=CONFIG_FILE, $configDDPath=CONFIG_DD) {
		$value_dict = LoadConfig($configFilePath);
		$myfile = fopen($configDDPath, "r") or die("Unable to open file!");
		while(!feof($myfile)) {
			$line = fgets($myfile);
			$atts = explode('|', $line);
			if (preg_match("/^[a-zA-Z]/", $atts[0])) {
                               if (in_array($atts[0], array("AI_ENGINE", "AINAMEP", "LISTEN_ENGINE", "SPEECH_ENGINE", "DEBUG"))) {
                                        eval("Print_".$atts[0]."(\$atts[1], \$atts[0], \$value_dict[\$atts[0]][0], \$atts[2]);");
				} else {
					if ($value_dict[$atts[0]][1] == "blob") {
						echo "<tr><td id=\"leftHand\"><b>" .$atts[1]. ":</b></td>";
						echo '<td id="rightHand"><textarea cols="40" rows="5" name="'.$atts[0].'" />'.$value_dict[$atts[0]][0].'</textarea></td></tr>';
					} elseif ($value_dict[$atts[0]][1] == "int") {
						echo "<tr><td id=\"leftHand\"><b>" .$atts[1]. ":</b></td>";
						echo '<td id="rightHand"><input size="15" type="0" name="'.$atts[0].'" value="'.$value_dict[$atts[0]][0].'" ></td></tr>';
					} else {
						echo "<tr><td id=\"leftHand\"><b>" .$atts[1]. ":</b></td>";
						echo '<td id="rightHand"><input size="15" type="0" name="'.$atts[0].'" value="'.$value_dict[$atts[0]][0].'" ></td></tr>';
					}
					echo "<tr><td></td><td><i>".$atts[2]."</i></td></tr>";
				}
			}
		}
		fclose($myfile);
	}

	function PrintConfigDev($configFilePath=CONFIG_FILE) {
		$myfile = fopen($configFilePath, "r") or die("Unable to open file!");
		while(!feof($myfile)) {
			$line = fgets($myfile);
			$atts = explode('|', $line);
			if (preg_match("/^[a-zA-Z]/", $atts[0])) {
				if (in_array($atts[0], array("AI_ENGINE", "AINAMEP", "LISTEN_ENGINE", "SPEECH_ENGINE", "DEBUG"))) {
					eval("Print_".$atts[0]."(\$atts[0], \$atts[0], \$atts[1]);");
				} else {
					if ($atts[2] == "blob") {
						echo "<tr><td id=\"leftHand\"><b>" . $atts[0] . "</b></td>";
						echo '<td id="rightHand"><textarea cols="40" rows="5" name="'.$atts[0].'" />'.$atts[1].'</textarea></td></tr>';
					} elseif ($atts[2] == "int") { 
						echo trd_labelData($atts[0], $atts[1], $atts[0], 0, "number");
					} else {
						echo trd_labelData($atts[0], $atts[1], $atts[0]);
					}
				}
			}
		}
		fclose($myfile);
	}
?>
