'use client'
import { useState, useEffect } from 'react'
export function useApi(url, interval = 10000) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    let alive = true
    const fetch_ = () => fetch(url)
      .then(r => r.json())
      .then(d => { if (alive) { setData(d); setError(null); setLoading(false) } })
      .catch(e => { if (alive) { setError(e.message); setLoading(false) } })
    fetch_()
    const t = setInterval(fetch_, interval)
    return () => { alive = false; clearInterval(t) }
  }, [url, interval])
  return { data, error, loading }
}
