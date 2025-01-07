<?php 	
	// turn on error reporting
	error_reporting(E_ALL ^ E_NOTICE);
	ini_set('display_errors', true);
        include './utils.php';

	const CONFIG_PATH =  "/home/el3ktra/LilL3x/config/";
	const CONFIG_ROOT =  "config.txt";
	const CONFIG_DD =  CONFIG_PATH . "config_dd.txt";
	const CONFIG_FILE =  CONFIG_PATH . CONFIG_ROOT;


	function HTMLHead() {
	  echo "<head>";
	  echo " <title>".gethostname()."</title>";
	  echo '  <meta name="viewport" content="width=device-width, initial-scale=1">';
	  echo "</head>";
	}

        function PrintIndex() {
          HTMLHead();
	  echo "<body> <p>";
          echo '<h1>Welcome to '.gethostname().'</h1>';
	  echo ' <a href="wifi.php">Set Wifi</a><br>';
	  echo ' <a href="config.php">configure</a><br>';
	  echo ' <a href="config.php?txt">configure (Developer Version)</a><br>';
	  echo ' <a href="config.php?vars">configure variables (Developer Version)</a><br>';
	  echo '</body></html>';

        }

	function PrintConfig() {
		$configFile = str_replace("txt", (sizeof(array_keys($_GET))>0?array_keys($_GET)[0]:"txt"), CONFIG_FILE);
		$configFile = file_exists($configFile)?$configFile:CONFIG_FILE;

		if (isset($_POST)) {
			if (count($_POST) > 0 ) {
		            WriteConfig($_POST, $configFile);
			}
		}

		echo "<body><table>";
                echo "<center><b><h1>Configure ".gethostname()."</b></h1></center>";
                echo '<form action="" method="POST">';

		if (sizeof(array_keys($_GET))>0) PrintConfigDev($configFile);
		else PrintConfigPretty();

		echo "</table>";
                echo '<input type="submit" value="Set"/></form>';
                echo '<p><a href="index.php">Back to main page</a></body>';
	}

	function PrintConfigPretty($configFilePath=CONFIG_FILE, $configDDPath=CONFIG_DD) {
                $func_list = GetFuncList();
		$value_dict = LoadConfig($configFilePath);
		$myfile = fopen($configDDPath, "r") or die("Unable to open file!");
		while(!feof($myfile)) {
			$line = fgets($myfile);
			$atts = explode('|', $line);
			if (sizeof($atts)>=3) {
	                        $key= $atts[0];
				$label = $atts[1];
				$desc = $atts[2];
	                        $val = array_key_exists($key, $value_dict)?$value_dict[$key][0]:'';
	                        $type= array_key_exists($key, $value_dict)?trim($value_dict[$key][1]):'str';

				if (preg_match("/^[a-zA-Z]/", $key)) {
					if ($key=="HEADER") {
						PrintHEADER($label, (array_key_exists(2, $atts)?$desc:"2"));
					} elseif (preg_match("/[A-Z]*_LED/", $key)) {
						Print_LED($label, $key, $val, $desc);
					} elseif (in_array($key, $func_list)) {
						eval("Print_".$key."(\$label, \$key, \$val, \$desc);");
	                                } elseif (in_array($type, $func_list)) {
	                                        eval("Print_".$type."(\$label, \$key, \$val, \$desc);");
					} else {
						Print_other($label, $key, $val, $desc);
					}
				}
			}
		}
		fclose($myfile);
	}

	function PrintConfigDev($configFilePath) {
                $func_list = GetFuncList();
		$myfile = fopen($configFilePath, "r") or die("Unable to open file!");
		while(!feof($myfile)) {
			$line = fgets($myfile);
			$atts = explode('|', $line);
			if (sizeof($atts)>=3) {
				$key = $atts[0];
				$val = $atts[1];
				$type = trim($atts[2]);
				if (preg_match("/[A-Z]*_LED/", $key)) Print_LED($label, $key, $val, $desc);
				elseif (in_array($key, $func_list)) eval("Print_".$key."(\$key, \$key, \$val);");
				elseif (in_array($type, $func_list)) 	eval("Print_".$type."(\$key, \$key, \$val);");
				else 	echo trd_labelData($key, $val, $key);
				
			}
		}
		fclose($myfile);
	}


	function WriteConfig($post, $configFilePath) {

                $chkFile = FALSE;

		// read current config file
		$myfile = fopen($configFilePath, "r") ;
		$config_new = "";
		while(!feof($myfile)) {
			$line = fgets($myfile);
			$att = explode('|', $line);
	                if (count($att) > 2 ) {
	                        if (($chkFile==FALSE) and (isset($post[$att[0]]) == FALSE)) {
					echo "Tried to write data to wrong File! \tFile: " . $configFilePath . "\tData:" . $line;
					break;
				} else $chkFile = TRUE;
 
                                if (trim($att[2]) == 'bool') {
					$val =  isset($post[$att[0]]) ? "1" : "0";
				} else {
	                                $val =  isset($post[$att[0]]) ? $post[$att[0]] : $att[1];
				}
     				$config_new = $config_new . $att[0] . '|' . preg_replace("~[\r]~", "", trim($val));
				for($i=2; $i < count($att); $i++) {
					$config_new = $config_new . '|' . $att[$i] ;
				}
                                unset($post[$att[0]]);
			} else {
				 $config_new = $config_new . $line;
			}
		}
		fclose($myfile);

	        // write to the new config file
		if ($chkFile) {
			try {
//		    		$myfile = fopen("\config.bk", "w");
		    		$myFile = fopen($configFilePath, "c");
				if (flock($myFile, LOCK_EX)) {
					fwrite($myFile, $config_new);
                                        fwrite($myFile, "##### Written by config_tools.php at ". date("Y-m-d h:i:sa"));
                                        fflush($myFile);
                                        flock($myFile, LOCK_UN);
					fclose($myFile);
//					rename(CONFIG_PATH."config.bk", $configFilePath);
					echo "Wrote to file ".$configFilePath;
				}
				else echo "Error opening ".$configFilePath. "\n";

			} catch (Exception $e) {
	                        echo "Error writing to ".$configFilePath .":". $e->getMessage() . "\n";
			}
		}
	}
	
        function LoadConfig($configFilePath) {
	        $value_dict = [];
		$configf = fopen($configFilePath, "r") or die("Unable to open file!");
		while(!feof($configf)) {
			$line = fgets($configf);
			$att = explode('|', $line);
			if (count($att) > 2 ) {
				$e = array($att[1], $att[2]);
				$value_dict[$att[0]] = $e;
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
					$line = fgets($pyfile);  // ((AI_[A-Z]*.)\)
					if (preg_match_all("/class AI_([A-Z].*)\((.*)\):/", $line, $matches)) {
						$ai_engine = $matches[1][0];
						$ai_parent = (preg_match("/^AI_/", $matches[2][0]) ? "  (" . ucfirst(str_replace('AI_', '', $matches[2][0])).")" : "");
						echo "<option value=\"" . $ai_engine . "\" "  .   (($ai_engine == $value)?"selected":"") . ">" . $ai_engine. $ai_parent ."</option>";
					}
				}
				fclose($pyfile);
			} // preg_match filename
		}
		if ($desc!="") echo "</select></td></tr><tr><td></td><td><i>".$desc."</i></td></tr>";
		else echo "</select></td></tr>";
	}

	function Print_INTERPRET_ENGINE($label, $name, $value, $desc="") {
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
		fclose($pyfile);
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
		fclose($pyfile);
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
		fclose($pyfile);
		if ($desc!="") echo "</select></td></tr><tr><td></td><td><i>".$desc."</i></td></tr>";
		else echo "</select></td></tr>";
	}

	function Print_LED($label, $name, $value, $desc="") {
		echo "<tr><td id='leftHand'><b>".$label.":</b></td>";
		echo "<td id='rightHand' >";
		echo "<select color=\"".$value."\"name=\"".$name."\" value=".$value.">";
		$pyfile = fopen('/home/el3ktra/LilL3x/raspberryPi/rasp_leds.py', "r");
		while(!feof($pyfile)) {
			$line = fgets($pyfile);
			if (preg_match_all("/'(.*)':/", $line, $matches)) {
				$val = $matches[1][0];
				echo "<option color=\"".$val."\" value=\"" . $val . "\" "  .   (($val == $value)?"selected":"") . ">" . $val ."</option>";
			}
		}
		fclose($pyfile);
		if ($desc!="") echo "</select></td></tr><tr><td></td><td><i>".$desc."</i></td></tr>";
		else echo "</select></td></tr>";
	}


	function Print_WAKE_WORD($label, $name, $value, $desc="") {
		echo "<tr><td id='leftHand'><b>".$label.":</b></td>\n";
		echo "<td id='rightHand' >\n";
		echo "<select name=\"".$name."\" value=".$value.">\n";
		foreach (scandir('/home/el3ktra/LilL3x/wake') as $file) {
			if (preg_match_all("/^([a-z1-9 ]*)_.*\.ppn/", str_replace('-', ' ', $file), $matches)) {
				$wake_word = ucwords($matches[1][0]);
				$filepath = '/home/el3ktra/LilL3x/wake/'.$file;
				echo "<option value=\"" . $filepath  . "\" " . (($filepath == $value)?"selected":"") . ">" . $wake_word . "</option>";
			}
		}
  		if ($desc!="") echo "</select></td></tr><tr><td></td><td><i>".$desc."</i></td></tr>";
		else echo "</select></td></tr>";
	}
	function Print_WAKE_WORD_ENGINE($label, $name, $value, $desc="") {
		echo "<tr><td id='leftHand'><b>".$label.":</b></td>\n";
		echo "<td id='rightHand' >\n";
		echo "<select name=\"".$name."\" value=".$value.">\n";
		foreach (scandir('/home/el3ktra/LilL3x/') as $file) {
                        echo $file;
			if (preg_match_all("/^([a-z]*)_wake.py/", $file, $matches)) {
				$wake_word_eng = $matches[1][0];
				echo "<option value=\"" . $wake_word_eng  . "\" " . (($wake_word_eng == $value)?"selected":"") . ">" . ucwords($wake_word_eng) . "</option>";
			}
		}
  		if ($desc!="") echo "</select></td></tr><tr><td></td><td><i>".$desc."</i></td></tr>";
		else echo "</select></td></tr>";
	}

        function PrintHEADER($label, $ht="2") {
		echo "<tr><td colspan='2'><br><hr><h".$ht."><center>".$label."</center></h".$ht."></td></tr>";
	}

        function Print_blob($label, $key, $val, $desc="") {
		echo "<tr><td id=\"leftHand\"><b>" . $label . ":</b></td>";
		echo '<td id="rightHand"><textarea cols="40" rows="5" name="'.$key.'" />'.$val.'</textarea></td></tr>';
		echo ($desc == ""?"":"<tr><td></td><td><i>".$desc."</i></td></tr>");
	}

        function Print_int($label, $key, $val, $desc="") {
                echo trd_labelData($label, $val, $key, 0, "number");
		echo ($desc == ""?"":"<tr><td></td><td><i>".$desc."</i></td></tr>");
	}

        function Print_bool($label, $key, $val, $desc="") {
		echo "<tr><td id=\"leftHand\"><b>" . $label . ":</b></td>";
		echo '<td id="rightHand"><input type="checkbox" value="'.$val.'" name="'.$key.'" '.($val=="1"?'checked':'').'></td></tr>';
		echo ($desc == ""?"":"<tr><td></td><td><i>".$desc."</i></td></tr>");

	}
        function Print_other($label, $key, $val, $desc="") {
                echo trd_labelData($label, $val, $key);
		echo ($desc == ""?"":"<tr><td></td><td><i>".$desc."</i></td></tr>");
	}


        function GetFuncList() {
		$func_list = [];
		$php_file = fopen('/home/el3ktra/LilL3x/config/config_tools.php', "r");
		while(!feof($php_file)) {
		        $line = fgets($php_file);
		        if (preg_match_all("/function Print_(.*)\(/", $line, $matches)) {
				array_push($func_list, $matches[1][0]);
			}
		}
		fclose($php_file);
		return $func_list;
        }

?>
