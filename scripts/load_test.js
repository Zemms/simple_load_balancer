import http from 'k6/http';
import { check } from 'k6';

export const options = {
  // Пороговые значения можно оставить прежними или смягчить,
  // если вы ожидаете, что на пике производительность немного просядет.
  thresholds: {
    'http_req_failed': ['rate<0.01'], // Доля ошибок < 1%
    'http_req_duration': ['p(95)<500'], // 95% запросов быстрее 500ms
  },

  scenarios: {
    // Назовем сценарий 'peak_load'
    peak_load: {
      executor: 'ramping-arrival-rate',

      // Настройки для управления частотой запросов
      startRate: 50,    // Начинаем с 50 RPS
      timeUnit: '1s', // Считаем запросы в секунду

      // Выделяем ресурсы для k6, чтобы он мог достичь цели
      preAllocatedVUs: 500,  // Начинаем с 500 "готовых" пользователей
      maxVUs: 2000,        // Максимум можем использовать 2000 пользователей

      // Этапы теста
      stages: [
        // 1. Плавный разгон до 500 RPS за 30 секунд
        { duration: '30s', target: 500 },
        // 2. Удержание нагрузки в 500 RPS в течение 1 минуты для "прогрева"
        { duration: '1m', target: 500 },
        // 3. Плавный разгон до пиковой нагрузки в 1500 RPS за 30 секунд
        { duration: '30s', target: 1500 },
        // 4. Удержание пиковой нагрузки в 1500 RPS в течение 1 минуты
        { duration: '1m', target: 1500 },
        // 5. Плавное снижение нагрузки до нуля за 30 секунд
        { duration: '30s', target: 0 },
      ],
    },
  },
};

export default function () {
  const videoUrl = 'http://s1.origin-cluster/video/1488/xcg2djHckad.m3u8';

  const res = http.get(
    `http://localhost:8000/?video_url=${encodeURIComponent(videoUrl)}`,
    {
      redirects: 0,
      tags: { name: 'GET /' } // Группируем запросы для чистоты отчета
    }
  );

  // Проверяем, что ответ корректный
  check(res, {
    'status is 307': (r) => r.status === 307,
    'has location header': (r) => r.headers['Location'] !== undefined,
  });

  // sleep(1) здесь не нужен, так как executor сам управляет частотой запросов.
}
