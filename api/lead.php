<?php
/**
 * Приймання заявки з форми сайту (multipart/form-data).
 * «Прийнято» означає: заявку й файли записано на диск сервера.
 * Сповіщення (email/Telegram) надсилаються після цього і на відповідь не впливають.
 */
declare(strict_types=1);
define('LUMIS_API', true);
require __DIR__ . '/bootstrap.php';

require_method('POST');
require_same_origin();

$maxFile  = (int)cfg('max_file_size', 10 * 1024 * 1024);
$maxFiles = (int)cfg('max_files', 5);

// Якщо тіло перевищило post_max_size, PHP мовчки віддає порожні $_POST і $_FILES.
if (empty($_POST) && empty($_FILES) && (int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 0) {
    fail(413, 'too_large', 'Запит завеликий: зменште розмір або кількість файлів');
}

if (!rate_limit('lead', (int)cfg('lead_rate_max', 5), (int)cfg('lead_rate_window', 600), false)) {
    fail(429, 'too_many_requests', 'Забагато заявок за короткий час. Спробуйте за кілька хвилин');
}

// Приховане поле-пастка: людина його не бачить і не заповнює.
if (trim((string)($_POST['website'] ?? '')) !== '') {
    fail(400, 'rejected', 'Заявку відхилено');
}

$name    = clean_text($_POST['name'] ?? '', 100);
$phone   = clean_text($_POST['phone'] ?? '', 40);
$handle  = clean_text($_POST['handle'] ?? '', 120);
$order   = clean_text($_POST['order'] ?? '', 150);
$message = clean_text($_POST['message'] ?? '', 3000, true);
$calc    = clean_text($_POST['calc'] ?? '', 1000, true);
$method  = clean_text($_POST['method'] ?? '', 20);

$errors = [];
if (mb_strlen($name) < 2) { $errors['name'] = "Вкажіть ім'я"; }

if (!in_array($method, ['email', 'telegram', 'viber', 'instagram'], true)) {
    $errors['method'] = "Оберіть спосіб зв'язку";
}

$digits = preg_replace('/\D+/', '', $phone) ?? '';
$phoneOk = $phone !== '' && preg_match('/^[\d\s()+\-]+$/', $phone) && strlen($digits) >= 10 && strlen($digits) <= 15;
if ($phone !== '' && !$phoneOk) {
    $errors['phone'] = 'Перевірте номер: потрібно 10–15 цифр';
}

// Потрібен хоча б один робочий контакт для обраного способу зв'язку.
if (!isset($errors['method'])) {
    if ($method === 'email') {
        if ($handle === '' || !filter_var($handle, FILTER_VALIDATE_EMAIL)) { $errors['handle'] = 'Вкажіть коректний email'; }
    } elseif ($method === 'instagram') {
        if (!preg_match('/^@?[A-Za-z0-9._]{1,30}$/', $handle)) { $errors['handle'] = 'Вкажіть нік в Instagram'; }
    } elseif ($method === 'telegram') {
        if ($handle !== '' && !preg_match('/^@?[A-Za-z0-9_]{4,32}$/', $handle)) { $errors['handle'] = 'Перевірте нік у Telegram'; }
        if ($handle === '' && $phone === '') { $errors['phone'] = 'Вкажіть телефон або нік у Telegram'; }
    } elseif ($method === 'viber') {
        if ($phone === '') { $errors['phone'] = 'Для Viber потрібен номер телефону'; }
    }
}

// ── Файли ──
$allowed = [
    'jpg' => 'image', 'jpeg' => 'image', 'png' => 'image',
    'pdf' => 'doc', 'ai' => 'doc', 'eps' => 'doc', 'svg' => 'doc', 'zip' => 'archive',
];

/** Перевірка вмісту за сигнатурою: розширення в назві файлу нічого не гарантує. */
function content_matches(string $ext, string $path): bool
{
    $head = (string)@file_get_contents($path, false, null, 0, 4096);
    $is = fn(string $sig) => strncmp($head, $sig, strlen($sig)) === 0;
    switch ($ext) {
        case 'jpg': case 'jpeg': return $is("\xFF\xD8\xFF");
        case 'png': return $is("\x89PNG\r\n\x1A\n");
        case 'pdf': return $is('%PDF-');
        case 'ai':  return $is('%PDF-') || $is('%!PS');
        case 'eps': return $is('%!PS') || $is("\xC5\xD0\xD3\xC6");
        case 'zip': return $is("PK\x03\x04") || $is("PK\x05\x06");
        case 'svg': return stripos($head, '<svg') !== false && strpos($head, "\0") === false;
    }
    return false;
}

$incoming = [];
if (!empty($_FILES['files']) && is_array($_FILES['files']['name'])) {
    foreach ($_FILES['files']['name'] as $i => $orig) {
        $err = (int)$_FILES['files']['error'][$i];
        if ($err === UPLOAD_ERR_NO_FILE) { continue; }
        $incoming[] = [
            'name' => (string)$orig, 'tmp' => (string)$_FILES['files']['tmp_name'][$i],
            'size' => (int)$_FILES['files']['size'][$i], 'error' => $err,
        ];
    }
}

if (count($incoming) > $maxFiles) {
    $errors['files'] = "Можна додати не більше $maxFiles файлів";
} else {
    foreach ($incoming as $f) {
        $shown = mb_substr(clean_text($f['name'], 120), 0, 60);
        $ext = strtolower(pathinfo($f['name'], PATHINFO_EXTENSION));
        if (in_array($f['error'], [UPLOAD_ERR_INI_SIZE, UPLOAD_ERR_FORM_SIZE], true) || $f['size'] > $maxFile) {
            $errors['files'] = "Файл «{$shown}» завеликий (максимум " . round($maxFile / 1048576) . ' МБ)'; break;
        }
        if ($f['error'] !== UPLOAD_ERR_OK || !is_uploaded_file($f['tmp'])) {
            $errors['files'] = "Файл «{$shown}» не вдалося отримати. Спробуйте ще раз"; break;
        }
        if ($f['size'] === 0) { $errors['files'] = "Файл «{$shown}» порожній"; break; }
        if (!isset($allowed[$ext])) { $errors['files'] = "Тип файлу «{$shown}» не підтримується"; break; }
        if (!content_matches($ext, $f['tmp'])) { $errors['files'] = "Вміст файлу «{$shown}» не відповідає його типу"; break; }
    }
}

if ($errors) {
    fail(422, 'validation', 'Перевірте заповнення форми', ['fields' => $errors]);
}

// ── Запис на диск ──
$id  = date('Ymd-His') . '-' . bin2hex(random_bytes(3));
$dir = data_dir() . '/leads/' . $id;
if (!@mkdir($dir, 0750, true)) {
    fail(500, 'storage_failed', 'Сервер не зміг зберегти заявку. Спробуйте ще раз');
}

$saved = [];
foreach ($incoming as $n => $f) {
    $ext = strtolower(pathinfo($f['name'], PATHINFO_EXTENSION));
    // На диску — нейтральна назва без розширення: такий файл не виконається як код.
    $stored = ($n + 1) . '.bin';
    if (!move_uploaded_file($f['tmp'], "$dir/$stored")) {
        array_map('unlink', glob("$dir/*") ?: []); @rmdir($dir);
        fail(500, 'storage_failed', 'Сервер не зміг зберегти файли. Спробуйте ще раз');
    }
    @chmod("$dir/$stored", 0640);
    $base = preg_replace('/[^\p{L}\p{N} ._()\-]+/u', '_', pathinfo($f['name'], PATHINFO_FILENAME)) ?? 'file';
    $saved[] = ['n' => $n + 1, 'name' => mb_substr(trim($base, ' .') ?: 'file', 0, 80) . '.' . $ext, 'size' => $f['size'], 'ext' => $ext];
}

$lead = [
    'id' => $id, 'created_at' => date('c'), 'ip' => client_ip(),
    'name' => $name, 'phone' => $phone, 'method' => $method, 'handle' => $handle,
    'order' => $order, 'message' => $message, 'calc' => $calc, 'files' => $saved,
    'notify' => ['email' => null, 'telegram' => null],
];
if (!write_json("$dir/lead.json", $lead)) {
    array_map('unlink', glob("$dir/*") ?: []); @rmdir($dir);
    fail(500, 'storage_failed', 'Сервер не зміг зберегти заявку. Спробуйте ще раз');
}
rate_limit('lead', (int)cfg('lead_rate_max', 5), (int)cfg('lead_rate_window', 600), true);

// ── Сповіщення (збій тут заявку не скасовує: вона вже збережена) ──
$labels = ['email' => 'Email', 'telegram' => 'Telegram', 'viber' => 'Viber', 'instagram' => 'Instagram'];
$text = "Нова заявка LUMIS № $id\n"
      . "Ім'я: $name\nТелефон: " . ($phone ?: '—') . "\n"
      . "Зв'язок: {$labels[$method]}" . ($handle ? " ($handle)" : '') . "\n"
      . 'Тип замовлення: ' . ($order ?: '—') . "\n"
      . 'Повідомлення: ' . ($message ?: '—') . "\n"
      . ($calc ? "\n$calc\n" : '')
      . 'Файлів: ' . count($saved) . ($saved ? ' (доступні в адмін-панелі, вкладка «Заявки»)' : '') . "\n";

$to = (string)cfg('lead_email_to', '');
if ($to !== '' && filter_var($to, FILTER_VALIDATE_EMAIL) && function_exists('mail')) {
    $from = (string)cfg('lead_email_from', '');
    if ($from === '' || !filter_var($from, FILTER_VALIDATE_EMAIL)) {
        $host = preg_replace('/[^a-z0-9.\-]/i', '', explode(':', (string)($_SERVER['HTTP_HOST'] ?? 'localhost'))[0]);
        $from = 'noreply@' . ($host ?: 'localhost');
    }
    $headers = "From: LUMIS <$from>\r\nMIME-Version: 1.0\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: 8bit";
    $subject = '=?UTF-8?B?' . base64_encode("Заявка LUMIS № $id") . '?=';
    $lead['notify']['email'] = @mail($to, $subject, $text, $headers);
}

$token = (string)cfg('telegram_bot_token', '');
$chat  = (string)cfg('telegram_chat_id', '');
if ($token !== '' && $chat !== '' && function_exists('curl_init')) {
    $ch = curl_init(rtrim((string)cfg('telegram_api_base', 'https://api.telegram.org'), '/') . "/bot$token/sendMessage");
    curl_setopt_array($ch, [
        CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 6, CURLOPT_CONNECTTIMEOUT => 4,
        CURLOPT_POSTFIELDS => ['chat_id' => $chat, 'text' => $text, 'disable_web_page_preview' => 'true'],
    ]);
    $resp = curl_exec($ch);
    $lead['notify']['telegram'] = $resp !== false && curl_getinfo($ch, CURLINFO_HTTP_CODE) === 200;
    curl_close($ch);
}
write_json("$dir/lead.json", $lead);

json_out(200, ['ok' => true, 'id' => $id, 'files' => count($saved)]);
