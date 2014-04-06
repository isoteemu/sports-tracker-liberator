<?php
/**
 * Endomondo API tracker script.
 * 
 * Purpose of this script is to proxy SSL requests from endomondo app.
 * By itself, it only logs queries, but with little dns faking and apache,
 * endomondo will accept it as authentic server.
 */

@ini_set('display_errors', 0);

## Where to dump traces

if(!function_exists('gzdecode')) {
	function gzencode($data) {
		return gzinflate(substr($data,10));
	}
}

$filename = 'endomondo-trace';
if (isset($_SERVER['HTTP_HOST'])) {

	if(gethostbyname($_SERVER['HTTP_HOST']) == '127.0.0.1') {
		header("HTTP/1.0 404 Not Found");
		die();
	}

	$filename = preg_replace('/[^a-z0-9\.]+/i', '-', $_SERVER['HTTP_HOST']);
	$filename .= preg_replace('/[^a-z0-9\.]+/i', '-', $_SERVER['REDIRECT_URL']);
}
$filename .= '-'.date('H:m:s.u');

$trace_file = '/dev/shm/'.$filename.'.txt';

$content = "\n*** ENTRY *** ".date('H:m:s')."\n";

$protocol = (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] == 'on') ? 'https://' : 'http://';

$url = $protocol.$_SERVER['HTTP_HOST'].$_SERVER['REQUEST_URI'];

$opts = array(
	'http'=>array(
		'method'=> $_SERVER['REQUEST_METHOD'],
		'header'=> "",
		'user_agent' =>  $_SERVER['HTTP_USER_AGENT'],
		'protocol_version' => 1.1
	)
);

if($opts['http']['method'] == 'POST') {
	if (count($_POST)) {
		$opts['http']['content'] = http_build_query($_POST);
	} else {
		$opts['http']['content'] = file_get_contents('php://input');
	}

	#file_put_contents('/dev/shm/'.$filename.'.data.txt', $opts['http']['content']);

	$opts['http']['header'] .= "Content-Length: ".strlen($opts['http']['content'])."\r\n";
}

foreach(getallheaders() as $key => $val) {
	switch($key) {
		case 'Connection':
		case 'Content-Length':
			break;
		default:
			$opts['http']['header'] .= "$key: $val\r\n";
			break;
	}
}
$opts['http']['header'] = trim($opts['http']['header']);

$context = stream_context_create($opts, array(
	'allow_self_signed' => true,
));

$data = file_get_contents($url, false, $context);

$reply = array(
	'URL' => $url,
	'SERVER' => $_SERVER,
	'POST'   => $_POST,
	'GET'	 => $_GET,
	'DATA'	 => $data,
	'OPTS'	 => $opts,
	'HEADERS'=> $http_response_header
);

if($_GET['gzip'] == 'true') {
	$reply['DATA'] = gzdecode($data);
	if(strlen($reply['OPTS']['http']['content']))
		$reply['OPTS']['http']['content'] = gzdecode($reply['OPTS']['http']['content']);

} elseif($_GET['deflate'] == 'true') {
	$reply['DATA'] = @gzinflate(substr($data,2));
	if(strlen($reply['OPTS']['http']['content']))
		$reply['OPTS']['http']['content'] = gzinflate(substr($reply['OPTS']['http']['content'],2));
}

$content .= var_export($reply, true);

file_put_contents($trace_file, $content, FILE_APPEND);

header('Connection: close');
foreach($http_response_header as $header) {
	header($header);
}

flush();

echo $data;
