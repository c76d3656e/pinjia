import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  analyzeAHP,
  analyzeFAHP,
  calculateAHP,
  calculateEntropyWeights,
  calculateEqualWeights,
  calculateExpertWeights,
  calculateFAHPFinalWeights,
  DEFAULT_RANGES,
  evaluate,
  EvaluationRange,
  MatrixDiagnostic,
} from "./lib/evaluation";
import { CATEGORIES, CategoryId, findIndicator, INDICATORS, IndicatorCategory, selectedCategories } from "./lib/indicators";
import { HistoryEntry, pushHistoryEntry, readHistory, WeightMethod as HistoryWeightMethod, writeHistory } from "./lib/history";
import "./styles.css";

type StepId = "indicators" | "weights" | "ranges" | "values" | "result";
type WeightMethod = "equal" | "expert" | "ahp" | "fahp" | "entropy";

const STEPS: Array<{ id: StepId; label: string }> = [
  { id: "indicators", label: "1. 指标选择" },
  { id: "weights", label: "2. 权重设置" },
  { id: "ranges", label: "3. 范围设置" },
  { id: "values", label: "4. 真实值输入" },
  { id: "result", label: "5. 综合评价" },
];

const METHOD_LABEL: Record<WeightMethod, string> = {
  equal: "等权重",
  expert: "专家打分",
  ahp: "AHP",
  fahp: "FAHP",
  entropy: "熵权法",
};

function fullMatrix(size: number, diagonal: number): number[][] {
  return Array.from({ length: size }, (_, row) => Array.from({ length: size }, (_, col) => (row === col ? diagonal : diagonal)));
}

function resizeMatrix(matrix: number[][], size: number, diagonal: number): number[][] {
  return Array.from({ length: size }, (_, row) =>
    Array.from({ length: size }, (_, col) => (row === col ? diagonal : matrix[row]?.[col] ?? diagonal)),
  );
}

function cloneRange(range: EvaluationRange): EvaluationRange {
  return {
    excellent: { ...range.excellent },
    good: { ...range.good },
    average: { ...range.average },
    poor: { ...range.poor },
    verypoor: { ...range.verypoor },
  };
}

function defaultRanges(): Record<string, EvaluationRange> {
  return Object.fromEntries(Object.entries(DEFAULT_RANGES).map(([id, range]) => [id, cloneRange(range)]));
}

function defaultMeasuredValues(): Record<string, number> {
  return Object.fromEntries(INDICATORS.map((indicator) => [indicator.id, DEFAULT_RANGES[indicator.id].excellent.value]));
}

function defaultExpertScores(): Record<string, number> {
  return Object.fromEntries(INDICATORS.map((indicator) => [indicator.id, 5]));
}

function defaultEntropyRows(): number[][] {
  return [
    [5, 0.1, 1.5, 0.2, 3, 20, 70, 1.5, 0.45, 0],
    [7, 0.3, 1.35, 0.45, 3.4, 22, 110, 2.0, 0.47, -1.5],
    [12, 0.5, 1.25, 0.75, 3.9, 24, 160, 2.5, 0.49, -2.5],
    [15, 0.7, 1.1, 1.0, 4.5, 26, 220, 3.5, 0.51, -3.5],
  ];
}

function numberValue(value: string): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function cloneMatrix(matrix: number[][]): number[][] {
  return matrix.map((row) => [...row]);
}

