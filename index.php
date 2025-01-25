<?php
       // turn on error reporting
        error_reporting(E_ALL ^ E_NOTICE);
        ini_set('display_errors', true);
        include '/home/el3ktra/LilL3x/config/html/utils.php';


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
          echo ' <a href="config/html/wifi.php">Set Wifi</a><br>';
          echo ' <a href="config">configure</a><br>';
          echo ' <a href="picts">Image Gallery</a><br>';
//          echo ' <a href="LilL3x/">Browse directory</a><br>';
          echo ' <p><hr>';
          echo ' <a href="config.php?txt">configure (Developer Version)</a><br>';
          echo ' <a href="config.php?vars">configure variables (Developer Version)</a><br>';
          echo '</body></html>';

        }


?>

<html>
<?php
	PrintIndex();

?>

</html>
