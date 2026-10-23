// 知識グラフの検証と「前提をさかのぼる」診断ロジックのプロトタイプ。
// 依存なし。`node --test adaptive/` でテストできる。

import { readFileSync } from "node:fs";

export function loadGraph(path = new URL("./skill-graph.json", import.meta.url)) {
  return buildGraph(JSON.parse(readFileSync(path, "utf8")).skills);
}

export function buildGraph(skills) {
  const byId = new Map(skills.map((s) => [s.id, s]));
  if (byId.size !== skills.length) throw new Error("duplicate skill id");
  for (const s of skills) {
    for (const p of s.prereqs) {
      if (!byId.has(p)) throw new Error(`${s.id}: unknown prereq ${p}`);
    }
  }
  // 循環検出（DFS）
  const state = new Map();
  const visit = (id, stack) => {
    if (state.get(id) === 2) return;
    if (state.get(id) === 1) throw new Error(`cycle: ${[...stack, id].join(" -> ")}`);
    state.set(id, 1);
    for (const p of byId.get(id).prereqs) visit(p, [...stack, id]);
    state.set(id, 2);
  };
  for (const id of byId.keys()) visit(id, []);
  return byId;
}

export function ancestors(graph, id) {
  const out = new Set();
  const walk = (x) => {
    for (const p of graph.get(x).prereqs) {
      if (!out.has(p)) { out.add(p); walk(p); }
    }
  };
  walk(id);
  return out;
}

/**
 * 誤答した問題の必要スキル `failed` から、つまずきの根っこ（root causes）を探す。
 * ask(skillId) は診断問題を出して正誤(boolean)を返す関数（実運用では生徒の回答）。
 *
 * 規則:
 *  - 診断に正解したスキルは、その祖先もすべて習得済みとみなす（推移的推論）
 *  - 不正解のスキルは、前提を順に診断する
 *  - 「前提がすべて習得済みなのに自分は不正解」なスキルが根っこ
 */
export function diagnose(graph, failed, ask) {
  const known = new Set();
  const unknown = new Set(failed);
  const asked = [];

  const test = (id) => {
    if (known.has(id)) return true;
    if (unknown.has(id) && !failed.includes(id)) return false;
    const ok = ask(id);
    asked.push({ id, ok });
    if (ok) {
      known.add(id);
      for (const a of ancestors(graph, id)) known.add(a);
    } else {
      unknown.add(id);
    }
    return ok;
  };

  const explore = (id) => {
    for (const p of graph.get(id).prereqs) {
      if (known.has(p)) continue;
      if (!test(p)) explore(p);
    }
  };
  for (const f of failed) explore(f);

  const roots = [...unknown].filter((id) =>
    graph.get(id).prereqs.every((p) => known.has(p)),
  );
  return { roots, asked };
}

/** 学習順（根っこ → 元の問題）: 前提が先になるトポロジカル順で、根っこの下流だけを返す */
export function learningPath(graph, roots, target) {
  const order = [];
  const seen = new Set();
  const visit = (id) => {
    if (seen.has(id)) return;
    seen.add(id);
    for (const p of graph.get(id).prereqs) visit(p);
    order.push(id);
  };
  visit(target);
  return order.filter(
    (id) => roots.includes(id) || [...ancestors(graph, id)].some((a) => roots.includes(a)),
  );
}