function App() {
  const [step, setStep] = useState<StepId>("indicators");
  const [selectedIds, setSelectedIds] = useState<string[]>(INDICATORS.map((indicator) => indicator.id));
  const [method, setMethod] = useState<WeightMethod>("fahp");
  const [expertScores, setExpertScores] = useState(defaultExpertScores);
  const [ahpMatrix, setAhpMatrix] = useState(fullMatrix(INDICATORS.length, 1));
  const [fahpLevel1, setFahpLevel1] = useState(fullMatrix(CATEGORIES.length, 0.5));
  const [fahpLevel2, setFahpLevel2] = useState<Record<CategoryId, number[][]>>({
    technical: fullMatrix(6, 0.5),
    safety: fullMatrix(2, 0.5),
    economic: fullMatrix(2, 0.5),
  });
  const [entropyRows, setEntropyRows] = useState(defaultEntropyRows);
  const [ranges, setRanges] = useState(defaultRanges);
  const [measuredValues, setMeasuredValues] = useState(defaultMeasuredValues);
  const [history, setHistory] = useState<HistoryEntry[]>(() => readHistory());
  const [lastSavedKey, setLastSavedKey] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);

  const selected = useMemo(() => selectedIds.map(findIndicator), [selectedIds]);
  const selectedCats = useMemo(() => selectedCategories(selectedIds), [selectedIds]);
  const ahpVisibleMatrix = useMemo(() => resizeMatrix(ahpMatrix, selectedIds.length, 1), [ahpMatrix, selectedIds.length]);
  const fahpVisibleLevel1 = useMemo(() => resizeMatrix(fahpLevel1, selectedCats.length, 0.5), [fahpLevel1, selectedCats.length]);

  const ahpDiagnostic = useMemo(() => analyzeAHP(ahpVisibleMatrix), [ahpVisibleMatrix]);
  const fahpLevel1Diagnostic = useMemo(() => analyzeFAHP(fahpVisibleLevel1), [fahpVisibleLevel1]);
  const fahpLevel2Diagnostics = useMemo(() => {
    return Object.fromEntries(
      selectedCats.map((category) => [
        category.id,
        analyzeFAHP(resizeMatrix(fahpLevel2[category.id] ?? [], category.indicators.length, 0.5)),
      ]),
    ) as Record<CategoryId, MatrixDiagnostic>;
  }, [fahpLevel2, selectedCats]);

  const weightState = useMemo((): { weights: Record<string, number>; error: string } => {
    try {
      if (!selectedIds.length) return { weights: {}, error: "请至少选择一个指标。" };
      if (method === "equal") return { weights: calculateEqualWeights(selectedIds), error: "" };
      if (method === "expert") {
        return { weights: calculateExpertWeights(Object.fromEntries(selectedIds.map((id) => [id, expertScores[id] ?? 0]))), error: "" };
      }
      if (method === "ahp") {
        const result = calculateAHP(ahpVisibleMatrix);
        return { weights: Object.fromEntries(selectedIds.map((id, index) => [id, result.weights[index]])), error: "" };
      }
      if (method === "entropy") {
        const sourceIndexes = selectedIds.map((id) => INDICATORS.findIndex((indicator) => indicator.id === id));
        const matrix = entropyRows.map((row) => sourceIndexes.map((index) => row[index]));
        return { weights: calculateEntropyWeights(matrix, selectedIds, selected.map((indicator) => indicator.isPositive)), error: "" };
      }
      const level2Matrices = Object.fromEntries(
        selectedCats.map((category) => [
          category.id,
          category.indicators.length === 1
            ? [[0.5]]
            : resizeMatrix(fahpLevel2[category.id] ?? [], category.indicators.length, 0.5),
        ]),
      );
      return { weights: calculateFAHPFinalWeights(selectedIds, selectedCats.length === 1 ? [[0.5]] : fahpVisibleLevel1, level2Matrices), error: "" };
    } catch (err) {
      return { weights: {}, error: err instanceof Error ? err.message : String(err) };
    }
  }, [ahpVisibleMatrix, entropyRows, expertScores, fahpLevel2, fahpVisibleLevel1, method, selected, selectedCats, selectedIds]);

  const evaluationState = useMemo(() => {
    try {
      if (!Object.keys(weightState.weights).length) return { result: null, error: "" };
      return { result: evaluate(selectedIds, weightState.weights, ranges, measuredValues), error: "" };
    } catch (err) {
      return { result: null, error: err instanceof Error ? err.message : String(err) };
    }
  }, [measuredValues, ranges, selectedIds, weightState.weights]);

  const updateSelected = (id: string, checked: boolean) => {
    const next = checked ? [...selectedIds, id] : selectedIds.filter((item) => item !== id);
    setSelectedIds(next);
    setAhpMatrix((matrix) => resizeMatrix(matrix, next.length, 1));
    setFahpLevel1((matrix) => resizeMatrix(matrix, selectedCategories(next).length, 0.5));
  };

  const setAhpPair = (row: number, col: number, value: number) => {
    setAhpMatrix((matrix) => {
      const next = resizeMatrix(matrix, selectedIds.length, 1).map((item) => [...item]);
      next[row][col] = value;
      next[col][row] = value > 0 ? 1 / value : 1;
      return next;
    });
  };

  const setFahpPair = (row: number, col: number, value: number) => {
    setFahpLevel1((matrix) => {
      const next = resizeMatrix(matrix, selectedCats.length, 0.5).map((item) => [...item]);
      const bounded = clamp(value, 0, 1);
      next[row][col] = bounded;
      next[col][row] = 1 - bounded;
      return next;
    });
  };

  const setFahpLevel2Pair = (categoryId: CategoryId, row: number, col: number, value: number) => {
    setFahpLevel2((matrices) => {
      const category = selectedCats.find((item) => item.id === categoryId);
      const size = category?.indicators.length ?? 1;
      const nextMatrix = resizeMatrix(matrices[categoryId] ?? [], size, 0.5).map((item) => [...item]);
      const bounded = clamp(value, 0, 1);
      nextMatrix[row][col] = bounded;
      nextMatrix[col][row] = 1 - bounded;
      return { ...matrices, [categoryId]: nextMatrix };
    });
  };

  const goNext = () => {
    const index = STEPS.findIndex((item) => item.id === step);
    if (index < STEPS.length - 1) setStep(STEPS[index + 1].id);
  };

  const weights = weightState.weights;
  const result = evaluationState.result;
  const error = weightState.error || evaluationState.error;

  const resultKey = useMemo(() => {
    if (!result || error) return "";
    return JSON.stringify({
      method,
      selectedIds,
      weights,
      ranges,
      measuredValues,
      score: result.overallScore,
      rows: result.rows.map((row) => [row.indicator.id, row.value, row.score, row.weight]),
    });
  }, [error, measuredValues, method, ranges, result, selectedIds, weights]);

  useEffect(() => {
    if (step !== "result" || !result || !resultKey || resultKey === lastSavedKey) return;
    const entry: HistoryEntry = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      createdAt: new Date().toISOString(),
      method: method as HistoryWeightMethod,
      selectedIds: [...selectedIds],
      weights: { ...weights },
      ranges: Object.fromEntries(Object.entries(ranges).map(([id, range]) => [id, cloneRange(range)])),
      measuredValues: { ...measuredValues },
      result,
      process: {
        expertScores: { ...expertScores },
        ahpMatrix: cloneMatrix(ahpVisibleMatrix),
        fahpLevel1: cloneMatrix(fahpVisibleLevel1),
        fahpLevel2: Object.fromEntries(Object.entries(fahpLevel2).map(([id, matrix]) => [id, cloneMatrix(matrix)])),
        entropyRows: cloneMatrix(entropyRows),
      },
    };
    setHistory((current) => {
      const next = pushHistoryEntry(current, entry, 10);
      writeHistory(next);
      return next;
    });
    setLastSavedKey(resultKey);
  }, [
    ahpVisibleMatrix,
    entropyRows,
    error,
    expertScores,
    fahpLevel1,
    fahpLevel2,
    fahpVisibleLevel1,
    lastSavedKey,
    measuredValues,
    method,
    ranges,
    result,
    resultKey,
    selectedIds,
    step,
    weights,
  ]);

  return (
    <main className="app-shell">
      <header className="app-header">
        <h1>爆破效果综合评价系统</h1>
        <button type="button" className="history-trigger" onClick={() => setHistoryOpen(true)}>
          历史记录
          <span>{history.length}</span>
        </button>
      </header>

      <HistoryDrawer
        open={historyOpen}
        history={history}
        onClose={() => setHistoryOpen(false)}
        onClear={() => {
          setHistory([]);
          writeHistory([]);
        }}
      />

      <nav className="step-tabs" aria-label="评价流程">
        {STEPS.map((item) => (
          <button key={item.id} className={step === item.id ? "active" : ""} type="button" onClick={() => setStep(item.id)}>
            {item.label}
          </button>
        ))}
      </nav>

      {error ? <div className="notice error">{error}</div> : null}

      <section className="step-panel">
        {step === "indicators" ? (
          <IndicatorStep selectedIds={selectedIds} onToggle={updateSelected} onSelectAll={() => setSelectedIds(INDICATORS.map((indicator) => indicator.id))} onClear={() => setSelectedIds([])} onNext={goNext} />
        ) : null}

        {step === "weights" ? (
          <WeightStep
            method={method}
            setMethod={setMethod}
            selectedIds={selectedIds}
            selected={selected}
            selectedCats={selectedCats}
            expertScores={expertScores}
            setExpertScores={setExpertScores}
            ahpMatrix={ahpVisibleMatrix}
            ahpDiagnostic={ahpDiagnostic}
            setAhpPair={setAhpPair}
            fahpLevel1={fahpVisibleLevel1}
            fahpLevel1Diagnostic={fahpLevel1Diagnostic}
            fahpLevel2={fahpLevel2}
            fahpLevel2Diagnostics={fahpLevel2Diagnostics}
            setFahpPair={setFahpPair}
            setFahpLevel2Pair={setFahpLevel2Pair}
            entropyRows={entropyRows}
            setEntropyRows={setEntropyRows}
            weights={weights}
            onNext={goNext}
          />
        ) : null}

        {step === "ranges" ? (
          <RangeStep selectedIds={selectedIds} ranges={ranges} setRanges={setRanges} onNext={goNext} />
        ) : null}

        {step === "values" ? (
          <ValueStep selectedIds={selectedIds} values={measuredValues} setValues={setMeasuredValues} onNext={goNext} />
        ) : null}

        {step === "result" ? (
          <ResultStep result={result} weights={weights} selectedIds={selectedIds} error={error} />
        ) : null}
      </section>
    </main>
  );
}

