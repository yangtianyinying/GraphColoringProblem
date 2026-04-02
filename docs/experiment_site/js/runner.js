/**
 * jsPsych 7 runner: load stimulus JSON, sequential/free belief reporting, local download.
 */
import { initJsPsych } from "jspsych";
import htmlKeyboardResponse from "@jspsych/plugin-html-keyboard-response";
import callFunction from "@jspsych/plugin-call-function";

const { THEME, rgb } = window.GraphExperimentTheme;
const BASE_R = (window.GraphExperimentTheme.BASE_NODE && window.GraphExperimentTheme.BASE_NODE.nodeRadius) || 22;
const {
  drawNode,
  drawEdges,
  drawTrianglePicker,
  layoutFromNodes,
  findNodeAt,
} = window.GraphCanvasDraw;
const DEFAULT_PRACTICE_URLS = [
  "experiment_site/js/PracticeStimulateConfig.json",
  "./experiment_site/js/PracticeStimulateConfig.json",
  "docs/experiment_site/js/PracticeStimulateConfig.json",
  "./docs/experiment_site/js/PracticeStimulateConfig.json",
];
const DEFAULT_FORMAL_URLS = [
  "experiment_site/js/StimulateConfig01.json",
  "./experiment_site/js/StimulateConfig01.json",
  "docs/experiment_site/js/StimulateConfig01.json",
  "./docs/experiment_site/js/StimulateConfig01.json",
  "experiment_site/js/StimulateConfig.json",
  "./experiment_site/js/StimulateConfig.json",
  "docs/experiment_site/js/StimulateConfig.json",
  "./docs/experiment_site/js/StimulateConfig.json",
];
let defaultPracticeStimulus = null;
let defaultFormalStimulus = null;

function validateTrial(trial) {
  const ids = new Set(trial.nodes.map((n) => n.id));
  for (const [u, v] of trial.edges || []) {
    if (!ids.has(u) || !ids.has(v)) throw new Error(`边引用未知节点: ${u}-${v}`);
  }
  const colored = new Set(Object.keys(trial.initialBeliefs || {}));
  for (const id of colored) {
    if (!ids.has(id)) throw new Error(`initialBeliefs 含未知节点: ${id}`);
  }
  const uncolored = [...ids].filter((id) => !colored.has(id));
  if (trial.orderMode === "sequential") {
    const ro = trial.reportOrder || [];
    const setR = new Set(ro);
    if (ro.length !== uncolored.length || uncolored.some((id) => !setR.has(id))) {
      throw new Error("sequential 模式下 reportOrder 必须与未着色节点集合一致");
    }
  }
}

function buildContainer() {
  const wrap = document.createElement("div");
  wrap.className = "belief-trial-wrap";
  wrap.innerHTML = `
    <div class="belief-trial-inner">
      <div class="belief-graph-column">
        <canvas class="belief-graph-canvas"></canvas>
        <p class="belief-message"></p>
      </div>
      <div class="belief-picker-column">
        <canvas class="belief-picker-canvas" width="260" height="260"></canvas>
        <div class="belief-action-row">
          <button type="button" class="belief-confirm">确认填色</button>
          <button type="button" class="belief-clear">清空当前节点</button>
        </div>
      </div>
    </div>
  `;
  const style = document.createElement("style");
  style.textContent = `
    .belief-trial-wrap { font-family: "Segoe UI","Microsoft YaHei",sans-serif; padding: 12px; }
    .belief-trial-inner { display: flex; flex-direction: row; flex-wrap: wrap; align-items: flex-start; gap: 20px; max-width: 100%; }
    .belief-graph-column { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 10px; }
    .belief-graph-canvas { border: 1px solid #bbb; background: ${rgb(THEME.background)}; display: block; max-width: 100%; height: auto; }
    .belief-message { margin: 0; font-size: 15px; min-height: 2.5em; line-height: 1.45; }
    .belief-picker-column { flex: 0 0 auto; display: flex; flex-direction: column; align-items: center; gap: 12px; }
    .belief-picker-canvas { cursor: pointer; border: 1px solid #ccc; display: block; border-radius: 8px; }
    .belief-action-row { width: 100%; max-width: 260px; display: grid; gap: 8px; }
    .belief-confirm { padding: 10px 24px; font-size: 16px; cursor: pointer; width: 100%; box-sizing: border-box; }
    .belief-clear { padding: 9px 18px; font-size: 14px; cursor: pointer; width: 100%; box-sizing: border-box; }
    @media (max-width: 720px) {
      .belief-trial-inner { flex-direction: column; }
      .belief-picker-column { width: 100%; max-width: 100%; }
    }
  `;
  wrap.appendChild(style);
  return wrap;
}

