/** Preserve the tsci CLI table losslessly without flooding stdout.
 * This changes only table serialization, not circuit generation or simulation.
 */
import { mkdirSync, writeFileSync } from 'node:fs'
import { gzipSync } from 'node:zlib'
const originalLog = console.log.bind(console)
console.log = (...args: unknown[]) => {
  if (args.length === 1 && typeof args[0] === 'string' && /^Index\s+time\s/.test(args[0])) {
    mkdirSync('build/tsci', { recursive: true })
    writeFileSync('build/tsci/hv-table.txt.gz', gzipSync(args[0], { level: 3 }))
    originalLog('Saved complete tsci analog result table: build/tsci/hv-table.txt.gz')
  } else originalLog(...args)
}