function IndicatorStep({
  selectedIds,
  onToggle,
  onSelectAll,
  onClear,
  onNext,
}: {
  selectedIds: string[];
  onToggle: (id: string, checked: boolean) => void;
  onSelectAll: () => void;
  onClear: () => void;
  onNext: () => void;
}) {
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2>选择评价指标</h2>
          <p>按现有系统的三类指标组织，至少选择一个指标。</p>
        </div>
        <div className="actions">
          <button type="button" onClick={onSelectAll}>全选</button>
          <button type="button" onClick={onClear}>清空</button>
        </div>
      </div>
      <div className="category-grid">
        {CATEGORIES.map((category) => (
          <section className="category-section" key={category.id}>
            <h3>{category.name}</h3>
            {category.indicators.map((indicator) => (
              <label className="check-row" key={indicator.id}>
                <input type="checkbox" checked={selectedIds.includes(indicator.id)} onChange={(event) => onToggle(indicator.id, event.target.checked)} />
                <span>{indicator.name}</span>
                <small>{indicator.unit || "无单位"}</small>
              </label>
            ))}
          </section>
        ))}
      </div>
      <FooterActions disabled={!selectedIds.length} onNext={onNext} nextLabel="下一步：权重设置" />
    </div>
  );
}

function WeightStep(props: {
  method: WeightMethod;
  setMethod: (method: WeightMethod) => void;
  selectedIds: string[];
  selected: ReturnType<typeof findIndicator>[];
  selectedCats: IndicatorCategory[];
  expertScores: Record<string, number>;
  setExpertScores: React.Dispatch<React.SetStateAction<Record<string, number>>>;
  ahpMatrix: number[][];
  ahpDiagnostic: MatrixDiagnostic;
  setAhpPair: (row: number, col: number, value: number) => void;
  fahpLevel1: number[][];
  fahpLevel1Diagnostic: MatrixDiagnostic;
  fahpLevel2: Record<CategoryId, number[][]>;
  fahpLevel2Diagnostics: Record<CategoryId, MatrixDiagnostic>;
  setFahpPair: (row: number, col: number, value: number) => void;
  setFahpLevel2Pair: (categoryId: CategoryId, row: number, col: number, value: number) => void;
  entropyRows: number[][];
  setEntropyRows: React.Dispatch<React.SetStateAction<number[][]>>;
  weights: Record<string, number>;
  onNext: () => void;
}) {
  const methodReady = props.method !== "ahp" || props.ahpDiagnostic.ok;
  const fahpReady = props.method !== "fahp" || (props.fahpLevel1Diagnostic.ok && props.selectedCats.every((category) => props.fahpLevel2Diagnostics[category.id]?.ok));
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2>设置指标权重</h2>
          <p>矩阵输入后立即计算权重和一致性，红色格子表示优先检查项。</p>
        </div>
        <div className="method-tabs">
          {(Object.keys(METHOD_LABEL) as WeightMethod[]).map((key) => (
            <button key={key} className={props.method === key ? "active" : ""} type="button" onClick={() => props.setMethod(key)}>
              {METHOD_LABEL[key]}
            </button>
          ))}
        </div>
      </div>

      {props.method === "equal" ? <p className="hint">等权重会将所有选中指标平均分配权重。</p> : null}
      {props.method === "expert" ? (
        <InputGrid ids={props.selectedIds} values={props.expertScores} onChange={(id, value) => props.setExpertScores((scores) => ({ ...scores, [id]: value }))} />
      ) : null}
      {props.method === "ahp" ? (
        <MatrixEditor title="AHP判断矩阵" labels={props.selected.map((indicator) => indicator.name)} matrix={props.ahpMatrix} diagonal={1} min={0.111} max={9} step={0.1} diagnostic={props.ahpDiagnostic} onPairChange={props.setAhpPair} />
      ) : null}
      {props.method === "fahp" ? (
        <div className="stack">
          <MatrixEditor title="FAHP一级指标矩阵" labels={props.selectedCats.map((category) => category.shortName)} matrix={props.fahpLevel1} diagonal={0.5} min={0} max={1} step={0.01} diagnostic={props.fahpLevel1Diagnostic} onPairChange={props.setFahpPair} />
          {props.selectedCats.map((category) => (
            <MatrixEditor
              key={category.id}
              title={`${category.shortName}二级指标矩阵`}
              labels={category.indicators.map((indicator) => indicator.name)}
              matrix={resizeMatrix(props.fahpLevel2[category.id] ?? [], category.indicators.length, 0.5)}
              diagonal={0.5}
              min={0}
              max={1}
              step={0.01}
              diagnostic={props.fahpLevel2Diagnostics[category.id]}
              onPairChange={(row, col, value) => props.setFahpLevel2Pair(category.id, row, col, value)}
            />
          ))}
        </div>
      ) : null}
      {props.method === "entropy" ? <EntropyEditor rows={props.entropyRows} setRows={props.setEntropyRows} selectedIds={props.selectedIds} /> : null}

      <WeightPreview selectedIds={props.selectedIds} weights={props.weights} />
      <FooterActions disabled={!Object.keys(props.weights).length || !methodReady || !fahpReady} onNext={props.onNext} nextLabel="下一步：范围设置" />
    </div>
  );
}

