
<?php 	
	// turn on error reporting
	error_reporting(E_ALL ^ E_NOTICE);
	ini_set('display_errors', true);
        include '/home/el3ktra/LilL3x/config/html/utils.php';

	const CONFIG_PATH =  "/home/el3ktra/LilL3x/config/";
	const CONFIG_ROOT =  "config.txt";
	const CONFIG_DD =  CONFIG_PATH . "config_dd.txt";
	const CONFIG_FILE =  CONFIG_PATH . CONFIG_ROOT;
	const CONFIG_FILE_LOCK =  CONFIG_FILE . ".LOCK";


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
	  echo ' <a href="LilL3x/picts">Image Gallery</a><br>';
	  echo ' <a href="LilL3x/">Browse directory</a><br>';
	  echo ' <p><hr>';
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

		echo "<body>";
                echo "<center><b><h1>Configure ".gethostname()."</b></h1></center>";
                echo '<form action="" method="POST">';

		echo "<table>";

		if ((sizeof(array_keys($_GET))>0) and (strlen(array_keys($_GET)[0])>1)) PrintConfigDev($configFile);
		else PrintConfigPretty();

		echo "</table>";
                echo '<input type="submit" value="Set"/></form>';
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
				$class = sizeof($atts)>= 4? trim($atts[3]):"";
	                        $val = array_key_exists($key, $value_dict)?$value_dict[$key][0]:'';
	                        $type= array_key_exists($key, $value_dict)?trim($value_dict[$key][1]):'str';

				if (preg_match("/^[a-zA-Z]/", $key)) {
					if ($key=="HEADER") {
						PrintHEADER($label, (array_key_exists(2, $atts)?$desc:"2"));
					} elseif (preg_match("/[A-Z]*_LED/", $key)) {
						Print_LED($label, $key, $val, $desc, $class);
					} elseif (in_array($key, $func_list)) {
						eval("Print_".$key."(\$label, \$key, \$val, \$desc, \$class);");
	                                } elseif (in_array($type, $func_list)) {
	                                        eval("Print_".$type."(\$label, \$key, \$val, \$desc, \$class);");
					} else {
						Print_other($label, $key, $val, $desc, $class);
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
				$keyLabel = $key. " (<i>" . $type . "</i>)";
				if (preg_match("/[A-Z]*_LED/", $key)) Print_LED($keyLabel, $key, $val);
				elseif (in_array($key, $func_list)) eval("Print_".$key."(\$keyLabel, \$key, \$val);");
				elseif (in_array($type, $func_list)) 	eval("Print_".$type."(\$keyLabel, \$key, \$val);");
				else 	echo trd_labelData($keyLabel, $val, $key);
				
			}
		}
		fclose($myfile);
	}

        function LockFile() {
		while (file_exists(CONFIG_FILE_LOCK)) {
			usleep(1000000/0.25);
		}

		$myfileLock = fopen(CONFIG_FILE_LOCK, "w");
		fclose($myfileLock);
	}
	function UnlockFile() {
		while (file_exists(CONFIG_FILE_LOCK)) {
			unlink(CONFIG_FILE_LOCK);
		}
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
			}
		}
		fclose($myfile);

	        // write to the new config file
		if ($chkFile) {
			try {
//		    		$myfile = fopen("\config.bk", "w");
		    		$myFile = fopen($configFilePath."php.BAK", "w");
				fwrite($myFile, $config_new);
                                fwrite($myFile, "##### Written by config_tools.php at ". date("Y-m-d h:i:sa")."\n\n");
                                fflush($myFile);
				fclose($myFile);

				LockFile();
				rename($configFilePath."php.BAK", $configFilePath);
                                chmod($configFilePath, 0664);
				UnlockFile();
				echo "<i>Wrote to file '".basename($configFilePath)."'<i>";

			} catch (Exception $e) {
	                        echo "Error writing to ".basename($configFilePath) .":". $e->getMessage() . "\n";
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


	function Print_AI_ENGINE($label, $name, $value, $desc="", $class="") {
		echo "<tr><td id='leftHand'><b>".$label.":</b></td>";
		echo "<td id='rightHand' >";
		echo "<table><tr><td><select id='".$name."' class=\"".$name."\" name=\"".$name."\" value=".$value.">\n";
	
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
                echo "</select></td></tr>";
		echo "<tr><td><i>".$desc."</i></td></tr></table></td></tr>";
	}

	function Print_INTERPRET_ENGINE($label, $name, $value, $desc="", $class="") {
		echo "<tr class='".$class."' ><td id='leftHand'><b>".$label.":</b></td>";
		echo "<td id='rightHand' >";
		echo "<table><td><tr><select id='".$name."' name=\"".$name."\" value=".$value.">";
		$pyfile = fopen('/home/el3ktra/LilL3x/listen_tools.py', "r");
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
                echo "</select></td></tr>";
		echo "<tr><td><i>".$desc."</i></td></tr></table></td></tr>";
	}

	function Print_SPEECH_ENGINE($label, $name, $value, $desc="", $class="") {
		echo "<tr><td id='leftHand'><b>".$label.":</b></td>";
		echo "<td id='rightHand' >";
		echo "<table><tr><td><select id='".$name."'  name=\"".$name."\" value=".$value.">";
		$pyfile = fopen('/home/el3ktra/LilL3x/speech_tools.py', "r");
		while(!feof($pyfile)) {
			$line = fgets($pyfile);
			if (preg_match_all("/class (.*)_tts:/", $line, $matches)) {
			$engine = $matches[1][0];
			echo "<option value=\"" . $engine . "\" "  .   (($engine == $value)?"selected":"") . ">" . $engine ."</option>";
			}
		}
		fclose($pyfile);
                echo "</select></td></tr>";
		echo "<tr><td><i>".$desc."</i></td></tr></table></td></tr>";

	}

        function Print_LISTEN_ENGINE($label, $name, $value, $desc="", $class="") {
                echo "<tr><td id='leftHand'><b>".$label.":</b></td>";
                echo "<td id='rightHand' >";
                echo "<table><tr><td><select id='".$name."'  name=\"".$name."\" value=".$value.">";
                $pyfile = fopen('/home/el3ktra/LilL3x/lillex.py', "r");
                while(!feof($pyfile)) {
                        $line = fgets($pyfile);
                        if (preg_match_all("/from .* import (.*)_listener/", $line, $matches)) {
                        $engine = $matches[1][0];
                        echo "<option value=\"" . $engine . "\" "  .   (($engine == $value)?"selected":"") . ">" . $engine ."</option>";
                        }
                }
                fclose($pyfile);
                echo "</select></td></tr>";
                echo "<tr><td><i>".$desc."</i></td></tr></table></td></tr>";

        }


	function Print_DEBUG($label, $name, $value, $desc="", $class="") {
		echo "<tr><td id='leftHand'><b>".$label.":</b></td>";
		echo "<td id='rightHand' >";
		echo "<table><tr><td><select name=\"".$name."\" value=".$value.">";
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
                echo "</select></td></tr>";
		echo "<tr><td><i>".$desc."</i></td></tr></table></td></tr>";
	}

	function Print_LED($label, $name, $value, $desc="", $class="") {

                $colors = ['blue' => '#0002FF', 'green' => '#00FF00', 'orange' => '#FF8000', 'pink' => '#FF3399', 'purple' => '#800080', 'red' => '#FF0000', 'white' => '#FFFFFF', 'yellow' => '#FFFF33'];
                if ($value[0] != "#") {
                	$value=$colors[$value];
                }

		echo "<tr><td id='leftHand'><b>".$label.":</b></td>";
                echo "<td><table><tr><td><input type='color' name = '".$name."' value=".$value." /></td></tr>";
		echo "<tr><td><i>".$desc."</i></td></tr></table></td></tr>";
	}


	function Print_WAKE_WORD($label, $name, $value, $desc="", $class="") {
		echo "<tr  class=\"".$class."\" ><td id='leftHand'><b>".$label.":</b></td>\n";
		echo "<td id='rightHand' >\n";
		echo "<table><tr><td><select  value=".$value.">\n";
		foreach (scandir('/home/el3ktra/LilL3x/wake') as $file) {
			if (preg_match_all("/^([a-z1-9 ]*)_.*\.ppn/", str_replace('-', ' ', $file), $matches)) {
				$wake_word = ucwords($matches[1][0]);
				$filepath = '/home/el3ktra/LilL3x/wake/'.$file;
				echo "<option value=\"" . $filepath  . "\" " . (($filepath == $value)?"selected":"") . ">" . $wake_word . "</option>";
			}
		}
                echo "</select></td></tr>";
  		echo "<tr><td><i>".$desc."</i></td></tr></table></td></tr>";
	}
	function Print_WAKE_WORD_ENGINE($label, $name, $value, $desc="", $class="") {
		echo "<tr><td id='leftHand'><b>".$label.":</b></td>\n";
		echo "<td id='rightHand' >\n";
		echo "<table><tr><td><select  id='".$name."'  name=\"".$name."\" value=".$value.">\n";
		foreach (scandir('/home/el3ktra/LilL3x/') as $file) {
			if (preg_match_all("/^([a-z]*)_wake.py/", $file, $matches)) {
				$wake_word_eng = $matches[1][0];
				echo "<option value=\"" . $wake_word_eng  . "\" " . (($wake_word_eng == $value)?"selected":"") . ">" . ucwords($wake_word_eng) . "</option>";
			}
		}
                echo "</select></td></tr>";
  		echo "<tr><td><i>".$desc."</i></td></tr></table></td></tr>";
	}

        function PrintHEADER($label, $ht="2") {
                echo '<tr><td><input type="submit" value="Set"/></td><td></td></tr>';
		echo "<tr><td colspan='2'><br><hr><h".$ht."><center>".$label."</center></h".$ht."></td></tr>";
	}

        function Print_blob($label, $key, $val, $desc="", $class="") {
		echo "<tr class='".$class."' ><td id=\"leftHand\"><b>" . $label . ":</b></td>";
		echo '<td><table><tr><td id="rightHand"><textarea cols="60" rows="5" name="'.$key.'" />'.$val.'</textarea></td></tr>';
		echo "<tr><td><i>".$desc."</i></td></tr></table></td></tr>";
	}

        function Print_int($label, $key, $val, $desc="", $class="") {
		echo "<tr class='".$class."'><td id=\"leftHand\"><b><div class='".$class."' >" . $label . ":</div></b></td>";
                echo '<td><table><tr><td id="rightHand"><input size="50" type="int" name="'.$key.'" value="'.$val.'" /></td></tr>';
		echo "<tr><td><i>".$desc."</i></td></tr></table></td></tr>";
	}

        function Print_bool($label, $key, $val, $desc="", $class="") {
		echo "<tr class='".$class."'><td id=\"leftHand\"><b>" . $label . ":</b></td>";
		echo '<td><table><tr><td id="rightHand"><input type="checkbox" id="'.$key.'"   value="'.$val.'" name="'.$key.'" '.($val=="1"?'checked':'').'></td></tr>';
		echo "<tr><td><i>".$desc."</i></td></tr></table></td></tr>";

	}
        function Print_other($label, $key, $val, $desc="", $class="") {
		echo "<tr class='".$class."'  ><td   id=\"leftHand\"><b><div>" . $label . ":</b><div></td>";
                echo '<td><table><tr><td id="rightHand"><input size="50" type="" name="'.$key.'" value="'.$val.'" /></td></tr>';
		echo "<tr><td><i>".$desc."</i></td></tr></table></td></tr>";
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
