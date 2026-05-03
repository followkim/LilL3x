<?php
       // turn on error reporting
        error_reporting(E_ALL ^ E_NOTICE);
        ini_set('display_errors', true);
        include __DIR__ . '/config/html/utils.php';


        function HTMLHead() {
          echo "<head>";
          echo " <title>".gethostname()."</title>";
          echo '  <meta name="viewport" content="width=device-width, initial-scale=1">';
          echo '  <link rel="stylesheet" href="'.'config/html/lill3x.css'.'">';
          echo "</head>";
        }



        function PrintIndex() {
          HTMLHead();
          echo "<body> <p>";
          echo '<h1>Welcome to '.gethostname().'</h1>';
          echo ' <a href="config/html/wifi.php">Set Wifi</a><br>';
          echo ' <a href="config">Configure</a><br>';
          echo ' <a href="picts">Image Gallery</a><br>';
//          echo ' <a href="training">Training</a><br>';
          echo ' <a href="log">Logs</a><br>';
//          echo ' <a href="LilL3x/">Browse directory</a><br>';
          echo ' <p><hr>';
          echo ' <a href="config/?txt">Configure (Developer Version)</a><br>';
          echo ' <a href="config/?vars">Configure variables (Developer Version)</a><br>';
          echo '</body></html>';

        }


?>

<html>
<?php
	PrintIndex();

?>

</html>
