# Vic3 TODO — カスタムジャーナルの設計と根拠

対象: Victoria 3 1.14.5。MOD本体: `mod/Vic3TODO`。

## 目的

ゲーム内のJournal Entryと同じように、プレイヤーがどんな状況のジャーナルでも自分で作れるようにする。

- 自由入力のタイトルと説明（最大4行×50文字＝200文字、日本語可）
- 実際のゲーム状態から自動計算される条件（1件につき最大4つ、40種類）。条件ごとに進捗条件か失敗条件かを選べる
- 達成ルール（すべて／どれか1つ）、自動完了、手動完了・再開
- 期限（超過で「期限切れ」表示、または任意で「失敗」）
- バニラのJournalへの統合：専用グループ「カスタムジャーナル」に本物のJournal Entryとして表示される。ピン留め、アウトライナー、完了・失敗の通知はバニラのまま動く
- 進行中／完了・失敗の分離表示と、確認付きの一括削除

## 画面

| 場所 | 内容 |
|---|---|
| サイドバー（Map Listの下）のボタン | 専用ウィンドウの開閉。進行中の件数を表示 |
| 専用ウィンドウ | 一覧、作成、編集（本文・機能・条件）、削除。scripted widgetで追加するため、バニラのGUIファイルは置き換えない |
| ジャーナル画面「カスタムジャーナル」グループ | 1件につき1つのJournal Entry。本文・状態・条件の進捗バー、完了ボタン、「編集画面で開く」ボタン |

## 自由入力：会社名変更ポップアップを入力欄として使う