function RangeStep({
  selectedIds,
  ranges,
  setRanges,
  onNext,
}: {
  selectedIds: string[];
  ranges: Record<string, EvaluationRange>;
  setRanges: React.Dispatch<React.SetStateAction<Record<string, EvaluationRange>>>;
  onNext: () => void;
}) {
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2>设置指标评价范围</h2>
          <p>五级标准：优、良、一般、较差、很差。默认值沿用现有系统。</p>
        </div>
        <button type="button" onClick={() => setRanges(defaultRanges())}>恢复默认范围</button>
      </div>
      <RangeEditor selectedIds={selectedIds} ranges={ranges} onRangeChange={(id, next) => setRanges((current) => ({ ...current, [id]: next }))} />
      <FooterActions disabled={!selectedIds.length} onNext={onNext} nextLabel="下一步：真实值输入" />
    </div>
  );
}

function ValueStep({
  selectedIds,
  values,
  setValues,
  onNext,
}: {
  selectedIds: string[];
  values: Record<string, number>;
  setValues: React.Dispatch<React.SetStateAction<Record<string, number>>>;
  onNext: () => void;
}) {
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2>输入真实值</h2>
          <p>每个选中指标单独录入真实测量值，结果页会按范围自动评分。</p>
        </div>
      </div>
      <div className="value-grid">
        {selectedIds.map((id) => {
          const indicator = findIndicator(id);
          return (
            <label key={id} className="field-row">
              <span>{indicator.name}{indicator.unit ? ` (${indicator.unit})` : ""}</span>
              <input type="number" step="0.01" value={values[id] ?? 0} onChange={(event) => setValues((current) => ({ ...current, [id]: numberValue(event.target.value) }))} />
            </label>
          );
        })}
      </div>
      <FooterActions disabled={!selectedIds.length} onNext={onNext} nextLabel="查看综合评价" />
    </div>
  );
}

