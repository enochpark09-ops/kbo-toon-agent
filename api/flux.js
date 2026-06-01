export const config = { maxDuration: 60 };

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  // 환경변수에서 API 키 읽기 (브라우저에 키 노출 없음)
  const apiKey = process.env.BFL_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'BFL_API_KEY 환경변수가 설정되지 않았습니다' });

  const { prompt, action, pollingUrl } = req.body;

  try {
    // 폴링
    if (action === 'poll') {
      if (!pollingUrl) return res.status(400).json({ error: 'pollingUrl required' });
      const pollRes = await fetch(pollingUrl, {
        headers: { 'X-Key': apiKey, 'accept': 'application/json' }
      });
      return res.status(200).json(await pollRes.json());
    }

    // 생성 요청
    if (!prompt) return res.status(400).json({ error: 'prompt required' });

    const submitRes = await fetch('https://api.bfl.ai/v1/flux-pro-1.1', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Key': apiKey,
        'accept': 'application/json'
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
    if (!submitRes.ok) return res.status(submitRes.status).json({ error: submitData });

    return res.status(200).json({
      requestId: submitData.id,
      pollingUrl: submitData.polling_url
    });

  } catch (err) {
    console.error('Flux error:', err);
    return res.status(500).json({ error: err.message });
  }
}