function waitClick(el) {
  return new Promise((resolve) => {
    el.addEventListener("click", function handler() {
      el.removeEventListener("click", handler);
      resolve();
    });
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, Math.max(0, ms | 0)));
}

function escapeHtml(text) {
  return String(text == null ? "" : text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function waitSpaceToContinue(html) {
  return new Promise((resolve) => {
    const mount = document.getElementById("jspsych-target");
    if (!mount) {
      resolve();
      return;
    }
    mount.innerHTML = `
      <div class="phase-message-wrap">
        <style>
          .phase-message-wrap {
            min-height: 360px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
            font-family: "Segoe UI","Microsoft YaHei",sans-serif;
          }
          .phase-message-card {
            max-width: 860px;
            width: 100%;
            background: #fff;
            border: 1px solid #cfd8dc;
            border-radius: 10px;
            padding: 24px 28px;
            line-height: 1.65;
            font-size: 18px;
            color: #1f2d3d;
          }
          .phase-message-tip {
            margin-top: 14px;
            font-size: 15px;
            color: #546e7a;
          }
        </style>
        <div class="phase-message-card">${html}</div>
      </div>
    `;
    const onKeyDown = (e) => {
      if (e.code !== "Space" && e.key !== " ") return;
      e.preventDefault();
      window.removeEventListener("keydown", onKeyDown, true);
      resolve();
    };
    window.addEventListener("keydown", onKeyDown, true);
  });
}

function getStimulusUi(stimulus) {
  const ui = (stimulus && stimulus.ui) || {};
  const blockBreak = ui.blockBreak || {};
  return {
    phaseIntro: ui.phaseIntro || "",
    phaseOutro: ui.phaseOutro || "",
    trialTransitionMs: Number.isFinite(Number(ui.trialTransitionMs))
      ? Math.max(0, Number(ui.trialTransitionMs))
      : 350,
    blockBreak: {
      enabled: blockBreak.enabled !== false,
      title: blockBreak.title || "休息一下",
      body:
        blockBreak.body ||
        "你已完成 {done}/{total} 个 block（{percent}%）。\n按空格继续下一部分。",
      tip: blockBreak.tip || "按空格可立即跳过休息",
    },
  };
}

async function tryEnterFullscreen() {
  try {
    if (document.fullscreenElement) return;
    if (document.documentElement.requestFullscreen) {
      await document.documentElement.requestFullscreen();
    }
  } catch (e) {
    console.warn("进入全屏失败:", e);
  }
}

async function tryExitFullscreen() {
  try {
    if (!document.fullscreenElement) return;
    if (document.exitFullscreen) {
      await document.exitFullscreen();
    }
  } catch (e) {
    console.warn("退出全屏失败:", e);
  }
}

/**
 * 自由顺序：在画布上点未着色节点，或点「确认」。
 * 可多次点节点切换当前编辑对象；未确认则 beliefs 不会写入，节点保持空。
 */
function waitPickOrConfirm(graphCanvas, confirmBtn, clearBtn, layout, selectableSet) {
  return new Promise((resolve) => {
    function cleanup() {
      graphCanvas.removeEventListener("mousedown", onGraphDown);
      confirmBtn.removeEventListener("click", onConfirm);
      clearBtn.removeEventListener("click", onClear);
    }
    function onGraphDown(e) {
      const rect = graphCanvas.getBoundingClientRect();
      const sx = graphCanvas.width / rect.width;
      const sy = graphCanvas.height / rect.height;
      const mx = (e.clientX - rect.left) * sx;
      const my = (e.clientY - rect.top) * sy;
      const hit = findNodeAt(layout, [...selectableSet], mx, my);
      if (hit) {
        cleanup();
        resolve({ type: "pick", node: hit });
      }
    }
    function onConfirm() {
      cleanup();
      resolve({ type: "confirm" });
    }
    function onClear() {
      cleanup();
      resolve({ type: "clear" });
    }
    graphCanvas.addEventListener("mousedown", onGraphDown);
    confirmBtn.addEventListener("click", onConfirm);
    clearBtn.addEventListener("click", onClear);
  });
}

function rotateArray(arr, shift) {
  if (!Array.isArray(arr) || arr.length <= 1) return Array.isArray(arr) ? [...arr] : [];
  const n = arr.length;
  const s = ((shift % n) + n) % n;
  if (s === 0) return [...arr];
  return arr.slice(s).concat(arr.slice(0, s));
}

function getCounterbalanceGroup(participantId) {
  const m = String(participantId || "").trim().match(/^\d{3}$/);
  if (!m) return 0;
  const num = parseInt(m[0], 10);
  if (!Number.isFinite(num) || num <= 0) return 0;
  return (num - 1) % 3;
}

function applyParticipantCounterbalance(stimulus, participantId) {
  const copied = JSON.parse(JSON.stringify(stimulus));
  const group = getCounterbalanceGroup(participantId);
  const evidenceOrders = [
    ["high", "medium", "low"],
    ["medium", "low", "high"],
    ["low", "high", "medium"],
  ];
  const targetEvidenceOrder = evidenceOrders[group];

  copied.counterbalanceGroup = group + 1;
  copied.counterbalanceParticipantId = String(participantId || "");

  if (!Array.isArray(copied.blocks) || copied.blocks.length === 0) {
    return copied;
  }

  copied.blocks = rotateArray(copied.blocks, group).map((block) => {
    const trials = Array.isArray(block.trials) ? block.trials : [];
    if (!trials.length) return block;

    const byLevel = new Map();
    const fallback = [];
    for (const tr of trials) {
      const lv = String((tr && tr.evidenceLevel) || "").toLowerCase();
      if (targetEvidenceOrder.includes(lv) && !byLevel.has(lv)) byLevel.set(lv, tr);
      else fallback.push(tr);
    }

    let reordered = null;
    if (targetEvidenceOrder.every((lv) => byLevel.has(lv))) {
      reordered = targetEvidenceOrder.map((lv) => byLevel.get(lv)).concat(fallback);
    } else {
      reordered = rotateArray(trials, group);
    }
    return { ...block, trials: reordered };
  });

  return copied;
}

async function runSingleTrial(stimulusDoc, trial, meta) {
  validateTrial(trial);
  const cw = stimulusDoc.canvasWidth || 960;
  const ch = stimulusDoc.canvasHeight || 620;
  const container = buildContainer();
  const graphCanvas = container.querySelector(".belief-graph-canvas");
  const pickerCanvas = container.querySelector(".belief-picker-canvas");
  const msgEl = container.querySelector(".belief-message");
  const btn = container.querySelector(".belief-confirm");
  const clearBtn = container.querySelector(".belief-clear");
  graphCanvas.width = cw;
  graphCanvas.height = ch;

  const layout = layoutFromNodes(trial.nodes);
  const beliefs = { ...(trial.initialBeliefs || {}) };
  const nodeIds = trial.nodes.map((n) => n.id);
  const colored = new Set(Object.keys(trial.initialBeliefs || {}));
  const uncolored = nodeIds.filter((id) => !colored.has(id));
  let remaining = new Set(uncolored);
  const queue = trial.orderMode === "sequential" ? [...(trial.reportOrder || [])] : [];

  const picker = new window.TriangleColorPicker(
    pickerCanvas.width / 2,
    pickerCanvas.height / 2 + 8,
    Math.min(pickerCanvas.width, pickerCanvas.height) * 0.36
  );
  picker.setBelief(1 / 3, 1 / 3, 1 / 3);

  const rows = [];
  let focusedNode = null;
  const confirmLabelFill = "确认填色";
  const confirmLabelNext = "确认下一个试次";
  function redraw(focused, liveBelief) {
    const ctx = graphCanvas.getContext("2d");
    ctx.fillStyle = rgb(THEME.background);
    ctx.fillRect(0, 0, graphCanvas.width, graphCanvas.height);
    drawEdges(ctx, layout, trial.edges);
    for (const n of trial.nodes) {
      const pos = layout[n.id];
      let b = beliefs[n.id] != null ? beliefs[n.id] : null;
      if (n.id === focused && remaining.has(n.id) && b == null && liveBelief) {
        b = liveBelief;
      }
      const isSel = remaining.has(n.id);
      const isFoc = n.id === focused;
      drawNode(ctx, pos, b, isSel, isFoc);
    }
    const pctx = pickerCanvas.getContext("2d");
    pctx.fillStyle = rgb(THEME.background);
    pctx.fillRect(0, 0, pickerCanvas.width, pickerCanvas.height);
    const triFont = Math.max(10, Math.min(18, Math.round(14 * (THEME.nodeRadius / BASE_R))));
    drawTrianglePicker(pctx, picker, triFont);
  }

  function setMessage(text) {
    msgEl.textContent = text;
  }

  pickerCanvas.addEventListener("mousedown", (e) => {
    const rect = pickerCanvas.getBoundingClientRect();
    const sx = pickerCanvas.width / rect.width;
    const sy = pickerCanvas.height / rect.height;
    const mx = (e.clientX - rect.left) * sx;
    const my = (e.clientY - rect.top) * sy;
    picker.handleClick(mx, my);
    redraw(focusedNode, picker.getBelief());
  });
  pickerCanvas.addEventListener("mousemove", (e) => {
    if (e.buttons !== 1) return;
    const rect = pickerCanvas.getBoundingClientRect();
    const sx = pickerCanvas.width / rect.width;
    const sy = pickerCanvas.height / rect.height;
    const mx = (e.clientX - rect.left) * sx;
    const my = (e.clientY - rect.top) * sy;
    picker.handleClick(mx, my);
    redraw(focusedNode, picker.getBelief());
  });

  const mount = document.getElementById("jspsych-target");
  mount.innerHTML = "";
  mount.appendChild(container);

  try {
    btn.textContent = confirmLabelFill;
    while (remaining.size > 0) {
      if (trial.orderMode === "sequential") {
        focusedNode = queue[0];
        picker.setBelief(1 / 3, 1 / 3, 1 / 3);
        setMessage(
          "请按顺序完成当前高亮节点的信念填色，调节三角盘后点击确认。"
        );
        redraw(focusedNode, picker.getBelief());

        const onsetMs = Math.round(performance.now());
        await waitClick(btn);
        const offsetMs = Math.round(performance.now());
        const [r, g, b] = picker.getBelief();

        if (focusedNode !== queue[0]) {
          setMessage("顺序错误，请按当前高亮节点作答。");
          continue;
        }

        beliefs[focusedNode] = [r, g, b];
        rows.push({
          ...meta,
          step_index: rows.length + 1,
          chosen_node: focusedNode,
          belief_red: r,
          belief_green: g,
          belief_blue: b,
          onset_ms: onsetMs,
          offset_ms: offsetMs,
          RT_ms: offsetMs - onsetMs,
        });
        remaining.delete(focusedNode);
        queue.shift();
        focusedNode = null;
      } else {
        focusedNode = null;
        picker.setBelief(1 / 3, 1 / 3, 1 / 3);
        setMessage(
          "请点击节点，调节三角盘后点确认。可重复修改已着色节点；清空按钮会清除当前节点且不记录动作。"
        );
        redraw(null, null);
        let selectionTime = Math.round(performance.now());

        for (;;) {
          const ev = await waitPickOrConfirm(graphCanvas, btn, clearBtn, layout, new Set(nodeIds));
          if (ev.type === "pick") {
            focusedNode = ev.node;
            if (beliefs[focusedNode]) {
              const [r, g, b] = beliefs[focusedNode];
              picker.setBelief(r, g, b);
            } else {
              picker.setBelief(1 / 3, 1 / 3, 1 / 3);
            }
            selectionTime = Math.round(performance.now());
            setMessage(
              "已选节点。可确认填色、改色，或清空当前节点。切换节点不会自动提交。"
            );
            redraw(focusedNode, picker.getBelief());
            continue;
          }
          if (ev.type === "clear") {
            if (!focusedNode) {
              setMessage("请先点击一个节点，再执行清空。");
              continue;
            }
            delete beliefs[focusedNode];
            remaining.add(focusedNode);
            setMessage("已清空当前节点信念。该操作不会计入动作序列。");
            redraw(focusedNode, null);
            continue;
          }

          const [r, g, b] = picker.getBelief();
          if (!focusedNode) {
            setMessage("请先点击一个节点，再点确认。");
            continue;
          }

          const onsetMs = selectionTime;
          const offsetMs = Math.round(performance.now());

          beliefs[focusedNode] = [r, g, b];
          rows.push({
            ...meta,
            step_index: rows.length + 1,
            chosen_node: focusedNode,
            belief_red: r,
            belief_green: g,
            belief_blue: b,
            onset_ms: onsetMs,
            offset_ms: offsetMs,
            RT_ms: offsetMs - onsetMs,
          });
          remaining.delete(focusedNode);
          focusedNode = null;
          break;
        }
      }
    }

    // 所有节点完成后，不自动跳转；允许最后调整，需手动确认进入下一试次。
    focusedNode = null;
    let finalSelectionOnset = Math.round(performance.now());
    btn.textContent = confirmLabelNext;
    clearBtn.style.display = "none";
    setMessage("本试次已完成。可点击任意节点做最后调整；完成后点击“确认下一个试次”。");
    redraw(null, null);
    for (;;) {
      const ev = await waitPickOrConfirm(graphCanvas, btn, clearBtn, layout, new Set(nodeIds));
      if (ev.type === "pick") {
        focusedNode = ev.node;
        if (beliefs[focusedNode]) {
          const [r, g, b] = beliefs[focusedNode];
          picker.setBelief(r, g, b);
        } else {
          picker.setBelief(1 / 3, 1 / 3, 1 / 3);
        }
        finalSelectionOnset = Math.round(performance.now());
        btn.textContent = confirmLabelFill;
        setMessage("已选节点。点击“确认填色”保存本次调整；或重新点其它节点继续调整。");
        redraw(focusedNode, picker.getBelief());
        continue;
      }
      if (ev.type === "clear") {
        setMessage("最后调整阶段不支持清空节点；如需修改可直接覆盖填色。");
        continue;
      }
      if (!focusedNode) {
        break;
      }
      const [r, g, b] = picker.getBelief();
      const offsetMs = Math.round(performance.now());
      beliefs[focusedNode] = [r, g, b];
      rows.push({
        ...meta,
        step_index: rows.length + 1,
        chosen_node: focusedNode,
        belief_red: r,
        belief_green: g,
        belief_blue: b,
        onset_ms: finalSelectionOnset,
        offset_ms: offsetMs,
        RT_ms: offsetMs - finalSelectionOnset,
        is_final_adjustment: true,
      });
      focusedNode = null;
      btn.textContent = confirmLabelNext;
      setMessage("已保存最终调整。可继续调整，或点击“确认下一个试次”进入下一试次。");
      redraw(null, null);
    }
  } finally {
    btn.textContent = confirmLabelFill;
    clearBtn.style.display = "";
    mount.innerHTML = "";
  }

  return rows;
}

async function runAllTrials(stimulus, participantId, opts = {}) {
  const ui = getStimulusUi(stimulus);
  const totalBlocks = Array.isArray(stimulus.blocks) ? stimulus.blocks.length : 0;
  const enableBlockBreak = !!opts.enableBlockBreak;
  const showPhaseMessages = opts.showPhaseMessages !== false;
  if (showPhaseMessages && ui.phaseIntro) {
    await waitSpaceToContinue(
      `<div>${escapeHtml(ui.phaseIntro).replace(/\n/g, "<br>")}</div><div class="phase-message-tip">按空格开始</div>`
    );
  }

  const runScaleEl = document.getElementById("run-node-scale");
  let scale = runScaleEl && runScaleEl.value !== "" ? parseFloat(runScaleEl.value) : NaN;
  if (Number.isNaN(scale)) {
    scale =
      typeof stimulus.nodeVisualScale === "number" && stimulus.nodeVisualScale > 0
        ? stimulus.nodeVisualScale
        : 0.88;
  }
  window.GraphExperimentTheme.setNodeVisualScale(scale);

  const allRows = [];
  let trialGlobal = 0;
  for (let bi = 0; bi < stimulus.blocks.length; bi++) {
    if (enableBlockBreak && bi > 0 && ui.blockBreak.enabled) {
      const done = bi;
      const total = Math.max(1, totalBlocks);
      const percent = Math.round((done / total) * 100);
      const blockMsg = escapeHtml(ui.blockBreak.body)
        .replace(/\{done\}/g, String(done))
        .replace(/\{total\}/g, String(total))
        .replace(/\{percent\}/g, String(percent));
      await waitSpaceToContinue(
        `<h3>${escapeHtml(ui.blockBreak.title)}</h3><div>${blockMsg.replace(/\n/g, "<br>")}</div><div class="phase-message-tip">${escapeHtml(ui.blockBreak.tip)}</div>`
      );
    }

    const block = stimulus.blocks[bi];
    for (let ti = 0; ti < block.trials.length; ti++) {
      trialGlobal += 1;
      const trial = block.trials[ti];
      validateTrial(trial);
      const meta = {
        participant: participantId,
        counterbalance_group: stimulus.counterbalanceGroup || "",
        stimulus_name: stimulus.name || "",
        block_index: bi + 1,
        block_id: block.blockId,
        trial_in_block: ti + 1,
        trial_global: trialGlobal,
        graph_id: trial.graphId,
        order_mode: trial.orderMode,
      };
      const rows = await runSingleTrial(stimulus, trial, meta);
      for (const r of rows) {
        allRows.push(r);
      }
      if (ui.trialTransitionMs > 0) {
        await sleep(ui.trialTransitionMs);
      }
    }
  }

  if (showPhaseMessages && ui.phaseOutro) {
    await waitSpaceToContinue(
      `<div>${escapeHtml(ui.phaseOutro).replace(/\n/g, "<br>")}</div><div class="phase-message-tip">按空格继续</div>`
    );
  }
  return allRows;
}

function downloadJson(filename, obj) {
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function downloadCsv(filename, rows) {
  if (!rows.length) {
    downloadJson(filename.replace(/\.csv$/, ".json"), []);
    return;
  }
  const keys = Object.keys(rows[0]);
  const esc = (v) => {
    const s = v == null ? "" : String(v);
    if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };
  const lines = [keys.join(",")];
  for (const r of rows) {
    lines.push(keys.map((k) => esc(r[k])).join(","));
  }
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function calcAgeMonthsFromBirthdate(yyyyMmDd) {
  const d = new Date(yyyyMmDd);
  if (!(d instanceof Date) || Number.isNaN(d.getTime())) return null;
  const now = new Date();
  let months = (now.getFullYear() - d.getFullYear()) * 12 + (now.getMonth() - d.getMonth());
  if (now.getDate() < d.getDate()) months -= 1;
  return months >= 0 ? months : null;
}

async function loadJsonByCandidateUrls(urls, label) {
  let lastErr = null;
  for (const url of urls) {
    try {
      const resp = await fetch(url, { cache: "no-store" });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      if (!data || data.version !== 1) throw new Error(`${label} 不是 version: 1`);
      return data;
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr || new Error(`${label} 加载失败`);
}

async function loadDefaultStimulus() {
  const st = document.getElementById("run-stimulus-status");
  try {
    defaultPracticeStimulus = await loadJsonByCandidateUrls(
      DEFAULT_PRACTICE_URLS,
      "默认练习刺激集"
    );
    defaultFormalStimulus = await loadJsonByCandidateUrls(
      DEFAULT_FORMAL_URLS,
      "默认正式刺激集"
    );
    if (st) {
      st.textContent =
        "默认刺激集已加载（PracticeStimulateConfig.json + StimulateConfig01.json）；将先练习后正式。";
    }
    return true;
  } catch (e) {
    defaultPracticeStimulus = null;
    defaultFormalStimulus = null;
    if (st) {
      st.textContent = `默认刺激集加载失败：${String(
        (e && e.message) || e || "unknown error"
      )}；请手动选择刺激集 JSON。`;
    }
    return false;
  }
}

export async function startExperimentFromUi() {
  const participantName = (document.getElementById("run-name").value || "").trim();
  if (!participantName) {
    alert("请先填写姓名，再开始实验。");
    document.getElementById("run-name").focus();
    return;
  }
  const birthdate = (document.getElementById("run-birthdate").value || "").trim();
  if (!birthdate) {
    alert("请先选择出生日期，再开始实验。");
    document.getElementById("run-birthdate").focus();
    return;
  }
  const ageMonths = calcAgeMonthsFromBirthdate(birthdate);
  if (ageMonths == null) {
    alert("出生日期无效，请重新选择。");
    document.getElementById("run-birthdate").focus();
    return;
  }
  const gender = (document.getElementById("run-gender").value || "").trim();
  if (!gender) {
    alert("请先选择性别，再开始实验。");
    document.getElementById("run-gender").focus();
    return;
  }
  const pid = (document.getElementById("run-participant").value || "").trim();
  if (!pid) {
    alert("请先输入被试编号，再开始实验。");
    document.getElementById("run-participant").focus();
    return;
  }
  if (!/^\d{3}$/.test(pid)) {
    alert("被试编号需为三位数字（如 001 / 002 / 003）。");
    document.getElementById("run-participant").focus();
    return;
  }
  const fileInput = document.getElementById("run-stimulus-file");
  const file = fileInput.files && fileInput.files[0];
  let practiceStimulus = null;
  let formalStimulus = null;
  let exportStimulus = null;
  let shouldRunPracticeFirst = false;
  if (file) {
    const text = await file.text();
    let singleStimulus = null;
    try {
      singleStimulus = JSON.parse(text);
    } catch (e) {
      alert("JSON 解析失败: " + e);
      return;
    }
    if (!singleStimulus || singleStimulus.version !== 1) {
      alert("需要 version: 1 的刺激集");
      return;
    }
    formalStimulus = singleStimulus;
    exportStimulus = formalStimulus;
  } else {
    if (!defaultPracticeStimulus || !defaultFormalStimulus) {
      await loadDefaultStimulus();
    }
    if (defaultPracticeStimulus && defaultFormalStimulus) {
      practiceStimulus = defaultPracticeStimulus;
      formalStimulus = defaultFormalStimulus;
      exportStimulus = formalStimulus;
      shouldRunPracticeFirst = true;
    } else {
      alert("默认刺激集未就绪，请先选择刺激集 JSON 文件。");
      return;
    }
  }

  if (typeof formalStimulus.nodeVisualScale === "number" && formalStimulus.nodeVisualScale > 0) {
    const s = String(formalStimulus.nodeVisualScale);
    const rs = document.getElementById("run-node-scale");
    const es = document.getElementById("editor-node-scale");
    if (rs) rs.value = s;
    if (es) es.value = s;
    localStorage.setItem("graphNodeVisualScale", s);
    window.GraphExperimentTheme.setNodeVisualScale(formalStimulus.nodeVisualScale);
    const pct = Math.round(formalStimulus.nodeVisualScale * 100);
    const v1 = document.getElementById("editor-node-scale-val");
    const v2 = document.getElementById("run-node-scale-val");
    if (v1) v1.textContent = `${pct}%`;
    if (v2) v2.textContent = `${pct}%`;
    if (window.EditorApp && window.EditorApp.refreshEditorView) {
      window.EditorApp.refreshEditorView();
    }
  }

  if (practiceStimulus) {
    practiceStimulus = applyParticipantCounterbalance(practiceStimulus, pid);
  }
  formalStimulus = applyParticipantCounterbalance(formalStimulus, pid);

  await tryEnterFullscreen();
  try {
    const jsPsych = initJsPsych({
      display_element: document.getElementById("jspsych-target"),
      on_finish: function () {
        try {
          jsPsych.data.get().localSave("json", `graph_coloring_${pid}_jspsych.json`);
        } catch (e) {
          console.warn(e);
        }
      },
    });

    const timeline = [
      {
        type: htmlKeyboardResponse,
        stimulus:
          shouldRunPracticeFirst
            ? "<p>图着色信念任务：请按空格继续。</p><p>将先进行练习试次，再进入正式实验。练习数据不会导出。</p>"
            : "<p>图着色信念任务：请按空格继续。</p><p>请按系统给出的当前高亮节点依次报告。</p>",
        choices: [" "],
      },
      {
        type: callFunction,
        async: true,
        func: async function () {
          if (practiceStimulus) {
            await runAllTrials(practiceStimulus, pid, {
              enableBlockBreak: false,
              showPhaseMessages: true,
            });
          }
          const rows = await runAllTrials(formalStimulus, pid, {
            enableBlockBreak: true,
            showPhaseMessages: true,
          });
          rows.forEach((r) => {
            r.participant_name = participantName;
            r.participant_birthdate = birthdate;
            r.participant_age_months = ageMonths;
            r.participant_gender = gender;
          });
          downloadCsv(`graph_coloring_${pid}.csv`, rows);
          downloadJson(`graph_coloring_${pid}.json`, {
            participant: pid,
            participant_profile: {
              name: participantName,
              birthdate,
              age_months: ageMonths,
              gender,
            },
            stimulus: exportStimulus,
            practice_not_recorded: shouldRunPracticeFirst,
            rows,
          });
        },
      },
      {
        type: htmlKeyboardResponse,
        stimulus: "<p>实验结束。数据应已下载。按任意键关闭。</p>",
        choices: "ALL_KEYS",
        response_ends_trial: true,
      },
    ];

    await jsPsych.run(timeline);
  } finally {
    await tryExitFullscreen();
  }
}

document.getElementById("btn-start-exp").addEventListener("click", () => {
  startExperimentFromUi().catch((e) => {
    console.error(e);
    alert(String(e));
  });
});

document.getElementById("run-stimulus-file").addEventListener("change", (e) => {
  const f = e.target.files && e.target.files[0];
  const st = document.getElementById("run-stimulus-status");
  if (f) st.textContent = `已选择: ${f.name}（将覆盖默认刺激集）`;
  else if (defaultPracticeStimulus && defaultFormalStimulus)
    st.textContent =
      "已恢复使用默认刺激集（PracticeStimulateConfig.json + StimulateConfig01.json）";
  else st.textContent = "请先选择刺激集 JSON 文件";
});

loadDefaultStimulus();
