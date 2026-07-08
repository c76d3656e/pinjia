import { CATEGORIES, findIndicator, Indicator, selectedCategories } from "./indicators";

export type GradeKey = "excellent" | "good" | "average" | "poor" | "verypoor";

export type EvaluationInterval = {
  min: number | null;
  max: number | null;
};

export type EvaluationRange = {
  satisfaction: EvaluationInterval[];
  tolerance: EvaluationInterval[];
};

export type AHPResult = {
  weights: number[];
  lambdaMax: number;
  ci: number;
  cr: number;
};

export type FAHPResult = {
  weights: number[];
  ci: number;
};

export const DEFAULT_ALPHA = 0.25;
export const DEFAULT_BETA = 1;

export type MatrixDiagnostic = {
  ok: boolean;
  message: string;
  weights: number[];
  lambdaMax?: number;
  ci: number;
  cr?: number;
  invalidCells: string[];
};

export type IndicatorEvaluation = {
  indicator: Indicator;
  value: number;
  weight: number;
  score: number;
  grade: string;
  weightedScore?: number;
  satisfaction: number;
  weightedSatisfaction: number;
};

export type EvaluationResult = {
  overallScore: number;
  overallGrade: string;
  rows: IndicatorEvaluation[];
  categoryScores: Array<{
    categoryId: string;
    categoryName: string;
    weight: number;
    satisfaction: number;
    score: number;
  }>;
  topsis: {
    dPlus: number;
    dMinus: number;
    cRaw: number;
  };
  safety: {
    sSafe: number;
    alpha: number;
    beta: number;
    penalty: number;
  };
};

export const DEFAULT_RANGES: Record<string, EvaluationRange> = {
  technical_1: rangeAtMost(5, 10),
  technical_2: rangeAtMost(0.5, 1.0),
  technical_3: { satisfaction: [finiteInterval(0, 1)], tolerance: [finiteInterval(1, 4)] },
  technical_4: rangeBetween(5, 8, 3, 10),
  technical_5: rangeBetween(2.5, 3, 2.0, 3.5),
  technical_6: rangeBetween(1.5, 1.8, 1.3, 2.0),
  safety_1: rangeAtMost(100, 200),
  safety_2: rangeAtMost(5, 8),
  economic_1: rangeAtMost(0.45, 0.55),
  economic_2: { satisfaction: [finiteInterval(25, 30)], tolerance: [finiteInterval(30, 35)] },
};

// 各指标的容许偏离偏差量（自动跟随满意阈计算）
const DEVIATIONS: Record<string, { low?: number; high?: number }> = {
  technical_1: { high: 5 },
  technical_2: { high: 0.5 },
  technical_3: { high: 3 },
  technical_4: { low: 2, high: 2 },
  technical_5: { low: 0.5, high: 0.5 },
  technical_6: { low: 0.2, high: 0.2 },
  safety_1: { high: 100 },
  safety_2: { high: 3 },
  economic_1: { high: 0.1 },
  economic_2: { high: 5 },
};

// 从满意阈自动推导容许偏离区间
export function deriveTolerance(satisfaction: EvaluationInterval[], id: string): EvaluationInterval[] {
  const dev = DEVIATIONS[id];
  if (!dev) return [];
  const result: EvaluationInterval[] = [];
  for (const interval of satisfaction) {
    if (dev.low != null && interval.min != null) {
      result.push(finiteInterval(interval.min - dev.low, interval.min));
    }
    if (dev.high != null && interval.max != null) {
      result.push(finiteInterval(interval.max, interval.max + dev.high));
    }
  }
  return result;
}

const GRADE_SCORES = {
  excellent: 100,
  good: 85,
  average: 70,
  poor: 50,
  verypoor: 20,
};

function finiteInterval(min: number | null, max: number | null): EvaluationInterval {
  return { min, max };
}

function rangeAtMost(satisfactionMax: number, toleranceMax: number): EvaluationRange {
  return {
    satisfaction: [finiteInterval(0, satisfactionMax)],
    tolerance: [finiteInterval(satisfactionMax, toleranceMax)],
  };
}

function rangeAtLeast(satisfactionMin: number, toleranceMin: number): EvaluationRange {
  return {
    satisfaction: [finiteInterval(satisfactionMin, null)],
    tolerance: [finiteInterval(toleranceMin, satisfactionMin)],
  };
}

