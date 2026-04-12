import re
from collections import defaultdict, Counter


def organize_labels(
    labels: list[str],
    groups_init: dict[str, list[str]] = None,
    category_dict: dict[str, list[str]] = None,
    auto_create_new_groups: bool = True,
    segment_split_enabled: bool = True,
    segment_delimiters: str = r"[_-]",
    min_segment_match: int = 1,
):
    result_groups = defaultdict(set)
    if groups_init:
        for k, v in groups_init.items():
            result_groups[k].update(v)

    # --- 1. 候補となるグループ名の抽出 ---
    potential_group_names = set(result_groups.keys())

    label_to_segments = {}
    if segment_split_enabled:
        all_segments = []
        for label in labels:
            segs = [s for s in re.split(segment_delimiters, label) if s]
            all_segments.extend(segs)
            label_to_segments[label] = segs

        # 出現回数が閾値以上のセグメントをグループ名候補に追加
        segment_counts = Counter(all_segments)
        for seg, count in segment_counts.items():
            if count >= min_segment_match:
                potential_group_names.add(seg)

    # --- 2. 振り分け処理 ---
    for label in labels:
        label_lower = label.lower()

        # 機能 A: category_dict に基づく部分一致
        if category_dict:
            for group_name, keywords in category_dict.items():
                for kw in keywords:
                    if kw.lower() in label_lower:
                        result_groups[group_name].add(label)
                        break  # このグループへの振り分けが確定したため、このグループの他のキーワードは確認不要

        # 機能 B: セグメントに由来するグループ名が含まれているか判定
        # ここを「完全一致」から「部分一致」のニュアンスに変更
        for group_candidate in potential_group_names:
            # ラベルの中にグループ名候補が含まれているかチェック
            # (例: group_candidateが"user"なら、"new_user_data"というラベルもヒットする)
            if group_candidate.lower() in label_lower:
                if auto_create_new_groups or group_candidate in result_groups:
                    result_groups[group_candidate].add(label)

    # 整形して返却
    output = {"groups": {k: sorted(list(v)) for k, v in result_groups.items() if v}}
    return output
