// 백엔드 응답과 1:1 매칭되는 도메인 타입.
// 백엔드 schema·라우터가 바뀌면 본 파일도 같은 커밋에서 업데이트.

export interface Line {
  id: number;
  name: string;
}

export interface Model {
  id: number;
  name: string;
}

export interface Equipment {
  id: number;
  name: string;
  ip: string;
  line_id: number;
  line_name: string;
  model_id: number;
  model_name: string;
  ftp_port: number | null;
  ftp_mode: string | null;
  encoding: string | null;
  note: string | null;
}

export interface RecipeListItem {
  id: number;
  equipment_id: number;
  equipment_name: string;
  line_name: string;
  model_name: string;
  path: string;
  film_name: string | null;
  body_hash: string;
  encoding_used: string | null;
  last_scanned_at: string;
  last_modified_at: string | null;
}

export interface RecipeDetail extends RecipeListItem {
  body_text: string;
  ini_text: string | null;
}

// compare 알고리즘 결과 — docs/COMPARE_ALGORITHM_SPEC.md와 1:1 동기화.
export type DiffKind = "added" | "removed" | "changed" | "moved" | "unchanged";
export type Severity = "info" | "minor" | "major" | "critical";

export interface Diff {
  kind: DiffKind;
  section: string | null;
  key: string | null;
  left_value: string | null;
  right_value: string | null;
  left_line: number | null;
  right_line: number | null;
  note: string | null;
  severity: Severity;
}

export interface ComparePair {
  left_recipe_id: number;
  right_recipe_id: number;
  same: boolean;
  similarity: number;
  diffs: Diff[];
  raw_diff: {
    unified: string;
    left_lines: string[];
    right_lines: string[];
    matcher_ops: Array<{
      tag: "equal" | "replace" | "delete" | "insert";
      left_start: number;
      left_end: number;
      right_start: number;
      right_end: number;
    }>;
  } | null;
}

export interface CompareSummary {
  total_pairs: number;
  pairs_identical: number;
  pairs_with_diffs: number;
  total_diffs: number;
  by_kind: Record<string, number>;
  by_severity: Record<string, number>;
}

export interface RecipeMeta {
  recipe_id: number;
  equipment_name: string;
  line_name: string;
  model_name: string;
  path: string;
  film_name: string;
  analysis2_text: string;
  strategy_ini_text: string;
}

// 1.1: N-way 가독성용 부가 산출물

export interface Cluster {
  id: string;
  recipe_ids: number[];
  representative_recipe_id: number;
  signature: string;
  body_hash_match: boolean;
  is_majority: boolean;
}

export interface ClusterPairDiff {
  left_cluster_id: string;
  right_cluster_id: string;
  diffs: Diff[];
}

export interface ClusteringResult {
  clusters: Cluster[];
  pair_diffs: ClusterPairDiff[];
}

export interface PivotBranch {
  value: string;
  recipe_ids: number[];
  is_majority: boolean;
}

export interface PivotEntry {
  section: string | null;
  key: string;
  branches: PivotBranch[];
  is_outlier_present: boolean;
}

export interface PivotResult {
  entries: PivotEntry[];
}

export interface CompareResult {
  schema_version: string;
  generated_at: string;
  inputs: RecipeMeta[];
  pairs: ComparePair[];
  summary: CompareSummary;
  warnings: string[];
  clusters: ClusteringResult | null;
  pivot: PivotResult | null;
}
