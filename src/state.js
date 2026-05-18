const STORAGE_KEY = 'crypt-progress';

function load() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}');
  } catch {
    return {};
  }
}

function save(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

const state = load();

export function markComplete(puzzleId) {
  state[puzzleId] = true;
  save(state);
}

export function isComplete(puzzleId) {
  return Boolean(state[puzzleId]);
}

export function reset() {
  Object.keys(state).forEach((k) => delete state[k]);
  localStorage.removeItem(STORAGE_KEY);
}