function HistoryDrawer({
  open,
  history,
  onClose,
  onClear,
}: {
  open: boolean;
  history: HistoryEntry[];
  onClose: () => void;
  onClear: () => void;
}) {
  return (
    <div className={`history-drawer ${open ? "open" : ""}`} aria-hidden={!open}>
      <button type="button" className="drawer-backdrop" onClick={onClose} tabIndex={open ? 0 : -1} aria-label="关闭历史记录" />
      <aside className="drawer-panel" aria-label="历史记录">
        <div className="drawer-header">
          <div>
            <h2>历史记录</h2>
            <p>最近 10 次综合评价</p>
          </div>
          <button type="button" onClick={onClose}>关闭</button>
        </div>
        <div className="drawer-actions">
          <button type="button" onClick={onClear} disabled={!history.length}>清空历史</button>
        </div>
        {history.length ? (
          <div className="history-list drawer-list">
            {history.map((entry) => (
              <details key={entry.id} className="history-item">
                <summary>
                  <span>{new Date(entry.createdAt).toLocaleString()}</span>
                  <strong>{entry.result.overallScore.toFixed(2)} 分 / {entry.result.overallGrade}</strong>
                  <small>{METHOD_LABEL[entry.method]}，{entry.selectedIds.length} 个指标</small>
                </summary>
                <div className="history-detail">
                  <div className="history-meta">
                    <span>权重和 {Object.values(entry.weights).reduce((sum, value) => sum + value, 0).toFixed(6)}</span>
                    <span>真实值 {Object.keys(entry.measuredValues).length} 项</span>
                    <span>明细 {entry.result.rows.length} 行</span>
                  </div>
                  <div className="history-rows">
                    {entry.result.rows.map((row) => (
                      <div key={row.indicator.id} className={`history-row grade-${gradeClass(row.grade)}`}>
                        <span>{row.indicator.name}</span>
                        <strong>{row.score.toFixed(1)}</strong>
                        <small>{row.grade}</small>
                      </div>
                    ))}
                  </div>
                </div>
              </details>
            ))}
          </div>
        ) : (
          <div className="notice info">还没有历史记录。</div>
        )}
      </aside>
    </div>
  );
}

