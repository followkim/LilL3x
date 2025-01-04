<?php
	// turn on error reporting
	error_reporting(E_ALL ^ E_NOTICE);
	ini_set('display_errors', true); 
        include '/home/el3ktra/LilL3x/config/config_tools.php';

?>

<!DOCTYPE html>
<html>
	<head>
		<meta charset="UTF-8">
		<title>Configure <?php echo gethostname() ?></title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
	</head>

	<body>
	   	<center><b><h1>Configure <?php echo gethostname() ?></b></h1></center>
		<div class="container">
			<form action="" method="POST">
				<?php PrintConfig(); ?>
				<input type="submit" value="Set"/>
			</form>
			<p><a href="index.php">Back to main page</a>
		</div>
	</body>
</html>
