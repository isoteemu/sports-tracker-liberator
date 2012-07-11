<?php
/**
 * Endomondo API tracker script.
 * 
 * Purpose of this script is to tracke SSL requests from endomondo app.
 * By itself, it only logs queries, but with little dns faking and apache,
 * endomondo will accept it as authentic server.
 */

$content = "\n\n*** ENTRY *** ".date('H:M:s')."\n";

$protocol = (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] == 'on') ? 'https://' : 'http://';

$url = $protocol.$_SERVER['HTTP_HOST'].$_SERVER['REQUEST_URI'];

$opts = array(
	'http'=>array(
		'method'=> $_SERVER['REQUEST_METHOD'],
		'header'=> implode("\r\n", array(
			'User-Agent' => $_SERVER['HTTP_USER_AGENT']
		))
	)
);

$context = stream_context_create($opts);

$data = file_get_contents($url, false, $context);

$content .= print_r(array(
	'URL' => $url,
	'SERVER' => $_SERVER,
	'POST'   => $_POST,
	'GET'	 => $_GET,
	'DATA'	 => $data,
	'HEADERS' => $http_response_header
),1);
file_put_contents('/tmp/endomondo.txt', $content, FILE_APPEND);

foreach($http_response_header as $header) {
	header($header);
}

flush();

echo $data;
