# society_neta_example.ak — 台本 (SCRIPT / raw material) atoms for studio_ai / mail_show（✉️ show）
#
# ここには「事実・素材」だけを置く（何が起きたか）。解釈=演出は別ファイル
# society_neta_example.csl 側で curation.new として台本にかける（演出=解釈=curationの構造）。
#
# 台本 atom   neta:<gid>:<space>:<id>   … 役者(caster)に渡す事実。curation の path になる。
# ここでは set にも入れておく（演出 curation が ids= で参照するための素材プール）。

def "neta:studio_ai:mail_show:001" "あるチームが7Bのオープンウェイトモデルを公開。前世代の70B級に迫るベンチマーク、商用可ライセンス、重みは完全公開でダウンロード可能。"
def "neta:studio_ai:mail_show:002" "大手クラウド事業者がAI推論用の自社チップを発表。外部GPUへの依存を下げる狙いで、量産は来年後半の見込み。"
def "neta:studio_ai:mail_show:003" "研究者らがコードエージェント同士を競わせるベンチマークを公開。上位モデルでもタスク完遂率は6割止まりだった。"

set.add name="neta:studio_ai:mail_show:src" id="neta:studio_ai:mail_show:001"
set.add name="neta:studio_ai:mail_show:src" id="neta:studio_ai:mail_show:002"
set.add name="neta:studio_ai:mail_show:src" id="neta:studio_ai:mail_show:003"
