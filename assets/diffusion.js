(() => {
  'use strict';
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  document.querySelectorAll('.diffusion-widget[data-model="mode"]').forEach(widget => {
    const curve = widget.querySelector('.model-curve');
    const slider = widget.querySelector('[data-motion="time"]');
    const play = widget.querySelector('[data-motion="play"]');
    const speed = widget.querySelector('[data-motion="speed"]');
    const output = widget.querySelector('output');
    let playing = false, previous = null, frame = null, modelTime = 0;
    const render = tau => {
      modelTime = tau;
      const points = Array.from({length: 201}, (_, i) => {
        const x = i / 200;
        const u = 1 + 0.5 * Math.cos(Math.PI * x) * Math.exp(-(Math.PI ** 2) * tau);
        return `${70 + 550 * x},${150 - 180 * (u - 1)}`;
      });
      curve.setAttribute('points', points.join(' '));
      slider.value = String(tau);
      output.textContent = `τ = ${tau.toFixed(3)}; mean = 1.000`;
      widget.dataset.time = String(tau);
    };
    const pause = () => { playing = false; previous = null; cancelAnimationFrame(frame); play.textContent = 'Play'; play.setAttribute('aria-pressed', 'false'); };
    const tick = now => {
      if (!playing) return;
      const elapsed = previous === null ? 0 : (now - previous) / 1000;
      previous = now;
      const tau = Math.min(0.5, modelTime + elapsed * 0.05 * Number(speed.value));
      render(tau);
      if (tau >= 0.5) pause(); else frame = requestAnimationFrame(tick);
    };
    play.setAttribute('aria-pressed', 'false');
    play.addEventListener('click', () => {
      if (playing) return pause();
      if (modelTime >= 0.5) render(0);
      playing = true; previous = null; play.textContent = 'Pause'; play.setAttribute('aria-pressed', 'true');
      frame = requestAnimationFrame(tick);
    });
    slider.addEventListener('input', () => { pause(); render(Number(slider.value)); });
    widget.querySelector('[data-motion="reset"]').addEventListener('click', () => { pause(); render(0); });
    reduced.addEventListener('change', () => { if (reduced.matches) pause(); });
    document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
    addEventListener('beforeprint', pause);
    // Deterministic seeking is available for sampled-frame checks.
    widget.renderFrame = tau => { pause(); render(Math.min(0.5, Math.max(0, tau))); };
    render(0);
  });
})();
