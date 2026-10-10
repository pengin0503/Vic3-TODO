# Vic3 TODO — カスタムジャーナル

Victoria 3（1.14.5）で、ゲーム内のジャーナルと同じように **自分でジャーナルを作れる** MODです。

- 自由入力のタイトルと説明（日本語可、最大4行×50文字）
- 実際のゲーム状態から自動計算される進捗条件を、1件につき最大4つ（33種類）：建物のレベル、GDP、人口、識字率、陸海軍、技術、法律、他国との関係、国家ランク、威信、生活水準、悪名、国庫・負債、商品の生産量と価格、利益集団の支持と影響力、急進派・支持派、権威・官僚、平和、経過日数 など
- 「作成時から増加」（作成前からある分は数えない）／「目標値以上」／「作成時から減少」／「目標値以下」
- すべて満たす／どれか1つ、自動完了、手動完了・再開、期限（期限切れ表示、または任意で失敗扱い）
- 作成したジャーナルは、ゲームのジャーナル画面の「カスタムジャーナル」グループに本物のJournal Entryとして表示される。ピン留め、アウトライナー表示、完了・失敗の通知はバニラと同じように動く
- バニラのファイルは置き換えない

**ゲーム内での動作はまだ確認していません。** 開発環境ではゲームを起動できないため、静的検査とテストで確認した段階です。[ゲーム内確認手順](docs/runtime-checklist.md)で試し、結果を共有してください。

## インストール

Victoria 3を完全に終了し、リポジトリ直下で実行します（Python 3.10以上）。

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\tools\install_mod.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Victoria 3"
```

`Documents\Paradox Interactive\Victoria 3\mod\Vic3TODO` に入ります。ランチャーのプレイセットで「Vic3 TODO - Custom Journals」を有効にしてください。以前の **「Vic3 TODO Phase 0 Probe」は無効にしてください**（HUDのファイルを置き換えるため）。

`-GameDir` は任意です。付けると、建物・技術・法律の一覧をインストール済みのゲームから作り直します。

## 使い方

1. サイドバー（Map Listの下）のボタンで「カスタムジャーナル」ウィンドウを開く
2. 「＋ 新しいジャーナル」を押すと、ゲームの「名前の変更」入力欄が開く。タイトルを入力して確定する
3. 編集画面で、説明行の追加、自動完了・達成ルール・期限の設定、条件の追加を行う
4. ジャーナル画面にも同じジャーナルが表示される。完了・ピン留めはどちらからでも操作できる

### 入力の仕組みについて

1.14では、MOD独自の入力欄の文字列をスクリプトに渡す方法がありません。そのため、ゲーム標準の「会社名の変更」入力欄を借りています。入力の間だけ入力用の一時的な会社が作られ、確定またはキャンセルですぐに消えます。このとき、会社数の上限に関する通知が一瞬出ることがあります。文字列はジャーナル側の変数に保存され、会社名として残ることはありません。詳しくは[設計と根拠](docs/design/custom-journals.md)を参照してください。

## 開発

```bash
python tools/build_catalog.py --source /path/to/Vic3_todo_source.zip --parsed-vanilla /path/to/vanilla_parsed   # data/vic3_catalog.json
python tools/generate_mod.py          # 生成ファイルを更新（--check で鮮度確認）
python tools/lint_mod.py              # 静的検査
python -m unittest discover -s tests
```

- `mod/Vic3TODO/` — MOD本体。ファイル名に `generated` を含むものは `tools/generate_mod.py` の出力なので、直接編集しない
- `tools/templates/vic3_todo_window.gui.in` — ウィンドウのGUIテンプレート（マクロを展開して出力）
- `tools/templates/loc_strings.py` — 画面の文言（日本語・英語を1つの表で管理）
- `data/vic3_catalog.json` — 対象一覧。番号 `idx` はセーブに保存されるため固定で、再生成しても変わらない

## 以前のPhase 0 probe

`probe_src/`、`tools/*probe*`、`docs/feasibility/` は、実現可能性を調べるための検証用probeの記録です。本体MODとは別物で、インストールは不要です。
