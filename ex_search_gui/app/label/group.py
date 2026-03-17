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

    # 1. セグメントの全体出現回数をカウント
    all_segments_in_corpus = []
    label_to_segments = {}  # 各ラベルがどのセグメントを持つか保持

    for label in labels:
        if segment_split_enabled:
            # 分割して空文字を除外
            segs = [s for s in re.split(segment_delimiters, label) if s]
            all_segments_in_corpus.extend(segs)
            label_to_segments[label] = segs
        else:
            label_to_segments[label] = []

    segment_counts = Counter(all_segments_in_corpus)

    # 2. 振り分け処理
    # 辞書の逆引き (キーワード -> グループ名)
    rev_category_map = {}
    if category_dict:
        for group_name, keywords in category_dict.items():
            for kw in keywords:
                rev_category_map[kw.lower()] = group_name

    for label in labels:
        # --- 機能 A: 辞書を元にグループを分ける (部分一致判定) ---
        if category_dict:
            for kw, target_group in rev_category_map.items():
                if kw in label.lower():
                    if auto_create_new_groups or target_group in result_groups:
                        result_groups[target_group].add(label)

        # --- 機能 B: セグメント分割でグループを作成 ---
        if segment_split_enabled:
            segs = label_to_segments.get(label, [])
            for seg in segs:
                # 全ラベルの中での出現回数が閾値以上かチェック
                if segment_counts[seg] >= min_segment_match:
                    if auto_create_new_groups or seg in result_groups:
                        result_groups[seg].add(label)

    # 整形して返却
    output = {"groups": {k: sorted(list(v)) for k, v in result_groups.items() if v}}
    return output