function rangeBetween(satisfactionMin: number, satisfactionMax: number, toleranceMin: number, toleranceMax: number): EvaluationRange {
  return {
    satisfaction: [finiteInterval(satisfactionMin, satisfactionMax)],
    tolerance: [finiteInterval(toleranceMin, satisfactionMin), finiteInterval(satisfactionMax, toleranceMax)],
  };
}

function normalize(values: number[]): number[] {
  const total = values.reduce((sum, value) => sum + value, 0);
  if (total <= 0 || !Number.isFinite(total)) {
    throw new Error("权重和必须大于 0");
  }
  return values.map((value) => value / total);
}

function assertSquareMatrix(matrix: number[][], name: string): void {
  if (!matrix.length || matrix.some((row) => row.length !== matrix.length)) {
    throw new Error(`${name}必须为非空方阵`);
  }
  matrix.forEach((row, rowIndex) => {
    row.forEach((value, colIndex) => {
      if (!Number.isFinite(value)) {
        throw new Error(`${name}包含无效数值: [${rowIndex}, ${colIndex}]`);
      }
    });
  });
}

function powerIterationWeights(matrix: number[][]): number[] {
  const n = matrix.length;
  let weights = Array.from({ length: n }, () => 1 / n);
  for (let step = 0; step < 200; step += 1) {
    const next = matrix.map((row) => row.reduce((sum, value, col) => sum + value * weights[col], 0));
    const normalized = normalize(next);
    const diff = normalized.reduce((sum, value, index) => sum + Math.abs(value - weights[index]), 0);
    weights = normalized;
    if (diff < 1e-12) {
      break;
    }
  }
  return weights;
}

function ahpInconsistencyCells(matrix: number[][]): string[] {
  const n = matrix.length;
  const scores = new Map<string, number>();
  for (let i = 0; i < n; i += 1) {
    for (let j = i + 1; j < n; j += 1) {
      let score = 0;
      let count = 0;
      for (let k = 0; k < n; k += 1) {
        if (k === i || k === j) continue;
        const expected = matrix[i][k] / matrix[j][k];
        if (expected > 0 && matrix[i][j] > 0) {
          score += Math.abs(Math.log(matrix[i][j] / expected));
          count += 1;
        }
      }
      scores.set(`${i}-${j}`, count > 0 ? score / count : 0);
    }
  }
  const maxScore = Math.max(0, ...scores.values());
  if (maxScore <= 0.15) return [];
  return [...scores.entries()]
    .filter(([, score]) => score >= maxScore * 0.8)
    .map(([key]) => key);
}

export function analyzeAHP(matrix: number[][]): MatrixDiagnostic {
  try {
    assertSquareMatrix(matrix, "AHP判断矩阵");
    const invalidCells = new Set<string>();
    const n = matrix.length;
    matrix.forEach((row, i) => {
      row.forEach((value, j) => {
        if (value <= 0) invalidCells.add(`${Math.min(i, j)}-${Math.max(i, j)}`);
        if (i === j && Math.abs(value - 1) > 1e-6) invalidCells.add(`${i}-${j}`);
        if (Math.abs(value * matrix[j][i] - 1) > 1e-3) invalidCells.add(`${Math.min(i, j)}-${Math.max(i, j)}`);
      });
    });
    if (invalidCells.size > 0) {
      return { ok: false, message: "矩阵需满足正数、对角线为 1、互反性 aij * aji = 1。", weights: [], ci: 1, cr: 1, invalidCells: [...invalidCells] };
    }
    if (n === 1) {
      return { ok: true, message: "单项自动通过一致性校验。", weights: [1], lambdaMax: 1, ci: 0, cr: 0, invalidCells: [] };
    }

    const weights = powerIterationWeights(matrix);
    const aw = matrix.map((row) => row.reduce((sum, value, col) => sum + value * weights[col], 0));
    const lambdaMax = aw.reduce((sum, value, index) => sum + value / weights[index], 0) / n;
    const ci = (lambdaMax - n) / (n - 1);
    const riValues: Record<number, number> = { 1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45 };
    const ri = riValues[n] ?? 1.45;
    const cr = ri > 0 ? ci / ri : 0;
    const ok = cr <= 0.1;
    return {
      ok,
      message: ok ? `一致性通过，CR = ${cr.toFixed(4)}。` : `一致性未通过，CR = ${cr.toFixed(4)} > 0.1，红色格子建议优先调整。`,
      weights,
      lambdaMax,
      ci,
      cr,
      invalidCells: ok ? [] : ahpInconsistencyCells(matrix),
    };
  } catch (err) {
    return { ok: false, message: err instanceof Error ? err.message : String(err), weights: [], ci: 1, cr: 1, invalidCells: [] };
  }
}

