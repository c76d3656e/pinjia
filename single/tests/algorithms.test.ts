import assert from "node:assert/strict";
import {
  analyzeAHP,
  analyzeFAHP,
  calculateAHP,
  calculateEntropyWeights,
  calculateFAHP,
  calculateFAHPFinalWeights,
  calculateIndicatorScore,
  evaluate,
  DEFAULT_RANGES,
} from "../src/lib/evaluation";
import { HistoryEntry, pushHistoryEntry, trimHistory } from "../src/lib/history";

function almostEqual(actual: number, expected: number, epsilon = 1e-6) {
  assert.ok(Math.abs(actual - expected) < epsilon, `${actual} != ${expected}`);
}

{
  const result = calculateFAHP([
    [0.5, 0.6, 0.7],
    [0.4, 0.5, 0.6],
    [0.3, 0.4, 0.5],
  ]);
  almostEqual(result.weights.reduce((sum, value) => sum + value, 0), 1);
  almostEqual(result.weights[0], 0.3833333333333333);
  almostEqual(result.weights[1], 0.3333333333333333);
  almostEqual(result.weights[2], 0.2833333333333333);
  assert.ok(result.weights[0] > result.weights[1]);
  assert.ok(result.weights[1] > result.weights[2]);
}

{
  const weights = calculateFAHPFinalWeights(
    ["technical_1", "technical_2", "safety_1"],
    [
      [0.5, 0.7],
      [0.3, 0.5],
    ],
    {
      technical: [
        [0.5, 0.6],
        [0.4, 0.5],
      ],
      safety: [[0.5]],
    },
  );
  almostEqual(Object.values(weights).reduce((sum, value) => sum + value, 0), 1);
  almostEqual(weights.technical_1, 0.33);
  almostEqual(weights.technical_2, 0.27);
  almostEqual(weights.safety_1, 0.4);
}

{
  assert.throws(() =>
    calculateAHP([
      [1, 3, 4],
      [0.5, 1, 2],
      [0.25, 0.5, 1],
    ]),
  );
  const result = calculateAHP([
    [1, 2, 4],
    [0.5, 1, 2],
    [0.25, 0.5, 1],
  ]);
  almostEqual(result.weights.reduce((sum, value) => sum + value, 0), 1);
}

{
  const diagnostic = analyzeAHP([
    [1, 9, 1],
    [1 / 9, 1, 9],
    [1, 1 / 9, 1],
  ]);
  assert.equal(diagnostic.ok, false);
  assert.ok((diagnostic.cr ?? 0) > 0.1);
  assert.ok(diagnostic.invalidCells.length > 0);
}

{
  const diagnostic = analyzeFAHP([
    [0.5, 0.9, 0.1],
    [0.1, 0.5, 0.9],
    [0.9, 0.1, 0.5],
  ]);
  assert.equal(diagnostic.ok, false);
  assert.ok(diagnostic.invalidCells.length > 0);
}

{
  const result = calculateFAHP([
    [0.5, 0.97, 1],
    [0.03, 0.5, 0.9],
    [0, 0.1, 0.5],
  ]);
  almostEqual(result.weights.reduce((sum, value) => sum + value, 0), 1);
  assert.ok(result.weights[0] > result.weights[1]);
  assert.ok(result.weights[1] > result.weights[2]);
}

{
  const weights = calculateEntropyWeights(
    [
      [10, 100],
      [20, 80],
      [40, 60],
    ],
    ["benefit", "cost"],
    [true, false],
  );
  almostEqual(Object.values(weights).reduce((sum, value) => sum + value, 0), 1);
  assert.ok(weights.benefit > 0);
  assert.ok(weights.cost > 0);
}

{
  const lowerLow = calculateIndicatorScore(6, {
    excellent: { operator: "<=", value: 5 },
    good: { min: 5, max: 10 },
    average: { min: 10, max: 15 },
    poor: { min: 15, max: 20 },
    verypoor: { operator: ">=", value: 20 },
  });
  const lowerHigh = calculateIndicatorScore(9, {
    excellent: { operator: "<=", value: 5 },
    good: { min: 5, max: 10 },
    average: { min: 10, max: 15 },
    poor: { min: 15, max: 20 },
    verypoor: { operator: ">=", value: 20 },
  });
  assert.ok(lowerLow.score > lowerHigh.score);

  const higherLow = calculateIndicatorScore(1.35, DEFAULT_RANGES.technical_6);
  const higherHigh = calculateIndicatorScore(1.45, DEFAULT_RANGES.technical_6);
  assert.ok(higherHigh.score > higherLow.score);
}

{
  const result = evaluate(
    ["technical_1", "technical_2", "safety_1"],
    { technical_1: 0.2, technical_2: 0.3, safety_1: 0.5 },
    DEFAULT_RANGES,
    { technical_1: 5, technical_2: 0.1, safety_1: 70 },
  );
  almostEqual(result.overallScore, 100);
}

console.log("algorithm tests passed");

{
  const entries = Array.from({ length: 12 }, (_, index) => ({ id: String(index) }) as HistoryEntry);
  assert.equal(trimHistory(entries).length, 10);
  assert.equal(trimHistory(entries)[0].id, "0");
  assert.equal(trimHistory(entries)[9].id, "9");
}

{
  const current = Array.from({ length: 10 }, (_, index) => ({ id: String(index) }) as HistoryEntry);
  const next = pushHistoryEntry(current, { id: "new" } as HistoryEntry);
  assert.equal(next.length, 10);
  assert.equal(next[0].id, "new");
  assert.equal(next.some((entry) => entry.id === "9"), false);
}

console.log("history tests passed");
