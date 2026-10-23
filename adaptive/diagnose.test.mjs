import test from "node:test";
import assert from "node:assert/strict";
import { loadGraph, buildGraph, diagnose, learningPath } from "./diagnose.mjs";

const graph = loadGraph();

test("知識グラフは非循環で、前提がすべて存在する", () => {
  assert.ok(graph.size >= 35);
});

test("循環は検出される", () => {
  assert.throws(() =>
    buildGraph([
      { id: "a", prereqs: ["b"] },
      { id: "b", prereqs: ["a"] },
    ]),
  /cycle/);
});

// 生徒が「真に」できないスキル集合を与えて、診断が根っこに到達するか確認する
function simulate(weak, failed) {
  const blocked = new Set(weak);
  // 弱点スキルとその下流（それを前提とするスキル）はできない
  const cannot = (id) => blocked.has(id) || [...graph.get(id).prereqs].some(cannot);
  return diagnose(graph, failed, (id) => !cannot(id));
}

test("方程式の誤答の根っこが「分数の約分・通分」と特定できる", () => {
  const r = simulate(["E5_fraction_equiv"], ["J1_eq_frac"]);
  assert.deepEqual(r.roots, ["E5_fraction_equiv"]);
});

test("正負の数の加減が根っこなら、方程式の誤答からそこまで到達する", () => {
  const r = simulate(["J1_addsub_int"], ["J1_eq_basic"]);
  assert.deepEqual(r.roots, ["J1_addsub_int"]);
});

test("中間層の弱点なら、診断問題数は全スキル数の半分未満", () => {
  const r = simulate(["E5_gcd_lcm"], ["J1_eq_frac"]);
  assert.ok(r.asked.length < graph.size / 2, `asked ${r.asked.length}`);
  assert.deepEqual(r.roots, ["E5_gcd_lcm"]);
});

test("最深部（わり算）が弱い場合も根っこには到達する（問題数は多くなる）", () => {
  const r = simulate(["E3_div_basic"], ["J1_eq_word"]);
  assert.deepEqual(r.roots, ["E3_div_basic"]);
});

test("学習順は前提が先で、元の問題が最後になる", () => {
  const path = learningPath(graph, ["E5_fraction_equiv"], "J1_eq_frac");
  assert.equal(path[0], "E5_fraction_equiv");
  assert.equal(path.at(-1), "J1_eq_frac");
});