function fahpDeviationCells(matrix: number[][], weights: number[]): string[] {
  const n = matrix.length;
  const scores = new Map<string, number>();
  for (let i = 0; i < n; i += 1) {
    for (let j = i + 1; j < n; j += 1) {
      const denominator = weights[i] + weights[j];
      const expected = denominator > 0 ? weights[i] / denominator : 0.5;
      scores.set(`${i}-${j}`, Math.abs(matrix[i][j] - expected));
    }
  }
  const maxScore = Math.max(0, ...scores.values());
  if (maxScore <= 0.05) return [];
  return [...scores.entries()]
    .filter(([, score]) => score >= maxScore * 0.8)
    .map(([key]) => key);
}

export function analyzeFAHP(matrix: number[][]): MatrixDiagnostic {
  try {
    assertSquareMatrix(matrix, "FAHP判断矩阵");
    const invalidCells = new Set<string>();
    const n = matrix.length;
    matrix.forEach((row, i) => {
      row.forEach((value, j) => {
        if (value < 0 || value > 1) invalidCells.add(`${Math.min(i, j)}-${Math.max(i, j)}`);
        if (i === j && Math.abs(value - 0.5) > 1e-6) invalidCells.add(`${i}-${j}`);
        if (Math.abs(value + matrix[j][i] - 1) > 1e-6) invalidCells.add(`${Math.min(i, j)}-${Math.max(i, j)}`);
      });
    });
    if (invalidCells.size > 0) {
      return { ok: false, message: "矩阵需满足 0-1、对角线为 0.5、互补性 aij + aji = 1。", weights: [], ci: 1, invalidCells: [...invalidCells] };
    }
    const result = calculateFAHP(matrix);
    const ok = result.ci <= 0.1;
    return {
      ok,
      message: ok ? `相容性通过，CI = ${result.ci.toFixed(4)}。` : `相容性偏弱，CI = ${result.ci.toFixed(4)} > 0.1，红色格子建议优先调整。`,
      weights: result.weights,
      ci: result.ci,
      invalidCells: ok ? [] : fahpDeviationCells(matrix, result.weights),
    };
  } catch (err) {
    return { ok: false, message: err instanceof Error ? err.message : String(err), weights: [], ci: 1, invalidCells: [] };
  }
}

export function calculateEqualWeights(ids: string[]): Record<string, number> {
  if (!ids.length) {
    throw new Error("请至少选择一个指标");
  }
  const weight = 1 / ids.length;
  return Object.fromEntries(ids.map((id) => [id, weight]));
}

export function calculateExpertWeights(scores: Record<string, number>): Record<string, number> {
  const entries = Object.entries(scores);
  if (!entries.length) {
    throw new Error("专家打分不能为空");
  }
  entries.forEach(([id, score]) => {
    if (!Number.isFinite(score) || score <= 0) {
      throw new Error(`${findIndicator(id).name} 的专家打分必须大于 0`);
    }
  });
  const weights = normalize(entries.map(([, score]) => score));
  return Object.fromEntries(entries.map(([id], index) => [id, weights[index]]));
}

export function calculateAHP(matrix: number[][]): AHPResult {
  assertSquareMatrix(matrix, "AHP判断矩阵");
  const n = matrix.length;
  matrix.forEach((row, i) => {
    row.forEach((value, j) => {
      if (value <= 0) {
        throw new Error("AHP判断矩阵元素必须为正数");
      }
      if (i === j && Math.abs(value - 1) > 1e-6) {
        throw new Error("AHP判断矩阵对角线元素必须为 1");
      }
      if (Math.abs(value * matrix[j][i] - 1) > 1e-3) {
        throw new Error("AHP判断矩阵必须满足互反性 aij * aji = 1");
      }
    });
  });

  if (n === 1) {
    return { weights: [1], lambdaMax: 1, ci: 0, cr: 0 };
  }

  const weights = powerIterationWeights(matrix);

  const aw = matrix.map((row) => row.reduce((sum, value, col) => sum + value * weights[col], 0));
  const lambdaMax = aw.reduce((sum, value, index) => sum + value / weights[index], 0) / n;
  const ci = (lambdaMax - n) / (n - 1);
  const riValues: Record<number, number> = { 1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45 };
  const ri = riValues[n] ?? 1.45;
  const cr = ri > 0 ? ci / ri : 0;
  if (cr > 0.1) {
    throw new Error(`AHP判断矩阵一致性不满足要求，CR = ${cr.toFixed(3)} > 0.1`);
  }
  return { weights, lambdaMax, ci, cr };
}

