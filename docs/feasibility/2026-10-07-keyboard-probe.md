# キーから直接開くPhase 0検証画面

開始時の最新mainは`cb175eab08ebbb7cbc554fabd09dddb6ad13ed45`。
利用者は前回修正後もJournal非表示と報告し、キーから開く経路を要求した。
再実測ログは未提供のため、今回の非表示原因は断定しない。
Journal自動登録に依存せず入力・slot検証へ入れるHUD画面を追加する。
本番TODOシステム、自由入力の永続化、Task 7の実現可否判定は対象外。

## 操作と構成

- `Ctrl+Shift+T`または画面上部の`TODO検証 (Ctrl+Shift+T)`で開閉。
- 入力欄とslot情報・操作、「閉じる」「Journal一覧を開く」を配置。
- country scripted-GUI定義とExecute経路が実際の入力sourceで確認できた場合、開閉時に既存のoccupied-guard付きslot初期化を実行。開き直してもbaselineは再取得しない。
- `add_journal_entry`と`has_journal_entry`も確認できれば「検証用Journalを登録」を配置。未登録の3項目だけをプレイヤー国に追加する。
- scripted-GUI定義が不足するZIPだけでのビルドでも画面と入力欄は生成。未確認の操作callbackは生成しない。実際のゲームフォルダーでinstallerを実行して再判定する。
- 直接画面の表示成功を、Journal統合や入力文字列保存の成功として扱わない。

`tools/keyboard_probe.py`は入力sourceの`gui/ingame_hud.gui`と`gui/shortcuts.shortcuts`に限定して挿入する。
固定したVanilla GUIはリポジトリに保存しない。挿入箇所を除くと入力sourceと全バイトが一致することを検証する。
BOMとCRLFも維持。sourceにCtrl+Shift+Tの既存割り当てがあれば、上書きせずビルドを拒否する。
生成物はインストール先では同じVanillaパスを置換するため、同じファイルを変更するGUI MODとの併用は避ける。Journal GUI自体は置換しない。

MOD専用キー・操作・変数・ローカライズは`vic3_todo_`名前空間。
独立画面にはJournalEntry datacontextがないため、Journal用pin callbackを除き、数値・操作をプレイヤー国scopeに接続する。
Journal用と独立画面用のローカライズを分け、元のJournal表示も維持する。

`vic3_todo_keyboard_integration.json`にキー、元ファイルhash、挿入hash、初期化/登録の有無を記録。
installerは導入先と操作の有無を表示。MOD表示versionは`0.0.2`。
collectorは`game.log`とこのmetadataも収集し、`keyboard_open`、`keyboard_hud_button`、`keyboard_register`を個別記録する。

## 一次資料

添付ZIPの`Vic3_todo_source/game/`からの相対パス:

- `gui/shortcuts.shortcuts:1–7`: shortcutbindingsと修飾キー。
- `gui/ingame_hud.gui:111–115`: ゲーム内HUD root。
- `gui/company_panel.gui:544–555`: scrollarea、vertical_scrollbar、scrollwidget。
- `gui/information_panel_bar.gui:660–661,685`: Journal一覧を開く経路。
- `gui/journal_entry_widgets/ep2_japan_widgets.gui`: Country.MakeScope、script value、country-root scripted-GUI Execute。
- 他のGUIのGetPlayer、GetVariableSystem.Toggle/Exists/Clearから、同じCountry型の`GetPlayer.MakeScope`へ接続。これはAPIの組み合わせであり、キー経路全体のゲーム内成功は未検証。
- `common/journal_entries/00_player_objectives_hegemon.txt:242–245`、`common/buildings/03_mines.txt:29`: Journal追加と存在確認。

## 検証

新規回帰テストを先に実行し、生成物未作成、collectorの欠落結果、BOM付きsource拒否で失敗することを確認した。
修正後は全59テストPASS。Python compile、diff whitespace検査、添付ZIPでのビルドと再現性比較を実施。
HUD/shortcut接続、プレイヤー国bindings、原本バイト維持、BOM/CRLF、キー衝突拒否、改変検出、条件付きcallback、Journal重複防止構造、collectorを検証する。
これらはゲームエンジンの代替実行ではない。Windowsとゲーム内のキー入力・画面・操作は再確認が必要。

## 再導入と確認

Victoria 3を完全終了し、リポジトリ直下で実行:

```powershell
git pull --ff-only origin main
powershell -ExecutionPolicy Bypass -File .\tools\install_probe.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Victoria 3"
```

導入先を確認し、検証用MODが有効なplaysetでゲームを始める。
時間を進める前にCtrl+Shift+Tと上部のボタンをそれぞれ試す。
登録ボタンがある場合は検証用Journalを登録し、Journal一覧で3項目を確認する。
続いて`docs/runtime-verification-phase0.md`を実行する。

キーもボタンも使えない場合は、最新`game.log`、`gui.log`、`error.log`、導入先の`vic3_todo_keyboard_integration.json`と`vic3_todo_build_manifest.json`を収集する。
キーだけが効かない場合、またはJournal登録だけ失敗する場合は、その違いをNotesへ記録する。
