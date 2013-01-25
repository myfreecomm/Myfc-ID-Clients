<?php
$req_url = 'http://sandbox.app.passaporteweb.com.br/sso/initiate';
$authurl = 'http://sandbox.app.passaporteweb.com.br/sso/authorize';
$acc_url = 'http://sandbox.app.passaporteweb.com.br/sso/token';
$api_url = 'http://sandbox.app.passaporteweb.com.br/sso/fetchuserdata';
$callback_url = '<url do script atual>';
$conskey = 'SRCeyl5ioH';
$conssec = 'CfRB98YyqXXPNJSrpEAwGVM3OLWHLrAQ';

session_start();

// In state=1 the next request should include an oauth_token.
// If it doesn't go back to 0
if(!isset($_GET['oauth_token']) && $_SESSION['state']==1) $_SESSION['state'] = 0;
try {
  $oauth = new OAuth($conskey,$conssec,OAUTH_SIG_METHOD_HMACSHA1,OAUTH_AUTH_TYPE_AUTHORIZATION);
  $oauth->enableDebug();
  if(!isset($_GET['oauth_token']) && !$_SESSION['state']) {
    $request_token_info = $oauth->getRequestToken($req_url,$callback_url);
    $_SESSION['secret'] = $request_token_info['oauth_token_secret'];
    $_SESSION['state'] = 1;
    header('Location: '.$authurl.'?oauth_token='.$request_token_info['oauth_token']);
    exit;
  } else if($_SESSION['state']==1) {
    $oauth->setToken($_GET['oauth_token'],$_SESSION['secret']);
    $access_token_info = $oauth->getAccessToken($acc_url);
    $_SESSION['state'] = 2;
    $_SESSION['token'] = $access_token_info['oauth_token'];
    $_SESSION['secret'] = $access_token_info['oauth_token_secret'];
  }
  $oauth->setToken($_SESSION['token'],$_SESSION['secret']);
  $oauth->fetch($api_url);
  $json = json_decode($oauth->getLastResponse());
  print_r($json);
} catch(OAuthException $E) {
  print_r($E);
}
?>
