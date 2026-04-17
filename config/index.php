
<?php
	// turn on error reporting
	error_reporting(E_ALL ^ E_NOTICE);
	ini_set('display_errors', true); 
        include  __DIR__ . '/config_tools.php';

        echo"<html>";
	HTMLHead();
	PrintConfig();
        echo"</html>";
        echo '<p><a href="/LilL3x/index.php">Back to main page</a></body>';
?>

<script type="text/javascript" src="config_tools.js"></script>
