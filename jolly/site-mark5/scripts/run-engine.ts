import { runEngine } from '../lib/planning-engine.ts';
let input='';
try {
  for await(const chunk of process.stdin){input+=chunk;if(Buffer.byteLength(input)>16*1024*1024)throw new Error('Engine input exceeds 16 MiB.');}
  process.stdout.write(JSON.stringify(runEngine(JSON.parse(input))));
} catch(error) { process.stderr.write(`${error instanceof Error?error.message:'Engine failed'}\n`);process.exitCode=1; }
