// api/flux.js — Vercel serverless function
// Flux API proxy to avoid CORS issues from browser

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { prompt, apiKey } = req.body;

  if (!prompt || !apiKey) {
    return res.status(400).json({ error: 'prompt and apiKey required' });
  }

  try {
    // Step 1: Submit generation request to Flux
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

    if (!submitRes.ok) {
      const err = await submitRes.text();
      return res.status(submitRes.status).json({ error: `Flux submit error: ${err}` });
    }

    const submitData = await submitRes.json();
    const requestId = submitData.id;

    if (!requestId) {
      return res.status(500).json({ error: 'No request ID from Flux' });
    }

    // Step 2: Poll for result (max 60s)
    let imageUrl = null;
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 2000));

      const pollRes = await fetch(`https://api.bfl.ml/v1/get_result?id=${requestId}`, {
        headers: { 'X-Key': apiKey }
      });

      if (!pollRes.ok) continue;

      const pollData = await pollRes.json();

      if (pollData.status === 'Ready' && pollData.result?.sample) {
        imageUrl = pollData.result.sample;
        break;
      }
      if (pollData.status === 'Error' || pollData.status === 'Failed') {
        return res.status(500).json({ error: 'Flux generation failed' });
      }
    }

    if (!imageUrl) {
      return res.status(504).json({ error: 'Flux generation timed out' });
    }

    return res.status(200).json({ imageUrl });

  } catch (err) {
    console.error('Flux API error:', err);
    return res.status(500).json({ error: err.message });
  }
}
