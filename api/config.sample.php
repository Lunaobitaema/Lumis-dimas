<?php
/**
 * Зразок налаштувань. Скопіюйте у config.php та заповніть.
 * Файл повертає масив і нічого не виводить, тож відкрити його через браузер неможливо.
 */
return [
    // Куди зберігати заявки, сесії та опублікований контент.
    // Найбезпечніше — каталог ПОЗА коренем сайту, наприклад '/home/USER/lumis-data'.
    'storage_dir' => __DIR__ . '/../storage',

    // Публічні зображення з адмін-панелі (портфоліо, карусель).
    'uploads_dir' => __DIR__ . '/../uploads',
    'uploads_url' => 'uploads',

    // Хеш стартового пароля: php api/tools/hash.php 'ваш-пароль'
    // Після першого входу панель вимагає задати власний пароль.
    'admin_password_hash' => '',

    // Сповіщення про нову заявку. Порожній рядок вимикає канал.
    'lead_email_to'   => '',
    'lead_email_from' => '',            // порожньо = noreply@<домен сайту>

    'telegram_bot_token' => '',         // токен бота від @BotFather
    'telegram_chat_id'   => '',         // id чату, куди бот пише
    'telegram_api_base'  => 'https://api.telegram.org',

    // true лише якщо сайт стоїть за Cloudflare/проксі: тоді IP відвідувача
    // береться із заголовка CF-Connecting-IP, а HTTPS — з X-Forwarded-Proto.
    'trust_proxy_headers' => false,

    // Обмеження
    'lead_rate_max'    => 5,            // заявок з одного IP
    'lead_rate_window' => 600,          // за стільки секунд
    'max_file_size'    => 10 * 1024 * 1024,
    'max_files'        => 5,
];