function ResultStep({ result, weights, selectedIds, error }: { result: ReturnType<typeof evaluate> | null; weights: Record<string, number>; selectedIds: string[]; error: string }) {
  if (error) return <div className="notice error">{error}</div>;
  if (!result) return <div className="notice warning">请先完成指标、权重、范围和真实值输入。</div>;
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2>综合评价结果</h2>
          <p>总分为各指标得分乘最终权重后求和。</p>
        </div>
        <span className="weight-total">权重和 {Object.values(weights).reduce((sum, value) => sum + value, 0).toFixed(6)}</span>
      </div>
      <div className="score-board">
        <div><span>综合得分</span><strong>{result.overallScore.toFixed(2)}</strong></div>
        <div><span>综合等级</span><strong>{result.overallGrade}</strong></div>
        <div><span>指标数量</span><strong>{selectedIds.length}</strong></div>
        {result.categoryScores.map((category) => (
          <div key={category.categoryId}><span>{category.categoryName}</span><strong>{category.score.toFixed(1)}</strong></div>
        ))}
      </div>
      <div className="table-wrap">
        <table className="result-table">
          <thead>
            <tr>
              <th>指标名称</th>
              <th>真实值</th>
              <th>权重</th>
              <th>得分</th>
              <th>等级</th>
              <th>加权得分</th>
            </tr>
          </thead>
          <tbody>
            {result.rows.map((row) => (
              <tr key={row.indicator.id} className={`grade-${gradeClass(row.grade)}`}>
                <td>{row.indicator.name}</td>
                <td>{row.value}</td>
                <td>{(row.weight * 100).toFixed(2)}%</td>
                <td>{row.score.toFixed(2)}</td>
                <td><span className={`grade-badge grade-${gradeClass(row.grade)}`}>{row.grade}</span></td>
                <td>{row.weightedScore.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function gradeClass(grade: string): string {
  if (grade.includes("优")) return "excellent";
  if (grade.includes("良")) return "good";
  if (grade.includes("一般")) return "average";
  if (grade.includes("较差")) return "poor";
  return "bad";
}

function MatrixEditor({
  title,
  labels,
  matrix,
  diagonal,
  min,
  max,
  step,
  diagnostic,
  onPairChange,
}: {
  title: string;
  labels: string[];
  matrix: number[][];
  diagonal: number;
  min: number;
  max: number;
  step: number;
  diagnostic: MatrixDiagnostic;
  onPairChange: (row: number, col: number, value: number) => void;
}) {
  if (labels.length <= 1) {
    return <div className="notice info">{title}：单项自动通过，权重为 1。</div>;
  }
  return (
    <section className="matrix-block">
      <div className="matrix-title">
        <h3>{title}</h3>
        <span className={diagnostic.ok ? "status ok" : "status bad"}>{diagnostic.message}</span>
      </div>
      <div className="table-wrap compact">
        <table className="matrix-table">
          <thead>
            <tr>
              <th></th>
              {labels.map((label) => <th key={label}>{label}</th>)}
            </tr>
          </thead>
          <tbody>
            {labels.map((rowLabel, row) => (
              <tr key={rowLabel}>
                <th>{rowLabel}</th>
                {labels.map((_, col) => {
                  const key = `${Math.min(row, col)}-${Math.max(row, col)}`;
                  const invalid = diagnostic.invalidCells.includes(key);
                  return (
                    <td key={`${row}-${col}`} className={invalid ? "cell-error" : ""}>
                      {row === col ? (
                        diagonal
                      ) : row < col ? (
                        <input
                          aria-label={`${rowLabel} 相对 ${labels[col]}`}
                          type="number"
                          min={min}
                          max={max}
                          step={step}
                          value={Number((matrix[row]?.[col] ?? diagonal).toFixed(3))}
                          onChange={(event) => onPairChange(row, col, numberValue(event.target.value))}
                        />
                      ) : (
                        Number((matrix[row]?.[col] ?? diagonal).toFixed(3))
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {diagnostic.weights.length ? (
        <div className="inline-weights">
          {diagnostic.weights.map((weight, index) => <span key={labels[index]}>{labels[index]} {(weight * 100).toFixed(2)}%</span>)}
        </div>
      ) : null}
    </section>
  );
}

function InputGrid({ ids, values, onChange }: { ids: string[]; values: Record<string, number>; onChange: (id: string, value: number) => void }) {
  return (
    <div className="value-grid">
      {ids.map((id) => {
        const indicator = findIndicator(id);
        return (
          <label key={id} className="field-row">
            <span>{indicator.name}</span>
            <input min="0.1" step="0.1" type="number" value={values[id] ?? 0} onChange={(event) => onChange(id, numberValue(event.target.value))} />
          </label>
        );
      })}
    </div>
  );
}

function EntropyEditor({ rows, setRows, selectedIds }: { rows: number[][]; setRows: React.Dispatch<React.SetStateAction<number[][]>>; selectedIds: string[] }) {
  return (
    <section>
      <div className="matrix-title">
        <h3>熵权法样本矩阵</h3>
        <button type="button" onClick={() => setRows((current) => [...current, Array.from({ length: INDICATORS.length }, () => 0)])}>添加样本</button>
      </div>
      <p className="hint">至少 2 个样本，当前选中的指标列参与熵权计算。</p>
      <div className="table-wrap compact">
        <table>
          <thead>
            <tr>
              <th>样本</th>
              {INDICATORS.map((indicator) => <th key={indicator.id}>{indicator.name}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                <th>#{rowIndex + 1}</th>
                {INDICATORS.map((indicator, colIndex) => (
                  <td key={indicator.id} className={selectedIds.includes(indicator.id) ? "" : "muted-cell"}>
                    <input
                      type="number"
                      step="0.01"
                      value={row[colIndex] ?? 0}
                      onChange={(event) =>
                        setRows((current) => current.map((item, index) =>
                          index === rowIndex ? item.map((value, col) => (col === colIndex ? numberValue(event.target.value) : value)) : item,
                        ))
                      }
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function RangeEditor({ selectedIds, ranges, onRangeChange }: { selectedIds: string[]; ranges: Record<string, EvaluationRange>; onRangeChange: (id: string, range: EvaluationRange) => void }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>评价指标</th>
            <th>优</th>
            <th>良</th>
            <th>一般</th>
            <th>较差</th>
            <th>很差</th>
          </tr>
        </thead>
        <tbody>
          {selectedIds.map((id) => {
            const indicator = findIndicator(id);
            const range = ranges[id] ?? DEFAULT_RANGES[id];
            return (
              <tr key={id}>
                <th>{indicator.name}{indicator.unit ? ` (${indicator.unit})` : ""}</th>
                <td>{range.excellent.operator}<NumberCell value={range.excellent.value} onChange={(value) => onRangeChange(id, { ...range, excellent: { ...range.excellent, value } })} /></td>
                <td><RangeCells range={range.good} onChange={(next) => onRangeChange(id, { ...range, good: next })} /></td>
                <td><RangeCells range={range.average} onChange={(next) => onRangeChange(id, { ...range, average: next })} /></td>
                <td><RangeCells range={range.poor} onChange={(next) => onRangeChange(id, { ...range, poor: next })} /></td>
                <td>{range.verypoor.operator}<NumberCell value={range.verypoor.value} onChange={(value) => onRangeChange(id, { ...range, verypoor: { ...range.verypoor, value } })} /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function WeightPreview({ selectedIds, weights }: { selectedIds: string[]; weights: Record<string, number> }) {
  if (!Object.keys(weights).length) return null;
  return (
    <section className="weight-preview">
      <h3>当前权重预览</h3>
      <div className="preview-grid">
        {selectedIds.map((id) => {
          const indicator = findIndicator(id);
          const weight = weights[id] ?? 0;
          return (
            <div key={id}>
              <span>{indicator.name}</span>
              <strong>{(weight * 100).toFixed(2)}%</strong>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function RangeCells({ range, onChange }: { range: { min: number; max: number }; onChange: (range: { min: number; max: number }) => void }) {
  return (
    <span className="range-cell">
      <NumberCell value={range.min} onChange={(value) => onChange({ ...range, min: value })} />
      <span>~</span>
      <NumberCell value={range.max} onChange={(value) => onChange({ ...range, max: value })} />
    </span>
  );
}

function NumberCell({ value, onChange }: { value: number; onChange: (value: number) => void }) {
  return <input type="number" step="0.01" value={value} onChange={(event) => onChange(numberValue(event.target.value))} />;
}

function FooterActions({ disabled, onNext, nextLabel }: { disabled: boolean; onNext: () => void; nextLabel: string }) {
  return (
    <div className="footer-actions">
      <button type="button" className="primary" disabled={disabled} onClick={onNext}>{nextLabel}</button>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
