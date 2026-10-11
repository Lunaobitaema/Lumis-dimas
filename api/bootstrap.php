<?php
/**
 * LUMIS — спільне ядро серверної частини.
 * Файл не має власної точки входу: пряме звернення нічого не повертає.
 */
declare(strict_types=1);

if (!defined('LUMIS_API')) { http_response_code(404); exit; }

error_reporting(E_ALL);
ini_set('display_errors', '0');
ini_set('log_errors', '1');

date_default_timezone_set('Europe/Kyiv');

header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: same-origin');
header('Cache-Control: no-store');

function cfg(?string $key = null, $default = null)
{
    static $c = null;
    if ($c === null) {
        $file = __DIR__ . '/config.php';
        if (!is_file($file)) {
            json_out(503, ['ok' => false, 'code' => 'not_configured', 'message' => 'Сервер не налаштовано: відсутній api/config.php']);
        }
        $c = require $file;
        if (!is_array($c)) { $c = []; }
    }
    return $key === null ? $c : ($c[$key] ?? $default);
}

function json_out(int $status, array $data): void
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function fail(int $status, string $code, string $message, array $extra = []): void
{
    json_out($status, ['ok' => false, 'code' => $code, 'message' => $message] + $extra);
}

function require_method(string ...$methods): string
{
    $m = $_SERVER['REQUEST_METHOD'] ?? 'GET';
    if (!in_array($m, $methods, true)) {
        header('Allow: ' . implode(', ', $methods));
        fail(405, 'method_not_allowed', 'Метод не підтримується');
    }
    return $m;
}

/** Запити, що змінюють дані, приймаються лише з власного походження сайту. */
function require_same_origin(): void
{
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    if ($origin === '') { return; }
    $host = parse_url($origin, PHP_URL_HOST);
    $port = parse_url($origin, PHP_URL_PORT);
    $given = strtolower((string)$host . ($port ? ':' . $port : ''));
    $own   = strtolower((string)($_SERVER['HTTP_HOST'] ?? ''));
    if ($given !== $own) {
        fail(403, 'bad_origin', 'Запит з іншого сайту відхилено');
    }
}

function is_https(): bool
{
    return (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https' && cfg('trust_proxy_headers', false));
}

function client_ip(): string
{
    if (cfg('trust_proxy_headers', false)) {
        $cf = $_SERVER['HTTP_CF_CONNECTING_IP'] ?? '';
        if ($cf !== '' && filter_var($cf, FILTER_VALIDATE_IP)) { return $cf; }
    }
    return (string)($_SERVER['REMOTE_ADDR'] ?? '0.0.0.0');
}

/**
 * Каталог даних. Усередині storage_dir створюється підкаталог з випадковою назвою,
 * тож навіть на сервері без .htaccess шлях до заявок неможливо вгадати.
 */
function data_dir(): string
{
    static $dir = null;
    if ($dir !== null) { return $dir; }
    $base = rtrim((string)cfg('storage_dir', __DIR__ . '/../storage'), '/');
    if (!is_dir($base) && !@mkdir($base, 0750, true)) {
        fail(500, 'storage_unavailable', 'Сховище даних недоступне');
    }
    $found = glob($base . '/data-*', GLOB_ONLYDIR);
    if ($found) {
        $dir = $found[0];
    } else {
        $dir = $base . '/data-' . bin2hex(random_bytes(16));
        if (!@mkdir($dir, 0750, true)) {
            fail(500, 'storage_unavailable', 'Сховище даних недоступне для запису');
        }
    }
    foreach (['leads', 'ratelimit', 'backups', 'sessions'] as $sub) {
        if (!is_dir("$dir/$sub")) { @mkdir("$dir/$sub", 0750, true); }
    }
    return $dir;
}

function read_json(string $file, $default = null)
{
    if (!is_file($file)) { return $default; }
    $raw = @file_get_contents($file);
    if ($raw === false) { return $default; }
    $data = json_decode($raw, true);
    return $data === null ? $default : $data;
}

/** Атомарний запис: тимчасовий файл + rename, щоб не отримати напівзаписаний JSON. */
function write_json(string $file, $data): bool
{
    $tmp = $file . '.' . bin2hex(random_bytes(4)) . '.tmp';
    $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
    if ($json === false || @file_put_contents($tmp, $json, LOCK_EX) === false) { @unlink($tmp); return false; }
    if (!@rename($tmp, $file)) { @unlink($tmp); return false; }
    return true;
}

/** Обмеження частоти: не більше $max подій за $window секунд на IP у межах $bucket. */
function rate_limit(string $bucket, int $max, int $window, bool $record = true): bool
{
    $file = data_dir() . '/ratelimit/' . hash('sha256', $bucket . '|' . client_ip()) . '.json';
    $fh = @fopen($file, 'c+');
    if (!$fh) { return true; }
    flock($fh, LOCK_EX);
    $raw = stream_get_contents($fh);
    $hits = json_decode($raw ?: '[]', true);
    if (!is_array($hits)) { $hits = []; }
    $now = time();
    $hits = array_values(array_filter($hits, fn($t) => is_int($t) && $t > $now - $window));
    $allowed = count($hits) < $max;
    if ($allowed && $record) { $hits[] = $now; }
    ftruncate($fh, 0); rewind($fh); fwrite($fh, json_encode($hits));
    flock($fh, LOCK_UN); fclose($fh);
    return $allowed;
}

function rate_limit_clear(string $bucket): void
{
    @unlink(data_dir() . '/ratelimit/' . hash('sha256', $bucket . '|' . client_ip()) . '.json');
}

function start_admin_session(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) { return; }
    session_save_path(data_dir() . '/sessions');
    session_name('lumis_admin');
    ini_set('session.use_strict_mode', '1');
    ini_set('session.use_only_cookies', '1');
    ini_set('session.gc_maxlifetime', '7200');
    session_set_cookie_params([
        'lifetime' => 0, 'path' => '/', 'secure' => is_https(),
        'httponly' => true, 'samesite' => 'Strict',
    ]);
    session_start();
    if (random_int(1, 40) === 1) { purge_old(data_dir() . '/sessions', 86400); purge_old(data_dir() . '/ratelimit', 86400); }
    $idle = 7200;
    if (!empty($_SESSION['admin']) && (time() - (int)($_SESSION['seen'] ?? 0)) > $idle) {
        $_SESSION = [];
        session_regenerate_id(true);
    }
    if (!empty($_SESSION['admin'])) { $_SESSION['seen'] = time(); }
}

