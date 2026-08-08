import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { PHASES, TOUR } from "./tour/tour-data.js";

const repositoryRoot = fileURLToPath(new URL("../../", import.meta.url));
const errors = [];

function findOccurrence(lines, anchor, occurrence = 1, from = 0) {
  let remaining = occurrence;
  for (let index = from; index < lines.length; index += 1) {
    if (lines[index].includes(anchor)) {
      remaining -= 1;
      if (remaining === 0) return index;
    }
  }
  return -1;
}

const ids = new Set();
const phaseIds = new Set(PHASES.map((phase) => phase.id));

for (const [stepIndex, step] of TOUR.entries()) {
  const label = `step ${stepIndex + 1} (${step.id})`;
  if (ids.has(step.id)) errors.push(`${label}: duplicate id`);
  ids.add(step.id);
  if (!phaseIds.has(step.phase)) errors.push(`${label}: unknown phase ${step.phase}`);
  if (!step.notes.length) errors.push(`${label}: no line notes`);

  let source;
  try {
    source = await readFile(`${repositoryRoot}/${step.file}`, "utf8");
  } catch (error) {
    errors.push(`${label}: cannot read ${step.file}: ${error.message}`);
    continue;
  }

  const lines = source.replaceAll("\r\n", "\n").split("\n");
  const start = findOccurrence(lines, step.anchor, step.occurrence ?? 1);
  if (start < 0) {
    errors.push(`${label}: start anchor not found: ${step.anchor}`);
    continue;
  }
  const end = step.endAnchor
    ? findOccurrence(lines, step.endAnchor, step.endOccurrence ?? 1, start)
    : start;
  if (end < start) {
    errors.push(`${label}: end anchor not found after start: ${step.endAnchor}`);
    continue;
  }
  const first = Math.max(0, start - (step.contextBefore ?? 2));
  const last = Math.min(lines.length - 1, end + (step.contextAfter ?? 2));

  for (const [noteIndex, note] of step.notes.entries()) {
    const noteLine = findOccurrence(
      lines,
      note.match,
      note.occurrence ?? 1,
      note.fromAnchor === false ? first : start,
    );
    if (noteLine < 0) {
      errors.push(`${label}, note ${noteIndex + 1}: match not found: ${note.match}`);
    } else if (noteLine < first || noteLine > last) {
      errors.push(
        `${label}, note ${noteIndex + 1}: L${noteLine + 1} is outside displayed L${first + 1}-L${last + 1}`,
      );
    }
  }
}

if (errors.length) {
  console.error(errors.map((error) => `- ${error}`).join("\n"));
  process.exitCode = 1;
} else {
  console.log(`Validated ${TOUR.length} live-source steps across ${PHASES.length} phases.`);
}
