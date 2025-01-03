<?php 	
	 	 
	// turn on error reporting
	error_reporting(E_ALL ^ E_NOTICE);
	ini_set('display_errors', true); 

	
//	include 'includes/utils.php';			// utils.php: database connection/disconnect functiosn
        include '/home/el3ktra/LilL3x/config/config_tools.php';
	// is this a POST if so, grab the POST varibales which are used to populate the search parameters.

	$isPost = ($_SERVER['REQUEST_METHOD'] == 'POST');
	if ($isPost) {
            WriteConfig($_POST);
	}

?>


<!DOCTYPE html>
<html>
	<head>
		<meta charset="UTF-8">
		<title>Configure <?php echo gethostname() ?></title>
                <meta name="viewport" content="width=device-width, initial-scale=1">

	</head>

	<body>


		<div class="container">
		<form action="" method="POST">
			<table id=criteria>

<?php
	PrintConfigDev();
?>

				
			</table>
			<input type="submit" value="Set"/>
			</form>
<p><a href="index.php">Back to main page</a>
			
		</div>
	</body>
</html>