export function calculateFAHP(matrix: number[][]): FAHPResult {
  assertSquareMatrix(matrix, "FAHP判断矩阵");
  const n = matrix.length;
  matrix.forEach((row, i) => {
    row.forEach((value, j) => {
      if (value < 0 || value > 1) {
        throw new Error("FAHP判断矩阵元素必须在 0 到 1 之间");
      }
      if (i === j && Math.abs(value - 0.5) > 1e-6) {
        throw new Error("FAHP判断矩阵对角线元素必须为 0.5");
      }
      if (Math.abs(value + matrix[j][i] - 1) > 1e-6) {
        throw new Error("FAHP判断矩阵必须满足互补性 aij + aji = 1");
      }
    });
  });

  if (n === 1) {
    return { weights: [1], ci: 0 };
  }

  const rowSums = matrix.map((row) => row.reduce((sum, value) => sum + value, 0));
  let weights = rowSums.map((sum) => (sum + n / 2 - 1) / (n * (n - 1)));
  if (weights.some((value) => value < -1e-10)) {
    throw new Error("FAHP权重计算异常，请检查判断矩阵");
  }
  weights = normalize(weights.map((value) => Math.max(0, value)));

  const wStar = weights.map((wi) => weights.map((wj) => (wi + wj > 0 ? wi / (wi + wj) : 0.5)));
  const ci =
    matrix.reduce(
      (sum, row, i) => sum + row.reduce((rowSum, value, j) => rowSum + Math.abs(value + wStar[j][i] - 1), 0),
      0,
    ) /
    (n * n);
  return { weights, ci };
}

export function calculateFAHPFinalWeights(
  selectedIds: string[],
  level1Matrix: number[][],
  level2Matrices: Record<string, number[][]>,
): Record<string, number> {
  const categories = selectedCategories(selectedIds);
  if (!categories.length) {
    throw new Error("请至少选择一个指标");
  }
  const level1Weights = categories.length === 1 ? [1] : calculateFAHP(level1Matrix).weights;
  if (level1Weights.length !== categories.length) {
    throw new Error("FAHP一级矩阵维度与选中分类不一致");
  }

  const finalWeights: Record<string, number> = {};
  categories.forEach((category, categoryIndex) => {
    const matrix = level2Matrices[category.id] ?? [[0.5]];
    const level2Weights = category.indicators.length === 1 ? [1] : calculateFAHP(matrix).weights;
    if (level2Weights.length !== category.indicators.length) {
      throw new Error(`${category.shortName} 二级矩阵维度与指标数量不一致`);
    }
    category.indicators.forEach((indicator, indicatorIndex) => {
      finalWeights[indicator.id] = level1Weights[categoryIndex] * level2Weights[indicatorIndex];
    });
  });

  const normalized = normalize(Object.values(finalWeights));
  return Object.fromEntries(Object.keys(finalWeights).map((id, index) => [id, normalized[index]]));
}

