import { PHASES, SCOPES, TOUR } from "./tour-data.js";

const REPO_ROOT = new URL("../../../", import.meta.url);
const sourceCache = new Map();
const elements = {
  phaseMap: document.querySelector("#phase-map"),
  sourceStatus: document.querySelector("#source-status"),
  restartButton: document.querySelector("#restart-button"),
  stepCount: document.querySelector("#step-count"),
  stepList: document.querySelector("#step-list"),
  codePath: document.querySelector("#code-path"),
  codeRange: document.querySelector("#code-range"),
  codeScroll: document.querySelector("#code-scroll"),
  codeView: document.querySelector("#code-view code"),
  copyPathButton: document.querySelector("#copy-path-button"),
  phaseLabel: document.querySelector("#phase-label"),
  stepPosition: document.querySelector("#step-position"),
  stepTitle: document.querySelector("#step-title"),
  stepQuestion: document.querySelector("#step-question"),
  stepSummary: document.querySelector("#step-summary"),
  callStack: document.querySelector("#call-stack"),
  lineNotes: document.querySelector("#line-notes"),
  stateSection: document.querySelector("#state-section"),
  stateGrid: document.querySelector("#state-grid"),
  visualSection: document.querySelector("#visual-section"),
  scopeVisual: document.querySelector("#scope-visual"),
  previousButton: document.querySelector("#previous-button"),
  nextButton: document.querySelector("#next-button"),
  nextPreview: document.querySelector("#next-preview"),
  progressFill: document.querySelector("#progress-fill"),
  sourceErrorTemplate: document.querySelector("#source-error-template"),
};

let currentIndex = indexFromUrl();
let currentResolvedStep = null;
let selectedNoteIndex = 0;

function indexFromUrl() {
  const raw = new URLSearchParams(window.location.search).get("step");
  const parsed = Number.parseInt(raw ?? "1", 10) - 1;
  return Number.isFinite(parsed) ? Math.min(Math.max(parsed, 0), TOUR.length - 1) : 0;
}

function writeIndexToUrl() {
  const url = new URL(window.location.href);
  url.searchParams.set("step", String(currentIndex + 1));
  history.replaceState(null, "", url);
}

async function loadSource(path) {
  if (sourceCache.has(path)) return sourceCache.get(path);
  const response = await fetch(new URL(path, REPO_ROOT));
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  const source = await response.text();
  sourceCache.set(path, source);
  return source;
}

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

function resolveStep(step, source) {
  const allLines = source.replaceAll("\r\n", "\n").split("\n");
  const anchorIndex = findOccurrence(allLines, step.anchor, step.occurrence ?? 1);
  if (anchorIndex < 0) throw new Error(`anchor not found: ${step.anchor}`);

  const endIndex = step.endAnchor
    ? findOccurrence(allLines, step.endAnchor, step.endOccurrence ?? 1, anchorIndex)
    : anchorIndex;
  if (endIndex < anchorIndex) throw new Error(`end anchor not found: ${step.endAnchor}`);

  const firstIndex = Math.max(0, anchorIndex - (step.contextBefore ?? 2));
  const lastIndex = Math.min(allLines.length - 1, endIndex + (step.contextAfter ?? 2));
  const notes = step.notes.map((note) => {
    const lineIndex = findOccurrence(
      allLines,
      note.match,
      note.occurrence ?? 1,
      note.fromAnchor === false ? firstIndex : anchorIndex,
    );
    return { ...note, lineIndex };
  });
  return { ...step, allLines, firstIndex, lastIndex, anchorIndex, endIndex, notes };
}

function phaseFor(id) {
  return PHASES.find((phase) => phase.id === id);
}

function renderPhaseMap() {
  const activePhaseIndex = PHASES.findIndex((phase) => phase.id === TOUR[currentIndex].phase);
  elements.phaseMap.replaceChildren(
    ...PHASES.map((phase, index) => {
      const node = document.createElement("div");
      node.className = "phase-node";
      if (index < activePhaseIndex) node.classList.add("complete");
      if (index === activePhaseIndex) node.classList.add("active");
      node.textContent = phase.label;
      node.title = phase.description;
      return node;
    }),
  );
}

