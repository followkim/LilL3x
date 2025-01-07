<?php
	// turn on error reporting
	error_reporting(E_ALL ^ E_NOTICE);
	ini_set('display_errors', true); 
        include '/home/el3ktra/LilL3x/config/config_tools.php';

        echo"<html>";
	HTMLHead();
	PrintConfig();
        echo"</html>";
?>