1.14では、MOD自身のeditboxに入力した文字列をスクリプトへ渡せない。`PdxGuiEditboxGetText` は `CUTF8String` を返し、`MakeScopeFlag`・変数システム・文字列関数が受け付ける `CString` へ変換する手段がないため。これは別MODの1.14.5実機試験で確認されている（[Vic3TimelineExtended PR #745](https://github.com/jakeOmega/Vic3TimelineExtended/pull/745)、同リポジトリの `docs/guides/gui_modding_guide.md` §"Typed text into script"）。試験では `MakeScopeFlag`、`Concatenate` など各種文字列関数、`GetVariableSystem.Set`、`ontextedited` へのSet渡しのすべてが失敗している。

同じ試験で動作が確認された経路は、バニラの「会社名の変更」ポップアップだけだった。ポップアップは入力された名前を会社に保存し、`Company.GetNameNoFormatting` はそれを `CString` で返す。そこで次の流れにした。

1. 「新しいジャーナル」を押すと、入力用の一時的な会社 `company_vic3_todo_carrier` と、その会社の枠1つ分のmodifierを追加する
2. ウィンドウの入力バナーが表示された時点で、会社の元の名前を記録してから名前変更ポップアップを開く（会社を作るのと同じクリックの中ではポップアップを開けないため）
3. 1×1のwatcherが、名前が元と変わった瞬間に `MakeScopeFlag(会社名)` をscripted GUIへ渡す。自動で拾われなかった場合のために「この文字で確定」ボタンも用意した
4. 文字列はジャーナル側のflag変数 `vic3_todo_line1..4` に保存し、会社とmodifierはすぐに削除する

**文字列を保存しているのは会社名ではない。** 会社は入力の数秒間だけ使う入力欄で、保存先はジャーナル（script container）のflag変数。flag変数はセーブに `flag="…"` として書かれ、ロード後も残ることが前述の試験で確認されている。

代償として、入力の開始時と終了時に会社数上限の通知が一瞬出ることがある（modifierが反映されるのは次のmodifier更新時のため）。会社には建設されない専用の建物タイプだけを持たせ、AIは使わない。入力を開いたまま30日たつと、月次処理で自動的に片付ける。

1行の上限50文字は、バニラのポップアップの `maxcharacters = 50` による。行の追加で最大4行まで入力できる。

## データ構造

すべてプレイヤー国にぶら下がる。国が消えるとscript containerもエンジンが片付ける（`parent`）。

```
country
├─ list vic3_todo_items          ジャーナル（script container, tag vic3_todo）
├─ list vic3_todo_slot_<n>       スロットnのジャーナル（0〜1件）。JEのwidgetがdatamodelで読む
├─ vic3_todo_slot_used_<n>       スロット使用中フラグ（JEのinvalid条件）
├─ vic3_todo_title_<n>           スロットnのタイトルのコピー（JE名が読む）
├─ vic3_todo_edit / _edit_tr     編集中のジャーナル／条件
└─ vic3_todo_in_*                入力中の状態（会社、モード、元の名前、開始日）

journal (container)
├─ tags: vic3_todo, vic3_todo_auto, vic3_todo_any, vic3_todo_deadline_on,
│        vic3_todo_fail_on_deadline, vic3_todo_fail_suppressed, vic3_todo_done,
│        vic3_todo_failed, vic3_todo_editing
├─ vic3_todo_line1..4 (flag), vic3_todo_lines, vic3_todo_id, vic3_todo_slot
├─ vic3_todo_deadline (game_dateの日数), vic3_todo_created, vic3_todo_finished
└─ list vic3_todo_trackers

tracker (container, tag vic3_todo_tracker)
├─ tag vic3_todo_tr_fail（失敗条件）, vic3_todo_tr_editing
└─ vic3_todo_kind, _mode, _goal, _baseline, _captures, _target_idx, _target, _target_cap
```

最大32件はJournal Entryのスロット数（`je_vic3_todo_0`〜`31`）による。条件は1件4つまで。

### 対象の番号

建物・技術・法律・商品・利益集団は、`data/vic3_catalog.json` の固定番号 `idx` で保存する。カタログを再生成しても既存キーの番号は変えず、新しいキーは末尾に追加し、消えたキーは `removed` として番号を欠番にする。ゲームを更新しても、既存セーブの条件が別の対象を指すことはない。

## 条件（トラッカー）

| 値の型 | 種類 |
|---|---|
| 数値（4モード：作成時から増加／目標値以上／作成時から減少／目標値以下） | 建物のレベル、GDP、人口、識字率、陸軍、海軍、他国との関係、威信、平均生活水準、悪名、研究済み技術数、州の数、週収入、正統性、金準備、負債、負債の上限比、投資プール、総貿易額、市場の商品生産量、商品価格の基準比、都市化率、急進派、支持派、利益集団の支持、利益集団の影響力、権威、官僚、自国の州（人口、平均生活水準、識字率、急進派、騒乱、インフラ） |
| はい／いいえ | 技術の研究、法律の制定、平和である、特定の国と戦争中 |
| 序列 | 国家ランク（選んだランク以上） |
| 時間 | 経過日数（作成時から） |

- 条件には「進捗条件」と「失敗条件」の2つの役割がある。進捗条件は達成ルール（すべて／どれか1つ）に数える。失敗条件は、満たされた時点でジャーナルを「失敗」にする（バニラJEの `fail` と同じ）。失敗した状態で失敗条件が満たされたまま再開した場合は、その条件が一度解消されるまで再び失敗にはしない
- 基準値（作成時の値）は、作成時と、種類・対象・モードの変更時に1回だけ取る。ウィンドウの開閉、セーブ／ロード、目標値の変更では取り直さない。手動の「基準値を取り直す」もある
- 進捗は基準値からの純変化で、0〜目標値に収める。建物を取り壊すと進捗は減る
- はい／いいえと序列の条件は、0%か100%だけを表示する。研究の途中経過のような架空の割合は出さない
- 対象が未選択、または無効（関係の相手国が消滅したなど）の条件は、未達成のまま「対象が未選択か無効です」と表示する。自動では完了も削除もしない
- 数値はGUIが表示中だけscript valueで計算する。自動完了と期限失敗の判定は、各ジャーナルのJEの週次パルス、月次のon_action、ウィンドウを開いた時点で行う

各値がバニラのscript valueとして読めることは、バニラ（添付ZIP）とVic3TimelineExtendedの使用例で確認した（例: `owner.country_has_building_type_levels(scope:x.var:y)` は `common/script_values/negotiation_values.txt`、`market.mg:<goods>.market_goods_pricier` はTEの市場値、`ig_approval`・`ig_clout`・`gold_reserves`・`radical_fraction` などはバニラのscript values）。

## 互換性

- バニラのファイルは1つも置き換えない。すべて新規の `vic3_todo` 接頭辞付きファイル（scripted widgets、JE、scripted GUI、script values、on_actionへの追加）
- `on_monthly_pulse_country` には `on_actions` リストで追加するだけ（複数MODで併用できる形式）
- ウィンドウの開閉キーはCommunity Mod Frameworkと同じ `com_open_window` を使うため、CMFのパネルと互いに閉じ合う
- シミュレーションに触れるのは、入力中だけの一時的な会社とその枠modifierのみ

## 未検証の点（ゲーム内で確認が必要）

この環境ではゲームを起動できないため、以下は静的な根拠に基づく。[ゲーム内確認手順](../runtime-checklist.md)で確認する。

1. 会社名ポップアップによる入力の一連の流れ（TEの試験では会社経由の取り込みと、別の運び手でのwatcherは動作済み。両者の組み合わせは未試験）
2. 日本語の名前を会社名として受け付け、flagとしてセーブ・ロードできること（TEの試験は英語のみ）
3. JE名 `[JournalEntry.GetCountry.MakeScope.Var('vic3_todo_title_N').GetFlagName]` が、ジャーナル一覧・アウトライナー・完了通知で表示されること。表示されない場合でも、本文はJEのwidgetに表示される
4. `GetPlayerJournalEntry` によるウィンドウからのピン留め
5. 新しい値リンク（`techs_researched`、`scaled_debt`、`market_goods_pricier` など）が、すべてのスコープでエラーなく読めること
