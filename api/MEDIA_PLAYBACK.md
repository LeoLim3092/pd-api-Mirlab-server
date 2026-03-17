# Playing video and audio from results (after login)

Media files under the results root (e.g. `/mnt/pd_app/results` or `/mnt/results`) can be streamed to the frontend after the user logs in. All endpoints require JWT: send `Authorization: Bearer <access_token>`.

## 1. List available media for a patient

**GET** `/api/list_result_media?pid=<patient_id>`

Returns folders and files under `results/{patient_name}/` so you can build a list of playable items.

Example response:
```json
{
  "patient_name": "Leo",
  "folders": [
    { "folder": "2024-01-15_10-30-00", "files": ["result.png", "vis_gait_extraction.png"] }
  ]
}
```

## 2. Stream a file (video / audio / image)

**GET** `/api/get_media?folder_name=<path>&file_name=<name>`

- `folder_name`: path under results, e.g. `Leo` or `Leo/2024-01-15_10-30-00`
- `file_name`: file name only (e.g. `result.png`, `recording.wav`)

Also supports **POST** with the same params in body (form or JSON).

Content-Type is set automatically from extension (e.g. `video/mp4`, `audio/wav`, `image/png`).

## 3. Frontend: play in `<video>` or `<audio>`

Browsers cannot send auth headers for a plain `src` URL. Use **fetch + blob URL**:

```javascript
async function getMediaUrl(apiBase, accessToken, folderName, fileName) {
  const params = new URLSearchParams({ folder_name: folderName, file_name: fileName });
  const res = await fetch(`${apiBase}/get_media?${params}`, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  if (!res.ok) throw new Error('Failed to load media');
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

// Usage: after login you have accessToken
const url = await getMediaUrl(API_BASE, accessToken, 'Leo/2024-01-15_10-30-00', 'result.png');
document.querySelector('img#preview').src = url;

// For video
const videoUrl = await getMediaUrl(API_BASE, accessToken, 'Leo/2024-01-15_10-30-00', 'some.mp4');
document.querySelector('video').src = videoUrl;

// For audio
const audioUrl = await getMediaUrl(API_BASE, accessToken, 'Leo', 'recording.wav');
document.querySelector('audio').src = audioUrl;

// When done (e.g. on page leave), revoke to free memory:
// URL.revokeObjectURL(url);
```

## 4. Legacy endpoint

**GET** or **POST** `/api/get_video` with `folder_name` and `file_name` — same as `get_media`; use `get_media` for both video and audio.

## 5. Using a different results path (`/mnt/results`)

On the server, set the environment variable before starting Django:

```bash
export RESULTS_MEDIA_ROOT=/mnt/results
```

Then all of the above endpoints will serve from `/mnt/results` instead of `/mnt/pd_app/results`.
