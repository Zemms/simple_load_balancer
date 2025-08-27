import http from 'k6/http';
import { check } from 'k6';
import { randomItem, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// --- Опции теста ---
export const options = {
  thresholds: {
    'http_req_failed': ['rate<0.02'], // Допускаем чуть больше ошибок из-за возможных 404
    'http_req_duration': ['p(95)<500'],
  },
  scenarios: {
    peak_load: {
      executor: 'ramping-arrival-rate',
      startRate: 50,
      timeUnit: '1s',
      preAllocatedVUs: 500,
      maxVUs: 2000,
      stages: [
        { duration: '30s', target: 500 },
        { duration: '1m', target: 500 },
        { duration: '30s', target: 1500 },
        { duration: '1m', target: 1500 },
        { duration: '30s', target: 0 },
      ],
    },
  },
};

// --- Функция подготовки (SETUP) ---
export function setup() {
  console.log('--- Running Setup: Creating CDN and Origin servers ---');

  const headers = { 'Content-Type': 'application/json' };

  // 1. Создаем CDN сервер
  const cdnPayload = JSON.stringify({
    host_name: "my-cdn.com",
    default_redirecting_ratio: 20,
  });
  const cdnRes = http.post('http://localhost:8000/cdn/', cdnPayload, { headers });
  check(cdnRes, { 'setup: CDN server created': (r) => r.status === 200 });

  // 2. Создаем несколько Origin серверов
  const originServersToCreate = [
    { name: 's1', redirecting_ratio: 10 },
    { name: 's2', redirecting_ratio: 5 },
    { name: 's3', redirecting_ratio: null }, // Будет использовать дефолтный ratio от CDN
    { name: 's4', redirecting_ratio: 50 },
    { name: 's5', redirecting_ratio: 100 },
  ];

  const createdOriginServers = [];

  for (const server of originServersToCreate) {
    const originPayload = JSON.stringify(server);
    const originRes = http.post('http://localhost:8000/origin/', originPayload, { headers });
    check(originRes, { [`setup: Origin server ${server.name} created`]: (r) => r.status === 200 });
    createdOriginServers.push(server);
  }

  console.log('--- Setup Complete ---');

  // Передаем список созданных серверов в основной тест
  return { originServers: createdOriginServers };
}

// --- Основная функция теста (VU code) ---
export default function (data) {
  let serverName;

  // 90% запросов будут к существующим серверам, 10% - к несуществующему
  if (Math.random() < 0.9) {
    // Выбираем случайный сервер из тех, что создали в setup
    serverName = randomItem(data.originServers).name;
  } else {
    // Эмулируем промах кеша, запрашивая несуществующий сервер
    serverName = `s${randomIntBetween(90, 99)}`;
  }

  // Генерируем случайный путь для URL
  const videoId = randomIntBetween(1000, 9999);
  const videoHash = Math.random().toString(36).substring(2, 15);

  const videoUrl = `http://${serverName}.origin-cluster/video/${videoId}/${videoHash}.m3u8`;

  const res = http.get(
    `http://localhost:8000/?video_url=${encodeURIComponent(videoUrl)}`,
    {
      redirects: 0,
      tags: {
        name: 'GET /balance_request', // Группируем запросы
        server: serverName.startsWith('s9') ? 'non-existent' : 'existent' // Добавляем тег для анализа
      }
    }
  );

  check(res, {
    'status is 307': (r) => r.status === 307,
    'has location header': (r) => r.headers['Location'] !== undefined,
  });
}

// --- Функция завершения (TEARDOWN) (опционально) ---
export function teardown(data) {
  console.log('--- Running Teardown ---');
  // Здесь можно было бы удалить созданные в setup сущности,
  // но для простоты оставим это пустым.
}