function renderStepList() {
  elements.stepCount.textContent = `${currentIndex + 1} / ${TOUR.length}`;
  elements.stepList.replaceChildren(
    ...TOUR.map((step, index) => {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "step-button";
      if (index < currentIndex) button.classList.add("complete");
      if (index === currentIndex) {
        button.classList.add("active");
        button.setAttribute("aria-current", "step");
      }
      const number = document.createElement("span");
      number.className = "step-number";
      number.textContent = String(index + 1).padStart(2, "0");
      const copy = document.createElement("span");
      copy.className = "step-name";
      copy.textContent = step.shortTitle ?? step.title;
      const file = document.createElement("span");
      file.className = "step-file";
      file.textContent = step.file.split("/").at(-1);
      copy.append(file);
      button.append(number, copy);
      button.addEventListener("click", () => goTo(index));
      item.append(button);
      return item;
    }),
  );
  elements.stepList.querySelector(".active")?.scrollIntoView({ block: "nearest" });
}

function renderCode(resolved) {
  const notedLines = new Map();
  resolved.notes.forEach((note, index) => {
    if (note.lineIndex >= 0 && !notedLines.has(note.lineIndex)) notedLines.set(note.lineIndex, index);
  });

  const fragment = document.createDocumentFragment();
  for (let index = resolved.firstIndex; index <= resolved.lastIndex; index += 1) {
    const line = document.createElement("span");
    line.className = "code-line";
    line.dataset.lineIndex = String(index);
    if (notedLines.has(index)) {
      line.classList.add("has-note");
      line.addEventListener("click", () => selectNote(notedLines.get(index)));
    }
    const number = document.createElement("span");
    number.className = "line-number";
    number.textContent = String(index + 1);
    const content = document.createElement("span");
    content.className = "line-content";
    content.textContent = resolved.allLines[index] || " ";
    line.append(number, content);
    fragment.append(line);
  }
  elements.codeView.replaceChildren(fragment);
  elements.codePath.textContent = resolved.file;
  elements.codePath.title = resolved.file;
  elements.codeRange.textContent = `L${resolved.firstIndex + 1}–L${resolved.lastIndex + 1} · anchor: ${resolved.anchor}`;
}

function renderNarrative(resolved) {
  const phase = phaseFor(resolved.phase);
  elements.phaseLabel.textContent = phase?.label ?? resolved.phase;
  elements.stepPosition.textContent = `${String(currentIndex + 1).padStart(2, "0")} / ${TOUR.length}`;
  elements.stepTitle.textContent = resolved.title;
  elements.stepQuestion.textContent = resolved.question;
  elements.stepSummary.textContent = resolved.summary;

  elements.callStack.replaceChildren(
    ...resolved.stack.map((frame) => {
      const item = document.createElement("li");
      item.textContent = frame;
      return item;
    }),
  );

  elements.lineNotes.replaceChildren(
    ...resolved.notes.map((note, index) => {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "note-button";
      const line = document.createElement("span");
      line.className = "note-line";
      line.textContent = note.lineIndex >= 0 ? `L${note.lineIndex + 1}` : "L?";
      const copy = document.createElement("span");
      copy.className = "note-copy";
      copy.textContent = note.text;
      button.append(line, copy);
      button.addEventListener("click", () => selectNote(index));
      item.append(button);
      return item;
    }),
  );

  elements.stateSection.hidden = !resolved.state?.length;
  elements.stateGrid.replaceChildren(
    ...(resolved.state ?? []).map(({ label, value }) => {
      const item = document.createElement("dl");
      item.className = "state-item";
      const term = document.createElement("dt");
      term.textContent = label;
      const description = document.createElement("dd");
      description.textContent = value;
      item.append(term, description);
      return item;
    }),
  );

  renderScopeVisual(resolved.visual);
}

function renderScopeVisual(visual) {
  if (!visual) {
    elements.visualSection.hidden = true;
    elements.scopeVisual.replaceChildren();
    return;
  }
  elements.visualSection.hidden = false;
  const chain = document.createElement("div");
  chain.className = "scope-chain";
  for (const scopeName of visual.scopes) {
    const scope = SCOPES.find((candidate) => candidate.name === scopeName);
    if (!scope) continue;
    const card = document.createElement("article");
    card.className = "scope-card";
    if (scope.name === visual.active) card.classList.add("active");
    const title = document.createElement("h4");
    title.textContent = scope.name;
    const kind = document.createElement("span");
    kind.textContent = ` · ${scope.kind}`;
    title.append(kind);
    const chips = document.createElement("div");
    chips.className = "symbol-chips";
    for (const symbol of scope.symbols) {
      const chip = document.createElement("span");
      chip.className = `symbol-chip ${symbol.tone ?? ""}`;
      chip.textContent = `${symbol.name}:${symbol.scope}`;
      chips.append(chip);
    }
    card.append(title, chips);
    chain.append(card);
  }
  elements.scopeVisual.replaceChildren(chain);
}

