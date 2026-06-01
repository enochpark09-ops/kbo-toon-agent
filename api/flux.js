// api/flux.js — Vercel serverless function
// Flux API: submit → return requestId immediately (polling은 브라우저에서)

export const config = { maxDuration: 60 };

export default async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { prompt, apiKey, action } = req.body;
  if (!apiKey) return res.status(400).json({ error: 'apiKey required' });

  try {
    // action=poll: 결과 폴링
    if (action === 'poll') {
      const { requestId } = req.body;
      const pollRes = await fetch(`https://api.bfl.ml/v1/get_result?id=${requestId}`, {
        headers: { 'X-Key': apiKey }
      });
      const pollData = await pollRes.json();
      return res.status(200).json(pollData);
    }

    // action=submit (기본): 생성 요청
    if (!prompt) return res.status(400).json({ error: 'prompt required' });

    const submitRes = await fetch('https://api.bfl.ml/v1/flux-pro-1.1', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Key': apiKey
      },
      body: JSON.stringify({
        prompt,
        width: 768,
        height: 1024,
        prompt_upsampling: false,
        safety_tolerance: 2,
        output_format: 'jpeg'
      })
    });

    const submitData = await submitRes.json();
    if (!submitRes.ok) {
      return res.status(submitRes.status).json({ error: submitData });
    }

    return res.status(200).json({ requestId: submitData.id });

  } catch (err) {
    console.error('Flux API error:', err);
    return res.status(500).json({ error: err.message });
  }
}
