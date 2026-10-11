<?php
/** Перегляд заявок і вкладень. Лише адміністратор. */
declare(strict_types=1);
define('LUMIS_API', true);
require __DIR__ . '/bootstrap.php';

$method = require_method('GET', 'POST');
$base = data_dir() . '/leads';
$idRe = '/^\d{8}-\d{6}-[a-f0-9]{6}$/';

if ($method === 'GET') {
    require_admin();
    $action = (string)($_GET['action'] ?? 'list');

    if ($action === 'file') {
        $id = (string)($_GET['id'] ?? '');
        $n  = (int)($_GET['n'] ?? 0);
        if (!preg_match($idRe, $id)) { fail(404, 'not_found', 'Файл не знайдено'); }
        $lead = read_json("$base/$id/lead.json", null);
        $meta = null;
        foreach ((array)($lead['files'] ?? []) as $f) { if ((int)$f['n'] === $n) { $meta = $f; } }
        $path = "$base/$id/$n.bin";
        if (!$meta || !is_file($path)) { fail(404, 'not_found', 'Файл не знайдено'); }
        // Завжди як вкладення: браузер зберігає файл, а не відкриває його на домені сайту.
        header('Content-Type: application/octet-stream');
        header('Content-Length: ' . filesize($path));
        header("Content-Disposition: attachment; filename=\"file-$n.{$meta['ext']}\"; filename*=UTF-8''" . rawurlencode($meta['name']));
        header("Content-Security-Policy: default-src 'none'; sandbox");
        readfile($path);
        exit;
    }

    $dirs = glob($base . '/*', GLOB_ONLYDIR) ?: [];
    rsort($dirs);
    $total = count($dirs);
    $leads = [];
    foreach (array_slice($dirs, 0, 100) as $d) {
        $lead = read_json("$d/lead.json", null);
        if (is_array($lead)) { $leads[] = $lead; }
    }
    json_out(200, ['ok' => true, 'total' => $total, 'leads' => $leads]);
}

require_same_origin();
require_admin();
require_csrf();
$in = json_body();
if (($in['action'] ?? '') === 'delete') {
    $id = (string)($in['id'] ?? '');
    if (!preg_match($idRe, $id) || !is_dir("$base/$id")) { fail(404, 'not_found', 'Заявку не знайдено'); }
    array_map('unlink', glob("$base/$id/*") ?: []);
    if (!@rmdir("$base/$id")) { fail(500, 'delete_failed', 'Не вдалося видалити заявку'); }
    json_out(200, ['ok' => true]);
}
fail(400, 'unknown_action', 'Невідома дія');
