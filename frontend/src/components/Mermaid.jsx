import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'monospace',
});

export default function Mermaid({ chart }) {
  const [svg, setSvg] = useState('');
  const [error, setError] = useState(null);
  // generate a unique ID once per component instance
  const containerId = useRef(`mermaid-${Math.random().toString(36).substring(2, 9)}`).current;

  useEffect(() => {
    if (!chart) return;
    let isMounted = true;

    const renderChart = async () => {
      try {
        const { svg: renderedSvg } = await mermaid.render(containerId, chart);
        if (isMounted) {
          setSvg(renderedSvg);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to render mermaid diagram');
          console.error('Mermaid render error:', err);
        }
      }
    };

    renderChart();

    return () => {
      isMounted = false;
    };
  }, [chart, containerId]);

  if (error) {
    return <div className="text-red-400 text-xs font-mono p-4 bg-red-500/10 rounded-xl border border-red-500/20 whitespace-pre-wrap">{error}</div>;
  }

  return (
    <div className="mermaid-wrapper w-full flex justify-center bg-slate-900/50 rounded-xl border border-white/5 p-8 mb-6 overflow-x-auto custom-scrollbar" dangerouslySetInnerHTML={{ __html: svg }} />
  );
}
