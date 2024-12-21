<?php 	
	// turn on error reporting
	error_reporting(E_ALL ^ E_NOTICE);
	ini_set('display_errors', true); 

	
	include 'includes/utils.php';			// utils.php: database connection/disconnect functiosn
		
	// is this a POST if so, grab the POST varibales which are used to populate the search parameters.
	$isPost = ($_SERVER['REQUEST_METHOD'] == 'POST');
 	

//	$config_dir = '/home/el3ktra/LilL3x/config/';
//	$config_file = $config_dir . 'config.txt';
	$config_file = "config.txt";
	$config_dd = "config_dd.txt";
        $value_dict = [];
	if ($isPost) {
		// read current config file
		$myfile = fopen($config_file, "r") or die("Unable to open file!");
		$config_new = "";
		while(!feof($myfile)) {
			$line = fgets($myfile);
			$att = explode('|', $line);
	                if (count($att) > 2 ) {
                                $val =  array_key_exists($att[0], $_POST) ? $_POST[$att[0]] : $att[1];
     				$config_new = $config_new . $att[0] . '|' . preg_replace("~[\r]~", "", trim($val));
				for($i=2; $i < count($att); $i++) {
					$config_new = $config_new . '|' . $att[$i] ;
				}
			}
		}
		fclose($myfile);

        // write to the new config file
		$myfile = fopen($config_file, "w") or die("Unable to open file!");
		fwrite($myfile, $config_new);
		fclose($myfile);
	}


                // laod the data dictionary
                $configf = fopen($config_file, "r") or die("Unable to open file!");
                while(!feof($configf)) {
                        $line = fgets($configf);
                        $att = explode('|', $line);
                        if (count($att) > 2 ) {
                            $e = array($att[1], $att[2]);
                            $value_dict[$att[0]] = $e;
//                            echo $value_dict[$att[0]][0]."|".$value_dict[$att[0]][1] . "";
                        }
                }
                fclose($configf);
?>


<!DOCTYPE html>
<html>
	<head>
		<meta charset="UTF-8">
		<title>Configure El3ktra</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">

	</head>

	<body>


		<div class="container">
		<form action="" method="POST">
			<table id=criteria>

<?php
					$myfile = fopen($config_dd, "r") or die("Unable to open file!");
					while(!feof($myfile)) {
						$line = fgets($myfile);
						$atts = explode('|', $line);
						if (preg_match("/^[a-zA-Z]/", $atts[0])) {
							if ($atts[0] == "AI_ENGINE") {
								echo "<tr><td id='leftHand'><b>".$atts[1].":</b></td>";
								echo "<td id='rightHand' >";
								echo "<select name=\"".$atts[0]."\" value=".$value_dict[$atts[0]][0].">\n";
								foreach (scandir('/home/el3ktra/LilL3x/beings') as $file) {
									if (preg_match("/^AI_[A-Z]/", $file)) {
                                                                                $pyfile = fopen('/home/el3ktra/LilL3x/beings/'.$file, "r");
                                                                                while(!feof($pyfile)) {
                                                                                    $line = fgets($pyfile);
                                                                                    if (preg_match_all("/class AI_([A-Z])(.*)\(/", $line, $matches)) {
                                                                                        $ai_engine = $matches[1][0].$matches[2][0];
											echo "<option value=\"" . $ai_engine . "\" "  .   (($ai_engine == $value_dict[$atts[0]][0])?"selected":"") . ">" . $ai_engine ."</option>";
										    }
										}
                                                                                fclose($pyfile);
									} // preg_match filename                                                                      
								}
                                                                echo "</select></td></tr><tr><td></td><td><i>".$atts[2]."</i></td></tr>";
							}
                                                       elseif ($atts[0] == "AINAMEP") {
                                                                echo "<tr><td id='leftHand'><b>".$atts[1].":</b></td>\n";
                                                                echo "<td id='rightHand' >\n";
                                                                echo "<select name=\"".$atts[0]."\" value=".$value_dict[$atts[0]][0].">\n";
                                                                foreach (scandir('/home/el3ktra/LilL3x/wake') as $file) {
                                                                        if (preg_match_all("/^([a-z ]*)_.*\.ppn/", $file, $matches)) {
                                                                               $wake_word = $matches[1][0];
                                                                               $filepath = '/home/el3ktra/LilL3x/wake/'.$file;
                                             echo "<option value=\"" . $filepath  . "\" "  .   (($filepath == $value_dict[$atts[0]][0])?"selected":"") . ">" . $wake_word . "</option>";
                                                                         }
                                                                }
                                                                echo "</select></td></tr><tr><td></td><td><i>".$atts[2]."</i></td></tr>";
                                                        }

                                                       elseif ($atts[0] == "LISTEN_ENGINE") {
                                                                echo "<tr><td id='leftHand'><b>".$atts[1].":</b></td>";
                                                                echo "<td id='rightHand' >";
                                                                echo "<select name=\"".$atts[0]."\" value=".$value_dict[$atts[0]][0].">";
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
        								echo "<option value=\"" . $engine . "\" "  .   (($engine == $value_dict[$atts[0]][0])?"selected":"") . ">" . $engine ."</option>";
 								}
                                                                echo "</select></td></tr><tr><td></td><td><i>".$atts[2]."</i></td></tr><br>";

                                                        }

                                                       elseif ($atts[0] == "SPEECH_ENGINE") {
                                                                echo "<tr><td id='leftHand'><b>".$atts[1].":</b></td>";
                                                                echo "<td id='rightHand' >";
                                                                echo "<select name=\"".$atts[0]."\" value=".$value_dict[$atts[0]][0].">";
                                                                $pyfile = fopen('/home/el3ktra/LilL3x/speech_tools.py', "r");
                                                                while(!feof($pyfile)) {
	                                                                $line = fgets($pyfile);
                                                                        if (preg_match_all("/class (.*)_tts:/", $line, $matches)) {
  	                        	                                        $engine = $matches[1][0];
               									echo "<option value=\"" . $engine . "\" "  .   (($engine == $value_dict[$atts[0]][0])?"selected":"") . ">" . $engine ."</option>";
                                                                        }
                                                                }
                                                                echo "</select></td></tr><tr><td></td><td><i>".$atts[2]."</i></td></tr>";
                                                        }

                                                       elseif ($atts[0] == "DEBUG") {
                                                                echo "<tr><td id='leftHand'>".$value_dict[$atts[0]][0].":</td>";
                                                                echo "<td id='rightHand' >";
                                                                echo "<select name=\"".$atts[0]."\" value=".$value_dict[$atts[0]][0].">";
                                                                $pyfile = fopen('/home/el3ktra/LilL3x/error_handling.py', "r");
                                                                while(!feof($pyfile)) {
	                                                                $line = fgets($pyfile);
                                                                        if (preg_match_all("/##(.*)-(.*)/", $line, $matches)) {
  	                        	                                        $val = $matches[1][0];
  	                        	                                        $desc = $matches[2][0];
               									echo "<option value=\"" . $val . "\" "  .   (($val == $value_dict[$atts[0]][0])?"selected":"") . ">" . $desc ."</option>";
                                                                        }
                                                                }
                                                                echo "</select></td></tr><tr><td></td><td><i>".$atts[2]."</i></td></tr>";

                                                        }

							else {
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
?>



				
			</table>
			<input type="submit" value="Set"/>
			</form>
			
		</div>
	</body>
</html>
