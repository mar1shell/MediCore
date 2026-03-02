import { http, HttpResponse } from 'msw'
import { MOCK_UPLOAD_RESPONSE, MOCK_SESSION_DATA } from './fixtures'

const BASE = 'http://localhost:8000'

export const handlers = [
  // POST /upload-chart
  http.post(`${BASE}/upload-chart`, () =>
    HttpResponse.json(MOCK_UPLOAD_RESPONSE, { status: 200 }),
  ),

  // GET /sessions/:id
  http.get(`${BASE}/sessions/:sessionId`, () =>
    HttpResponse.json(MOCK_SESSION_DATA, { status: 200 }),
  ),

  // DELETE /sessions/:id
  http.delete(`${BASE}/sessions/:sessionId`, () =>
    new HttpResponse(null, { status: 204 }),
  ),
]
