# Phase 0 ゲーム内実測手順（Task 6まで。Task 7未実行）

2026-10-07の初回実測でJournalのgroup未登録、旧建物ID、説明文キー欠落が見つかり、修正しました。[原因と検証記録](feasibility/2026-10-07-journal-activation-fix.md)。旧版を導入済みの場合は、下記の`git pull`に続けてinstallerも再実行してください。リポジトリの更新だけではインストール済みMODは変わりません。再確認はまず検証用新規ゲームで行ってください。

## 準備

Python 3.10以上を使用してください。Victoria 3を完全終了し、このリポジトリの最新mainを取得して、リポジトリ直下で実行します。

```powershell
git pull --ff-only origin main
python --version
powershell -ExecutionPolicy Bypass -File .\tools\install_probe.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Victoria 3"
```

ZIPそのものをPC上でも再監査する場合は次を使用します。最初の入力には保存したZIPの絶対パスを指定します。

```powershell
$SourceArchive = Read-Host "Vic3_todo_source.zip の絶対パス"
powershell -ExecutionPolicy Bypass -File .\tools\install_probe.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Victoria 3" -SourceArchive $SourceArchive
```

インストール先はWindowsの実際のDocumentsフォルダー配下の `Paradox Interactive\Victoria 3\mod\Vic3TODOProbe` です。OneDriveなどに移動したDocumentsもWindowsの設定から取得します。個別指定は `-UserDataDir "...\Paradox Interactive\Victoria 3"`。

installerはZIPを指定した場合にZIPを先に監査し、続いてinstalled treeを監査します。ZIPを指定しない場合はコミット済みのZIP由来証拠を比較元にします。`research/generated/source-comparison.json` に重複hash差、API差、片方だけのファイルを記録します。ゲームに読み込ませるprobeは実際のinstalled treeを入力にビルドするため、その選択もbuild manifestに残ります。原本ZIP/vanillaファイルはコピー・変更しません。

`common/scripted_guis` のcountry-scope/effect定義が確認できる場合だけselector操作を生成します。生成後の `vic3_todo_slot_capabilities.json` の `selector_ui` を確認してください。生成されない場合はselector UIをNOT_TESTEDとし、Script ExplorerでMOD専用effectをplayer countryへ実行する手動補助検証に限定します。手動実行をGUI selectorのPASSにしないでください。

ランチャーで新しい検証用playsetを作り、`Vic3 TODO Phase 0 Probe`を有効化してください。ゲーム画面の実際のバージョンが1.14.xであることを確認・記録します。GUI MODを併用せず、通常の新規ゲームまたは検証用セーブを使用します。Ironmanを避け、必要なScript Explorer調査時だけランチャーの起動引数へ `-debug_mode` を追加します。

## 最初の起動で行う検証

ゲームを開始して一度時間を進め、Journalに以下が出ることを確認します。

- `Vic3 TODO Phase 0 検証`：1個のUnicode入力欄、slotデータ表示、利用可能なselector controls、標準pin操作。
- `Slot 0` と `Slot 1`：独立した数値/config保存、各進捗バー、dynamic status。

### A. 日本語・free-text

`日本で家具工場を10レベル建てる` を入力します。ASCII、スペース、数字、`！?「」`、200文字付近、空欄、改行も別々に確認してください。

このprobeの入力欄には任意文字列をsaveへ渡す確認済みcallbackが**ありません**。入力できたことと保存できたことを分けて記録してください。下にある固定日本語サンプルの表示を、ユーザー入力の保存成功と誤認しないでください。

Journalを閉じて開く、別パネルへ移動して戻る、セーブ→メニュー→loadの順に、入力した文字列そのものが復元するか確認します。復元できない場合は該当項目をFAIL、操作できない場合はNOT_TESTEDです。session-only保持は永続化のPASSになりません。

### B–D. 2 slot・selector・baseline

