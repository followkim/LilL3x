<?php

	/*
	 * utils.php
	 * 
	 * Various functions and wrappers for DB connection
	 * 
	 */
	

	// lbt stands for "Little Bobby Tables".
	// Google it.
	function lbt($inStr)
	{
//		$inStr = stripslashes($inStr);
		$inStr = str_replace("\\", "\\\\", $inStr);
		$inStr = str_replace("'", "\'", $inStr);
		$inStr = str_replace("`", "\`", $inStr);
		$inStr = str_replace(";", "\;", $inStr);
		return $inStr;
	}

	function console_log($output, $with_script_tags = false) {
		$js_code = 'console.log(' . json_encode($output, JSON_HEX_TAG) .  ');';
		if ($with_script_tags) {
			$js_code = '<script>' . $js_code . '</script>';
		}
		echo $js_code;
	}
	
	function trd_labelData($label, $variable, $controlName = "", $isRequired = 0, $type="txt", $size=15  ) {
		echo "<tr>".td_labelData($label,$variable,$controlName,$isRequired,$type,$size)."</tr>";
	}
	function td_labelData($label, $variable, $controlName = "",  $type="txt", $isRequired = 0, $size=15)	{
		if ($controlName) {
			echo "<td id=\"leftHand\">".($isRequired?"<b>":"").($label?"$label":"")."".($isRequired?"*</b>":":")."</td>";
			echo "<td id=\"rightHand\"><input size=\"$size\" type=\"$type\" name=\"$controlName\" value=\"$variable\"/></td>";
		} else {
			echo "<td id=\"leftHand\"><b>".($label?"$label:":"")."</b></td>";
			echo "<td id=\"rightHand\">$variable</td>";
		}
	}
	
	function trd_dtData($label, $variable, $controlName = "", $isRequired = 0, $type="datetime-local", $size=15  ) {
		echo "<tr>".td_labelData($label,$variable,$controlName,$isRequired,$type,$size)."</tr>";
	}
	function td_dtData($label, $variable, $controlName = "",  $type="datetime-local", $isRequired = 0, $size=15)	{
		if ($controlName) {
			echo "<td id=\"leftHand\">".($isRequired?"<b>":"").($label?"$label":"")."".($isRequired?"*</b>":":")."</td>";
			echo "<td id=\"rightHand\"><input size=\"$size\" type=\"$type\" name=\"$controlName\" value=\"$variable\"/></td>";
		} else {
			echo "<td id=\"leftHand\"><b>".($label?"$label:":"")."</b></td>";
			echo "<td id=\"rightHand\">$variable</td>";
		}
	}

	
	function td_labelChk($label, $controlName, $isChecked=0) {
			echo "<td id=\"leftHand\">$label</b></td>";
			echo "<td><input type=\"checkbox\" name=\"$controlName\" value=\"1\" ".($isChecked?"checked":"")."></td>";
	}
	function trd_labelChk($label, $controlName, $isChecked=0) {
		echo "<tr>".td_labelChk($label, $controlName, $isChecked)."</tr>";
	}
