<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8" />
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.0/jquery.min.js"></script>
    <link href='css/default.css' rel='stylesheet' type='text/css'>
    <link href='simplelightbox/simplelightbox.min.css' rel='stylesheet' type='text/css'>
    <script type="text/javascript" src="simplelightbox/simple-lightbox.js"></script>
    <script type="text/javascript" src="js/main.js"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
        <title>Picture Gallery</title>
</head>

<body>
    <div class="container">
        <div class="oldgallery">

            <?php
            // Image extensions
            $image_extensions = array("png","jpg","jpeg","gif", "PNG","JPG","JPEG","GIF");

            // Target directory
            $dir = './';
            if (is_dir($dir))
			{

				if ($dh = opendir($dir)) 
				{

					// Generate the table
				   $count = 1;

					// Read files
					while (($file = readdir($dh)) !== false) 
					{

						if($file != '' && $file != '.' && $file != '..')
						{

							// Thumbnail image path
							$thumbnail_path = $file;

							// Image path
							$image_path = $file;

							$thumbnail_ext = pathinfo($thumbnail_path, PATHINFO_EXTENSION);
							$image_ext = pathinfo($image_path, PATHINFO_EXTENSION);

							$fb_share_link = "https://www.facebook.com/sharer/sharer.php?u=http://gallery.el3ktra.net/gallerys/rcds/" . $image_path."&TITLE=RCDS";
							$tw_share_link = "https://twitter.com/intent/tweet?text=RCDS+-+http://gallery.el3ktra.net/gallerys/rcds/" . $image_path;
							$dl_share_link = "http://gallery.el3ktra.net/gallerys/rcds/" . $image_path;

							// Check its not folder and it is image file
							if(!is_dir($image_path) && in_array($thumbnail_ext,$image_extensions) && in_array($image_ext,$image_extensions)) 
							{
								?>
								<table>
									<tr><td>
										<div class="gallery" ><a href="<?php echo $image_path; ?>"><img src="<?php echo $thumbnail_path; ?>" alt="" title="" /></a></div>
									</td></tr>	
									<tr><td>
										<table zheight="100%" width="100%" class="sm"><tr>
											<td background="#3B5998" width="25%"><a href="#" class="fa fa-facebook" onclick="pop_up('<?php echo $fb_share_link; ?>');"></a></td>
											<td background="#55ACEE" width="25%"><a href="#" class="fa fa-twitter"  onclick="pop_up('<?php echo $tw_share_link; ?>');"></a></td>
											<td background="#808080" width="25%"><a href="<?php echo $dl_share_link; ?>" download class="fa fa-download"></a></td>										
											<td background="#FF0000" width="25%"><a href="<?php echo $dl_share_link; ?>" download class="fa fa-download"></a></td>										
										</tr></table>
									</td></tr>
								</table>
								<?php
					
								// Break
								if( $count%4 == 0){
								   ?>
									 <div cclass="clear"></div>
								   <?php 
								}
								$count++;
							}
						}
					}
					closedir($dh);
				}
			 }
			?>
			</div>
		</div>
	</body>
	</html>


	<!-- Script -->
	<script type='text/javascript'>

		$(document).ready(function() {

			 // Intialize gallery
			 var gallery = $('.gallery a').simpleLightbox();


			$('.fa a').on('click.fa', function(e) {
				e.preventDefault();
				console.log("click")

				var self = $(this);
				PopupCenter(self.attr('href'), self.find('.text').html(), 600, 450);
			});
		});
	</script>