/** Прибирає застарілі службові файли (сесії, лічильники частоти). */
function purge_old(string $dir, int $age): void
{
    foreach (glob($dir . '/*') ?: [] as $f) {
        if (is_file($f) && filemtime($f) < time() - $age) { @unlink($f); }
    }
}

function admin_hash(): string
{
    $own = read_json(data_dir() . '/admin.json', []);
    if (!empty($own['hash'])) { return (string)$own['hash']; }
    return (string)cfg('admin_password_hash', '');
}

/** Поки діє стартовий пароль з config.php, зміни на сайті заборонено. */
function must_change_password(): bool
{
    $own = read_json(data_dir() . '/admin.json', []);
    return empty($own['hash']);
}

function require_admin(bool $allowInitialPassword = false): void
{
    start_admin_session();
    if (empty($_SESSION['admin'])) {
        fail(401, 'unauthorized', 'Потрібен вхід до адмін-панелі');
    }
    if (!$allowInitialPassword && must_change_password()) {
        fail(403, 'password_change_required', 'Спершу змініть стартовий пароль');
    }
}

function require_csrf(): void
{
    $given = (string)($_SERVER['HTTP_X_CSRF_TOKEN'] ?? '');
    $own   = (string)($_SESSION['csrf'] ?? '');
    if ($own === '' || $given === '' || !hash_equals($own, $given)) {
        fail(403, 'bad_csrf', 'Сесія застаріла. Оновіть сторінку та увійдіть знову');
    }
}

function json_body(): array
{
    $raw = file_get_contents('php://input', false, null, 0, 1024 * 1024);
    $data = json_decode($raw ?: '', true);
    if (!is_array($data)) { fail(400, 'bad_json', 'Некоректний запит'); }
    return $data;
}

/** Рядок з форми: лише коректний UTF-8, без керувальних символів, обрізаний до $max. */
function clean_text($v, int $max, bool $multiline = false): string
{
    if (!is_string($v)) { return ''; }
    if (!mb_check_encoding($v, 'UTF-8')) { return ''; }
    $v = str_replace(["\r\n", "\r"], "\n", $v);
    $v = preg_replace($multiline ? '/[^\P{C}\n]/u' : '/\p{C}/u', '', $v) ?? '';
    return mb_substr(trim($v), 0, $max);
}
