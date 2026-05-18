const SEED_RE = /^[a-zA-Z0-9-]{1,16}$/;

function djb2(str) {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = (Math.imul(hash, 33) + str.charCodeAt(i)) >>> 0;
  }
  return hash;
}

function makeMulberry32(seed) {
  let state = seed >>> 0;
  return function () {
    state = (state + 0x6D2B79F5) >>> 0;
    let z = state;
    z = Math.imul(z ^ (z >>> 15), z | 1) >>> 0;
    z = (z ^ (z + (Math.imul(z ^ (z >>> 7), z | 61) >>> 0))) >>> 0;
    return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
  };
}

export function validateSeed(seed) {
  return typeof seed === 'string' && SEED_RE.test(seed);
}

export function dailySeed() {
  return new Date().toISOString().slice(0, 10);
}

export function seedFromUrl() {
  const param = new URLSearchParams(window.location.search).get('seed');
  return param && validateSeed(param) ? param.toLowerCase() : dailySeed();
}

export function makeRng(seed) {
  return makeMulberry32(djb2(seed.toLowerCase()));
}

export function randInt(rng, min, max) {
  return Math.floor(rng() * (max - min)) + min;
}
