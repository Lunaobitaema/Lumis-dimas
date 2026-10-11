<?php
// Запуск лише з командного рядка: php api/tools/hash.php 'новий-пароль'
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
if (empty($argv[1]) || mb_strlen($argv[1]) < 10) { fwrite(STDERR, "Пароль має містити щонайменше 10 символів\n"); exit(1); }
echo password_hash($argv[1], PASSWORD_DEFAULT), "\n";
