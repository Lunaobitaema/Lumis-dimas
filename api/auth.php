<?php
declare(strict_types=1);
define('LUMIS_API', true);
require __DIR__ . '/bootstrap.php';

$method = require_method('GET', 'POST');
start_admin_session();

if ($method === 'GET') {
    $authed = !empty($_SESSION['admin']);
    json_out(200, [
        'ok' => true,
        'authenticated' => $authed,
        'csrf' => $authed ? ($_SESSION['csrf'] ?? null) : null,
        'must_change' => $authed ? must_change_password() : false,
    ]);
}

require_same_origin();
$in = json_body();
$action = (string)($in['action'] ?? '');

if ($action === 'login') {
    if (!rate_limit('login', 5, 900, false)) {
        fail(429, 'too_many_attempts', 'Забагато спроб входу. Спробуйте через 15 хвилин');
    }
    $hash = admin_hash();
    if ($hash === '') {
        fail(503, 'not_configured', 'Пароль адміністратора не задано на сервері');
    }
    $password = is_string($in['password'] ?? null) ? $in['password'] : '';
    if ($password === '' || !password_verify($password, $hash)) {
        rate_limit('login', 5, 900, true);
        usleep(400000);
        fail(401, 'bad_password', 'Невірний пароль');
    }
    rate_limit_clear('login');
    session_regenerate_id(true);
    $_SESSION = ['admin' => true, 'seen' => time(), 'csrf' => bin2hex(random_bytes(32))];
    json_out(200, ['ok' => true, 'csrf' => $_SESSION['csrf'], 'must_change' => must_change_password()]);
}

if ($action === 'logout') {
    if (!empty($_SESSION['admin'])) { require_csrf(); }
    $_SESSION = [];
    if (ini_get('session.use_cookies')) {
        $p = session_get_cookie_params();
        setcookie(session_name(), '', ['expires' => time() - 3600, 'path' => $p['path'], 'secure' => $p['secure'], 'httponly' => true, 'samesite' => 'Strict']);
    }
    session_destroy();
    json_out(200, ['ok' => true]);
}

if ($action === 'change_password') {
    require_admin(true);
    require_csrf();
    $current = is_string($in['current'] ?? null) ? $in['current'] : '';
    $new     = is_string($in['new'] ?? null) ? $in['new'] : '';
    if (!password_verify($current, admin_hash())) {
        usleep(400000);
        fail(422, 'bad_current', 'Поточний пароль введено невірно', ['fields' => ['current' => 'Невірний поточний пароль']]);
    }
    if (mb_strlen($new) < 10 || mb_strlen($new) > 200) {
        fail(422, 'weak_password', 'Новий пароль має містити щонайменше 10 символів', ['fields' => ['new' => 'Щонайменше 10 символів']]);
    }
    if (hash_equals($current, $new)) {
        fail(422, 'same_password', 'Новий пароль має відрізнятися від поточного', ['fields' => ['new' => 'Має відрізнятися від поточного']]);
    }
    if (!write_json(data_dir() . '/admin.json', ['hash' => password_hash($new, PASSWORD_DEFAULT), 'changed_at' => date('c')])) {
        fail(500, 'write_failed', 'Не вдалося зберегти пароль на сервері');
    }
    session_regenerate_id(true);
    $_SESSION['csrf'] = bin2hex(random_bytes(32));
    json_out(200, ['ok' => true, 'csrf' => $_SESSION['csrf'], 'must_change' => false]);
}

fail(400, 'unknown_action', 'Невідома дія');
