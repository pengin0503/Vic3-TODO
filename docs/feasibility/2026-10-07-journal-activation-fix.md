# Phase 0: Journalが表示されない不具合の調査と修正

## 対象と結論

調査開始時の最新main: `12c8312eea5065ddf3152d40b9c05272a5ef64ef`。
利用者は時間を進めても検証用Journalが表示されないと報告した。
添付`logs.zip`の最新`game.log`では検証用MODの3つのJournal定義を読み込んでいる。
MOD未読込ではなく、Journalのgroup未指定によりcountry contextが欠けていることが主原因と判断した。
表示回復そのものは修正後のゲーム内再検証が必要。

## 証拠

- `logs.zip` SHA-256: `26813dc9016c1050707d4cd5ed4b08f59411332ac7cc1190c310ab0a8578452e`。
- `logs/code_revisions.log:4`: game branchは`release/1.14.5`。
- `logs/game.log:33–38`（19:56:23）: `vic3_todo_probe`、`vic3_todo_slot_0_probe`、`vic3_todo_slot_1_probe`すべてでgroupがない旨とcontextless警告。
- `logs/game.log:39–41`: 3つのJournalの`_reason`ローカライズ欠落。
- `logs/game.log:70–76`: `is_building_type`の`building_furniture_manufacturies`、`building_textile_mills`をinvalid database objectとして報告。
- 変更前の`probe_src/common/journal_entries/vic3_todo_probe.txt`はgroupを指定せず、`is_shown_when_inactive`と`possible`で`is_player = yes`を使用していた。国scopeを必要とする条件がcontextlessで評価される構造だった。

一次資料`Vic3_todo_source.zip`（SHA-256: `645b43686ad86db50434bbc1fd1dedf97ed3606f48cad5f32de22b11f4e39d7e`）内、`Vic3_todo_source/game/`からの相対パス:

- `common/journal_entries/journal_entries.md:2–8,33–44`: groupがcontextを決め、表示条件・possible条件により自動起動する仕組み。
- `common/journal_entry_groups/00_journal_entries.txt:39–42`: Vanillaの国単位group例は`context = country`。
- `common/buildings/01_industry.txt:28–29,53–54`: 正式な定義IDは`building_textile_mill`、`building_furniture_manufactory`。旧複数形はaliasesに記載されているが、今回のゲーム実行ではtrigger参照が拒否された。

## 修正

1. MOD専用`vic3_todo_probe_group`を`context = country`で定義し、3つのJournalすべてに割り当てる。
2. 家具・繊維工場のtriggerを1.14.5の正式な定義IDへ変更する。
3. Journal説明文のキーを`_desc`からエンジンが要求した`_reason`へ変更する。主Journalの既定statusとgroup名も日英両方に追加する。
4. ビルド・インストール前のvalidatorが未定義/country context以外のJournal groupと欠落した日英Journal名・理由を拒否する。
5. ビルド時に実際の入力sourceの建物定義と`is_building_type`を照合し、存在しないIDなら出力を公開しない。

検証用groupは新規のnamespacedファイルのみ。Vanillaのgroup・GUIを置換しない。
元ZIPとVanilla原本は変更・コミットしない。ユーザーのログ原本もコミットしない。
添付ログ中の他MOD・Vanillaに関するエラーはこの修正の対象にしない。

## 検証

- 修正前の全42テストはPASS。従来の検証はgroup・Journal理由キー・建物参照の有効性を検出していなかった。
- 6つの新規回帰テストは修正前に期待した箇所でFAIL（groupテストは2 subtest）。
- 修正後: `python -m unittest discover -s tests -v`で48テストPASS。
- `python -m py_compile tools/*.py tests/*.py`、`git diff --check`はPASS。
- 添付ZIPとコミット済み派生evidenceを使ったビルドは14ファイルを生成。独立した2回のビルドでファイル名と全バイトが一致。
- ZIPのSHA-256は元の値と一致。
- Windows PowerShellとゲーム実行はこの環境では未検証。Journal表示・slot初期化・GUI表示についてruntime PASSを推定しない。
- 自由入力の永続化は依然未確認。Task 7の実現可否判定は今回行わない。

## 再導入と確認

Victoria 3を完全終了し、リポジトリ直下で実行:

```powershell
git pull --ff-only origin main
powershell -ExecutionPolicy Bypass -File .\tools\install_probe.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Victoria 3"
```

`git pull`だけではインストール済みMODは更新されない。installerを再実行する。
ランチャーで検証用MODが有効なplaysetを選び、まず検証用新規ゲームで日付を進める。
Journalの「Vic3 TODO Phase 0 検証」「Slot 0」「Slot 1」が表示されるか確認する。
続いて`docs/runtime-verification-phase0.md`に従う。
再び表示されなければ、修正後の実行で生成された`game.log`、`error.log`、`gui.log`とインストール済み`vic3_todo_build_manifest.json`を収集する。