export function calculateEntropyWeights(
  dataMatrix: number[][],
  indicatorIds: string[],
  benefitFlags: boolean[],
): Record<string, number> {
  if (dataMatrix.length < 2) {
    throw new Error("熵权法至少需要 2 个样本");
  }
  if (!indicatorIds.length || benefitFlags.length !== indicatorIds.length) {
    throw new Error("熵权法指标数量不一致");
  }
  dataMatrix.forEach((row) => {
    if (row.length !== indicatorIds.length) {
      throw new Error("熵权法样本列数必须与指标数量一致");
    }
    row.forEach((value) => {
      if (!Number.isFinite(value)) {
        throw new Error("熵权法样本包含无效数值");
      }
    });
  });

  const rowCount = dataMatrix.length;
  const colCount = indicatorIds.length;
  const normalized = dataMatrix.map(() => Array.from({ length: colCount }, () => 0));
  for (let col = 0; col < colCount; col += 1) {
    const values = dataMatrix.map((row) => row[col]);
    const min = Math.min(...values);
    const max = Math.max(...values);
    for (let row = 0; row < rowCount; row += 1) {
      if (Math.abs(max - min) < 1e-12) {
        normalized[row][col] = 1;
      } else if (benefitFlags[col]) {
        normalized[row][col] = (dataMatrix[row][col] - min) / (max - min);
      } else {
        normalized[row][col] = (max - dataMatrix[row][col]) / (max - min);
      }
    }
  }

  const entropy = Array.from({ length: colCount }, (_, col) => {
    const colSum = normalized.reduce((sum, row) => sum + row[col], 0);
    const pValues = normalized.map((row) => (colSum > 0 ? row[col] / colSum : 1 / rowCount)).filter((value) => value > 0);
    return -pValues.reduce((sum, value) => sum + value * Math.log(value), 0) / Math.log(rowCount);
  });
  const diversity = entropy.map((value) => 1 - value);
  const weights = diversity.reduce((sum, value) => sum + value, 0) <= 1e-12
    ? Array.from({ length: colCount }, () => 1 / colCount)
    : normalize(diversity);
  return Object.fromEntries(indicatorIds.map((id, index) => [id, weights[index]]));
}

function interpolate(x: number, x1: number, x2: number, y1: number, y2: number): number {
  if (Math.abs(x2 - x1) < 1e-12) {
    return y1;
  }
  const ratio = (x - x1) / (x2 - x1);
  return y1 + ratio * (y2 - y1);
}

function inRange(value: number, min: number, max: number): boolean {
  return value >= Math.min(min, max) && value <= Math.max(min, max);
}

export function calculateIndicatorScore(value: number, range: EvaluationRange): { score: number; grade: string } {
  const score = calculateSatisfaction(value, range) * 100;
  return { score, grade: getGrade(score) };
}

function intervalMin(interval: EvaluationInterval): number {
  return interval.min ?? Number.NEGATIVE_INFINITY;
}

function intervalMax(interval: EvaluationInterval): number {
  return interval.max ?? Number.POSITIVE_INFINITY;
}

function containsInterval(value: number, interval: EvaluationInterval): boolean {
  return value >= intervalMin(interval) && value <= intervalMax(interval);
}

function intervalLength(interval: EvaluationInterval): number {
  if (interval.min === null || interval.max === null) return Number.POSITIVE_INFINITY;
  return Math.abs(interval.max - interval.min);
}

function distanceToInterval(value: number, interval: EvaluationInterval): number {
  const min = intervalMin(interval);
  const max = intervalMax(interval);
  if (value < min) return min - value;
  if (value > max) return value - max;
  return 0;
}

function distanceToSatisfaction(value: number, intervals: EvaluationInterval[]): number {
  return Math.min(...intervals.map((interval) => distanceToInterval(value, interval)));
}

export function calculateSatisfaction(value: number, range: EvaluationRange): number {
  if (!Number.isFinite(value)) return 0;
  if (range.satisfaction.some((interval) => containsInterval(value, interval))) return 1;
  const tolerance = range.tolerance.find((interval) => containsInterval(value, interval));
  if (!tolerance) return 0;
  const toleranceLength = intervalLength(tolerance);
  if (!Number.isFinite(toleranceLength) || toleranceLength <= 1e-12) return 0;
  const distance = distanceToSatisfaction(value, range.satisfaction);
  return Math.max(0, Math.min(1, 1 - distance / toleranceLength));
}

export function getGrade(score: number): string {
  if (score >= 90) return "优秀";
  if (score >= 80) return "良好";
  if (score >= 60) return "一般";
  if (score >= 40) return "较差";
  return "很差";
}

