<?php
/**
 * Опублікований контент сайту.
 * GET  — відкритий для всіх відвідувачів.
 * POST — лише для адміністратора (сесія + CSRF-токен).
 */
declare(strict_types=1);
define('LUMIS_API', true);
require __DIR__ . '/bootstrap.php';

$method = require_method('GET', 'POST');
$file = data_dir() . '/content.json';

if ($method === 'GET') {
    $data = read_json($file, null);
    json_out(200, ['ok' => true, 'content' => $data['content'] ?? null, 'updated_at' => $data['updated_at'] ?? null]);
}

require_same_origin();
require_admin();
require_csrf();
$in = json_body();

function backup_content(string $file): void
{
    if (!is_file($file)) { return; }
    $dir = data_dir() . '/backups';
    @copy($file, $dir . '/content-' . date('Ymd-His') . '.json');
    $all = glob($dir . '/content-*.json') ?: [];
    sort($all);
    foreach (array_slice($all, 0, max(0, count($all) - 30)) as $old) { @unlink($old); }
}

if (($in['action'] ?? '') === 'reset') {
    backup_content($file);
    if (is_file($file) && !@unlink($file)) { fail(500, 'write_failed', 'Не вдалося скинути контент'); }
    json_out(200, ['ok' => true, 'content' => null]);
}

$src = $in['content'] ?? null;
if (!is_array($src)) { fail(400, 'bad_content', 'Некоректні дані'); }

$errors = [];
$out = ['fields' => [], 'colors' => [], 'toggles' => [], 'carousel' => [], 'portfolioImages' => []];
$imgRe = '~^' . preg_quote((string)cfg('uploads_url', 'uploads'), '~') . '/[a-f0-9]{32}\.(jpg|png|webp)$~';

// Текстові поля: лише відомі ключі, лише рядки, з обмеженням довжини.
$long = '/^(edit-hero-sub|edit-about-p[12]|step-desc-[0-3])$/';
foreach ((array)($src['fields'] ?? []) as $key => $val) {
    if (!is_string($key) || !preg_match('/^(edit-[a-z0-9-]{1,30}|pi-(name|type)-[0-5]|step-(name|desc)-[0-3])$/', $key)) { continue; }
    $isLong = (bool)preg_match($long, $key);
    $out['fields'][$key] = clean_text($val, $isLong ? 800 : 160, $isLong);
}
$f = $out['fields'];
if (isset($f['edit-email']) && $f['edit-email'] !== '' && !filter_var($f['edit-email'], FILTER_VALIDATE_EMAIL)) {
    $errors['edit-email'] = 'Некоректний email';
}
if (isset($f['edit-instagram']) && $f['edit-instagram'] !== '' && !preg_match('~^https://[A-Za-z0-9.\-]+(/[^\s"\'<>]*)?$~', $f['edit-instagram'])) {
    $errors['edit-instagram'] = 'Посилання має починатися з https://';
}
if (isset($f['edit-phone']) && $f['edit-phone'] !== '' && !preg_match('/^[\d\s()+\-]{7,25}$/', $f['edit-phone'])) {
    $errors['edit-phone'] = 'Некоректний номер телефону';
}
if (isset($f['edit-brand']) && $f['edit-brand'] === '') { $errors['edit-brand'] = 'Назва не може бути порожньою'; }

foreach (['gold', 'bg'] as $c) {
    $v = $src['colors'][$c] ?? null;
    if ($v === null || $v === '') { continue; }
    if (is_string($v) && preg_match('/^#[0-9a-fA-F]{6}$/', $v)) { $out['colors'][$c] = strtolower($v); }
    else { $errors["color-$c-hex"] = 'Колір у форматі #rrggbb'; }
}
foreach (['carousel', 'process', 'instagram', 'cursor'] as $t) {
    $out['toggles'][$t] = !array_key_exists($t, (array)($src['toggles'] ?? [])) || (bool)$src['toggles'][$t];
}

$slides = array_values((array)($src['carousel'] ?? []));
if (count($slides) < 1 || count($slides) > 20) { $errors['carousel'] = 'У каруселі має бути від 1 до 20 слайдів'; }
foreach (array_slice($slides, 0, 20) as $s) {
    $label = clean_text($s['label'] ?? '', 60);
    $image = is_string($s['image'] ?? null) ? $s['image'] : '';
    if ($image !== '' && !preg_match($imgRe, $image)) { $image = ''; }
    $out['carousel'][] = ['label' => $label !== '' ? $label : 'Слайд', 'image' => $image];
}
for ($i = 0; $i < 6; $i++) {
    $image = $src['portfolioImages'][$i] ?? '';
    $out['portfolioImages'][] = (is_string($image) && preg_match($imgRe, $image)) ? $image : '';
}

if ($errors) { fail(422, 'validation', 'Перевірте виділені поля', ['fields' => $errors]); }

backup_content($file);
$payload = ['updated_at' => date('c'), 'content' => $out];
if (!write_json($file, $payload)) { fail(500, 'write_failed', 'Сервер не зміг зберегти зміни'); }
json_out(200, ['ok' => true, 'content' => $out, 'updated_at' => $payload['updated_at']]);