function selectNote(index, shouldScroll = true) {
  if (!currentResolvedStep?.notes.length) return;
  selectedNoteIndex = Math.min(Math.max(index, 0), currentResolvedStep.notes.length - 1);
  const note = currentResolvedStep.notes[selectedNoteIndex];
  elements.lineNotes.querySelectorAll(".note-button").forEach((button, buttonIndex) => {
    button.classList.toggle("active", buttonIndex === selectedNoteIndex);
  });
  elements.codeView.querySelectorAll(".code-line").forEach((line) => {
    line.classList.toggle("selected", Number(line.dataset.lineIndex) === note.lineIndex);
  });
  if (shouldScroll && note.lineIndex >= 0) {
    elements.codeView
      .querySelector(`[data-line-index="${note.lineIndex}"]`)
      ?.scrollIntoView({ block: "center", behavior: "smooth" });
  }
}

function renderControls() {
  elements.previousButton.disabled = currentIndex === 0;
  elements.nextButton.disabled = currentIndex === TOUR.length - 1;
  elements.nextButton.firstChild.textContent = currentIndex === TOUR.length - 1 ? "완료 " : "다음 ";
  elements.nextPreview.textContent =
    currentIndex < TOUR.length - 1 ? `다음: ${TOUR[currentIndex + 1].title}` : "투어 완료";
  elements.progressFill.style.width = `${((currentIndex + 1) / TOUR.length) * 100}%`;
}

function renderSourceError(error) {
  console.error(error);
  const content = elements.sourceErrorTemplate.content.cloneNode(true);
  elements.codeView.replaceChildren(content);
  elements.codePath.textContent = TOUR[currentIndex].file;
  elements.codeRange.textContent = String(error.message ?? error);
  elements.sourceStatus.classList.remove("connected");
  elements.sourceStatus.classList.add("failed");
  elements.sourceStatus.lastChild.textContent = " 실제 저장소 소스 연결 실패";
}

async function render() {
  const step = TOUR[currentIndex];
  writeIndexToUrl();
  renderPhaseMap();
  renderStepList();
  renderControls();
  selectedNoteIndex = 0;
  try {
    const source = await loadSource(step.file);
    if (TOUR[currentIndex] !== step) return;
    currentResolvedStep = resolveStep(step, source);
    renderCode(currentResolvedStep);
    renderNarrative(currentResolvedStep);
    selectNote(0, false);
    elements.sourceStatus.classList.remove("failed");
    elements.sourceStatus.classList.add("connected");
    elements.sourceStatus.lastChild.textContent = " 실제 저장소 소스 사용 중";
  } catch (error) {
    currentResolvedStep = null;
    renderNarrative({ ...step, notes: step.notes.map((note) => ({ ...note, lineIndex: -1 })) });
    renderSourceError(error);
  }
}

function goTo(index) {
  const next = Math.min(Math.max(index, 0), TOUR.length - 1);
  if (next === currentIndex && currentResolvedStep) return;
  currentIndex = next;
  render();
}

elements.previousButton.addEventListener("click", () => goTo(currentIndex - 1));
elements.nextButton.addEventListener("click", () => goTo(currentIndex + 1));
elements.restartButton.addEventListener("click", () => goTo(0));
elements.copyPathButton.addEventListener("click", async () => {
  const path = TOUR[currentIndex].file;
  try {
    await navigator.clipboard.writeText(path);
    elements.copyPathButton.textContent = "복사됨";
  } catch {
    elements.copyPathButton.textContent = path;
  }
  window.setTimeout(() => (elements.copyPathButton.textContent = "경로 복사"), 1200);
});

window.addEventListener("keydown", (event) => {
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
  if (event.key === "ArrowLeft") goTo(currentIndex - 1);
  if (event.key === "ArrowRight") goTo(currentIndex + 1);
});

window.addEventListener("popstate", () => {
  currentIndex = indexFromUrl();
  render();
});

render();