1. 現在の国内家具工場レベル合計を数えてください。金融上の所有権・外国投資と国内建物のscopeは別問題です。各slotの `current`、`baseline_display`、`goal_display`、`target_display`、`mode_display`、`capture_count_display`、`completed_display`、`label_display` を記録します。初回capture countは1が期待値で、ゲームで実際に確認します。
2. slot 0だけ`complete`→`reopen`を実行し、slot 1のcompletionが変わらないことを確認します。
3. slot 0だけ`cosmetic edit`を実行し、label IDだけが変わり、baseline・capture countが変わらないことを確認します。これは固定ラベルの変更経路であり、free-text編集の証明ではありません。
4. 通常のゲーム操作で家具工場を1レベル完成させてください。currentが増え、deltaが1増え、baselineが変わらないことを確認します。建設中のentity数をレベル数に含めないでください。通常の取り壊しで1レベル減らし、net progressが戻ることも確認します。
5. slot 0だけ`select textile`、`select absolute`、`goal 5`を順に実行します。それぞれの変更確定時にcapture countが1だけ増えることを確認します。同じ操作を繰り返すと増えないこと、slot 1に影響しないことも確認します。`select furniture`、`select delta`、`goal 10`で戻せます。
6. `select technology`を選択し、Telephoneのresearch状態と0/1表示を照合します。research済み・未researchの両方を可能な範囲で確認し、研究の途中を架空の割合として表示していないことを確認します。未検証の側はNOT_TESTEDと記録します。
7. Relationsが生成されていれば、プレイヤーにGBR/FRA以外の国を選び、`select GBR`と`select FRA`で対象とcurrentを切り替え、外交画面の値と照合します。自国/存在しない対象ではprogress=0・未達成・対象参照不可になることを確認します。probe自体は外交状態を変更しません。
8. セーブ→load、Journal reopen後にbaseline・capture count・target・mode・goal・completion・label IDが維持されることを確認します。reopen/load時に再captureされる場合はFAILです。

Script Explorer補助用effect名は `vic3_todo_slot_0_cosmetic_edit`、`vic3_todo_slot_0_select_furniture`など、GUI controlsと同名です。slot 1は`_slot_1_`。Explorerでplayer countryをrootとして確認済みのscripted effectを実行します。使えない場合はNOT_TESTEDとし、未確認のconsole commandは使いません。

### E. Journal・progress・status・pin

進捗バーは最大100で、numeric ratioまたはTechnologyの0/100のみです。更新は週次です。日付を進めて週次pulseを跨ぎ、currentから得られる値とbarが一致することを確認します。設定変更直後にbarが旧値でも、次の週次更新と区別して記録してください。

達成前/条件達成/手動完了/対象無効に応じてdynamic statusを確認します。Journalの標準pinボタンとprobe内toggleを操作してOutlinerを確認してください。slot JEのpinも個別に確認します。保存後のpin保持は別項目です。

## 必須の完全終了→再起動

最初の起動でA–Eの大部分をまとめて検証できます。ただしfull restart/loadの証明には必ず二度目の起動が必要です。

セーブしてVictoria 3を終了し、プロセスが消えたことを確認します。

```powershell
Get-Process -Name victoria3 -ErrorAction SilentlyContinue
```

何も表示されない状態から通常どおり再起動し、同じセーブをloadしてください。入力した日本語文字列、両slotのbaseline/config/completion、pinを照合します。入力欄の文字列が失われたら `full_restart_text=FAIL`。原本ローカライズの再表示はPASSになりません。

## 結果の収集

確認後、リポジトリ直下で実行します。

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\collect_phase0_results.ps1
```

各項目に `PASS` / `FAIL` / `NOT_TESTED` を入力します。空欄はNOT_TESTEDです。国・開始日・変更前後のbaseline/current/goal・capture countと失敗の再現手順をNotesへ記入してください。ログがないことだけを理由にclean=PASSにしないでください。

`research/runtime/vic3_todo_phase0_<UTC>.zip` に手入力の結果、`error.log` / `gui.log` の末尾300行、利用可能な派生evidenceとbuild manifestをまとめます。セーブファイルやvanilla原本は収集しません。このZIPを次の確認へ渡してください。collectorはTask 7の決定を行いません。

PowerShell wrappersはこのLinux実行環境では実行していません。Pythonの監査・ビルド・publish/rollback・collectorはoffline testsで検証しています。ゲーム内結果はすべて未実測です。