export function evaluate(
  selectedIds: string[],
  weights: Record<string, number>,
  ranges: Record<string, EvaluationRange>,
  values: Record<string, number>,
): EvaluationResult {
  const rows = selectedIds.map((id) => {
    const indicator = findIndicator(id);
    const value = values[id];
    if (!Number.isFinite(value)) {
      throw new Error(`${indicator.name} 的实测值无效`);
    }
    const range = ranges[id] ?? DEFAULT_RANGES[id];
    const { score, grade } = calculateIndicatorScore(value, range);
    const weight = weights[id] ?? 0;
    const satisfaction = calculateSatisfaction(value, range);
    return {
      indicator,
      value,
      weight,
      satisfaction,
      weightedSatisfaction: weight * satisfaction,
      score,
      grade,
      weightedScore: score * weight,
    };
  });
  const overallScore = rows.reduce((sum, row) => sum + row.weightedScore, 0);
  const categoryScores = CATEGORIES.map((category) => {
    const categoryRows = rows.filter((row) => row.indicator.categoryId === category.id);
    const weight = categoryRows.reduce((sum, row) => sum + row.weight, 0);
    const weightedScore = categoryRows.reduce((sum, row) => sum + row.weightedScore, 0);
    const weightedSatisfaction = categoryRows.reduce((sum, row) => sum + row.weightedSatisfaction, 0);
    const satisfaction = weight > 0 ? weightedSatisfaction / weight : 0;
    return {
      categoryId: category.id,
      categoryName: category.shortName,
      weight,
      satisfaction,
      score: weight > 0 ? weightedScore / weight : 0,
    };
  }).filter((category) => category.weight > 0);
  return {
    overallScore,
    overallGrade: getGrade(overallScore),
    rows,
    categoryScores,
    topsis: { dPlus: 0, dMinus: 0, cRaw: 0 },
    safety: { sSafe: 1, alpha: 0, beta: DEFAULT_BETA, penalty: 1 },
  };
}

export function evaluateSATOPSIS(
  selectedIds: string[],
  weights: Record<string, number>,
  ranges: Record<string, EvaluationRange>,
  values: Record<string, number>,
  alpha: number = DEFAULT_ALPHA,
  beta: number = DEFAULT_BETA,
): EvaluationResult {
  // 第一步：计算各指标满意度
  const rows: IndicatorEvaluation[] = selectedIds.map((id) => {
    const indicator = findIndicator(id);
    const value = values[id];
    if (!Number.isFinite(value)) {
      throw new Error(`${indicator.name} 的实测值无效`);
    }
    const range = ranges[id] ?? DEFAULT_RANGES[id];
    const satisfaction = calculateSatisfaction(value, range);
    const weight = weights[id] ?? 0;
    return {
      indicator,
      value,
      weight,
      satisfaction,
      weightedSatisfaction: weight * satisfaction,
      score: satisfaction * 100,
      grade: getGrade(satisfaction * 100),
    };
  });

  const categoryScores = CATEGORIES.map((category) => {
    const categoryRows = rows.filter((row) => row.indicator.categoryId === category.id);
    const weight = categoryRows.reduce((sum, row) => sum + row.weight, 0);
    const weightedSat = categoryRows.reduce((sum, row) => sum + row.weightedSatisfaction, 0);
    const satisfaction = weight > 0 ? weightedSat / weight : 0;
    return {
      categoryId: category.id,
      categoryName: category.shortName,
      weight,
      satisfaction,
      score: satisfaction * 100,
    };
  }).filter((category) => category.weight > 0);

  // 第二步：TOPSIS 计算。按最新流程，一级指标满意度进入距离公式。
  const dPlusSq = categoryScores.reduce((sum, category) => {
    const diff = 1 - category.satisfaction;
    return sum + category.weight * diff * diff;
  }, 0);
  const dMinusSq = categoryScores.reduce((sum, category) => {
    return sum + category.weight * category.satisfaction * category.satisfaction;
  }, 0);
  const dPlus = Math.sqrt(dPlusSq);
  const dMinus = Math.sqrt(dMinusSq);
  const cRaw = dPlus + dMinus > 0 ? dMinus / (dPlus + dMinus) : 0;

  // 第三步：安全连续惩罚 SCP
  const safetyCategory = categoryScores.find((category) => category.categoryId === "safety");
  const sSafe = safetyCategory ? safetyCategory.satisfaction : 1;
  const boundedBeta = Math.min(1, Math.max(Number.EPSILON, beta));
  const penalty = 1 - alpha * (1 - sSafe) ** boundedBeta;
  const finalC = cRaw * penalty;
  const overallScore = finalC * 100;

  return {
    overallScore,
    overallGrade: getGrade(overallScore),
    rows,
    categoryScores,
    topsis: { dPlus, dMinus, cRaw },
    safety: { sSafe, alpha, beta: boundedBeta, penalty },
  };
}
