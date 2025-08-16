# SSL Certificates

Цей каталог містить SSL сертифікати для HTTPS.

## Для development

Створіть self-signed сертифікати:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/C=UA/ST=Ukraine/L=Kyiv/O=GraphRAG/OU=IT/CN=localhost"
```

## Для production

Замініть self-signed сертифікати на валідні від Let's Encrypt або іншого CA:

1. cert.pem - публічний сертифікат
2. key.pem - приватний ключ

## Безпека

- Ніколи не комітьте реальні приватні ключі в git
- Використовуйте відповідні права доступу (600 для ключів)
- Регулярно оновлюйте сертифікати
