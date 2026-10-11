<?php
/** Завантаження зображення для портфоліо/каруселі. Лише адміністратор. */
declare(strict_types=1);
define('LUMIS_API', true);
require __DIR__ . '/bootstrap.php';

require_method('POST');
require_same_origin();
require_admin();
require_csrf();

if (empty($_FILES['image']) && (int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 0) {
    fail(413, 'too_large', 'Файл завеликий (максимум 5 МБ)');
}
$f = $_FILES['image'] ?? null;
if (!$f || is_array($f['name'])) { fail(400, 'no_file', 'Файл не отримано'); }
if (in_array((int)$f['error'], [UPLOAD_ERR_INI_SIZE, UPLOAD_ERR_FORM_SIZE], true) || (int)$f['size'] > 5 * 1024 * 1024) {
    fail(413, 'too_large', 'Файл завеликий (максимум 5 МБ)');
}
if ((int)$f['error'] !== UPLOAD_ERR_OK || !is_uploaded_file($f['tmp_name'])) { fail(400, 'upload_failed', 'Файл не вдалося отримати'); }

// Тип визначаємо за вмістом, а не за назвою чи заголовком браузера.
$info = @getimagesize($f['tmp_name']);
$types = [IMAGETYPE_JPEG => 'jpg', IMAGETYPE_PNG => 'png', IMAGETYPE_WEBP => 'webp'];
if (!$info || !isset($types[$info[2]])) { fail(422, 'bad_type', 'Підтримуються лише JPG, PNG та WEBP'); }
if ($info[0] < 1 || $info[1] < 1 || $info[0] > 8000 || $info[1] > 8000) { fail(422, 'bad_size', 'Зображення завелике за розмірами (до 8000 px)'); }

$dir = rtrim((string)cfg('uploads_dir', __DIR__ . '/../uploads'), '/');
if (!is_dir($dir) && !@mkdir($dir, 0755, true)) { fail(500, 'storage_failed', 'Каталог зображень недоступний'); }
$name = bin2hex(random_bytes(16)) . '.' . $types[$info[2]];
if (!move_uploaded_file($f['tmp_name'], "$dir/$name")) { fail(500, 'storage_failed', 'Не вдалося зберегти зображення'); }
@chmod("$dir/$name", 0644);

json_out(200, ['ok' => true, 'url' => trim((string)cfg('uploads_url', 'uploads'), '/') . '/' . $name]);
