import { isComplete } from './state.js';

const params = new URLSearchParams(location.search);
const seed = params.get('seed') ?? 'default';

const app = document.getElementById('app');
app.innerHTML = `
  <h1>Cryptography Puzzles</h1>
  <p>Seed: <code>${seed}</code></p>
  <p>Puzzle 1-1 status: ${isComplete('1-1') ? 'complete' : 'not started'}</p>
`;
