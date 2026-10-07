# 軽量化解析の流用：文字列保存APIの調査

日付: 2026-10-07（日本時間）  
TODO調査基準: `210667802d5d6fc0142cd94355a0a048ffacb3f6`  
流用元: `pengin0503/Vic3-optimazation` / `c13bb2730a38a130186e1edb389f9ed8e1f54eef`  
状態: **静的な調査経路を具体化。実際のruntime型一覧と保存経路は未確認。**

## 結論

流用元の保存資料には、型・関数一覧の出力UIと、変数を文字入力から編集するGUIがある。これらはTODOの未解決点を調べるための一次資料として使える。ただし、変数編集画面の存在は「通常のMOD GUIから任意Unicodeを国のsave stateへ保存できる」ことの証明ではない。

特に、`VariableStore` → `VariableEntry` → `ScopeObjectEditor` という編集経路を確認できた。一方、プレイヤー国の保存用storeを取得するpromote、任意テキストを格納できる型、その型のsave/load契約が不足している。未確認の式をprobeへ追加しない。

次の入力は、ユーザーが実際に起動する1.14.5の型・関数一覧とscript documentation。[取得手順](../runtime-api-evidence.md)を用意した。新しいdumpがない間も候補は残すが、free-textのcapabilityは`candidate`のままにする。`PURE_MOD_VIABLE` / `PURE_MOD_BLOCKED`のどちらも今回決定しない。

## 情報源と同一性

最優先の資料は添付`Vic3_todo_source.zip`。SHA256は`645b43686ad86db50434bbc1fd1dedf97ed3606f48cad5f32de22b11f4e39d7e`で、調査前後に変更していない。

補助資料は流用元の[input-data/pc-evidence-2026-10-05](https://github.com/pengin0503/Vic3-optimazation/tree/c13bb2730a38a130186e1edb389f9ed8e1f54eef/input-data/pc-evidence-2026-10-05)。以下5アーカイブを読み取り、[保存index](https://github.com/pengin0503/Vic3-optimazation/blob/c13bb2730a38a130186e1edb389f9ed8e1f54eef/research/generated/pc-evidence-2026-10-05/preservation-index.json)のサイズ・SHA256と一致し、CRC検査も通過した。

| 補助資料 | bytes | 用途 |
|---|---:|---|
| `installed-game-gui.zip` | 901540 | 添付GUIとの比較。重複205ファイルがすべてバイト一致 |
| `installed-clausewitz.zip` | 311873 | 型一覧出力UI |
| `installed-jomini.zip` | 454834 | 変数editor、script/GUI profiler |
| `installed-game-tools.zip` | 552607 | Scripted Testsの仕様とJournal判定例 |
| `installed-root-controls.zip` | 16433 | 保存時点のビルド識別子 |

保存ビルドはCaligula `release/1.14.5` / `9f8281a37e85639359b3b0c2c5df0196e975ca4b`、Clausewitz `caligula/release/1.14.x` / `fd5e1dbd038c3c4a3f48a36abf60ebb42dd0ceef`。これは資料の識別であり、ユーザーが次回起動するexeの同一性は別途記録する。

元ZIP・展開GUI・exeはTODOリポジトリへコピーしない。[派生証拠](../../research/generated/optimization-api-reuse.json)にはハッシュ、位置、確認範囲を残す。既存の`phase0-api-evidence.json`やbuilderの判定は変更しない。

## 文字列保存に関する具体的な候補

以下の位置は各補助アーカイブ内のファイル。引用する識別子は実ファイルで確認したものだが、APIのsignature・利用可能context・save契約はGUI使用例だけから復元しない。

| ファイルと行 | 確認できたもの | まだ証明していないもの |
|---|---|---|
| `clausewitz/gui/applicationutils/datatypes_explorer.gui:14–16` | `Dump datatypes`ボタンが`DatatypesExplorer.DumpDataTypes`を呼ぶ | retailでの入口、console alias、出力先と形式 |
| `jomini/gui/object_explorer/common_inspector.gui:14–16` | `ScopeObjectEditor.AsString` / `SetFromString`。入力欄はNumberまたはFlagで表示 | 任意Unicode string型、保存・復元、200文字・空白・空入力の対応 |
| 同ファイル`:243–256,273–345` | `VariableStore.AccessVariables` → `VariableEntry.AccessScopeEditor`、新規entry編集・追加 | `Country`/`Scope`から保存用storeを取得できるpromote、固定slotへ安全に書く経路 |
| `jomini/gui/object_explorer/variable_inspector.gui:15,63,97–109` | inspectorが変数editorと新規変数追加を利用 | inspector pluginを通常のMOD GUIで構築・取得できること |
| `jomini/gui/object_explorer/script_runner_inspector.gui:94–100` | storeの実際のcontext例は`ScriptRunnerInspector.AccessEventTargets.AccessVariables` | この実例が国の永続変数storeであること。script runner用scope準備とsave stateを混同しない |

`AsString`は文字列への表示変換を意味し得る。`SetFromString`は数値・flagなどへの解析を意味し得る。これらの名前だけでは文字列型やserializationは確定しない。Flagに任意Unicodeを入れられるかも未確認であり、対応とも非対応とも断定しない。

また、engineが作るeditor contextと、modから取得できるcontextは別物。ゲームオブジェクト名を保存場所に流用せず、debug editor自体を製品UIへ埋め込まない。`Country.GetVariableStore`のような未確認のAPI名を作らない。

## 実装前に満たす接続条件

1. 通常のTODO GUIで入力文字列を受け取るcallbackの正確なsignatureとtext引数を確認する。
2. `GetPlayer`/`Country`/`Scope`から、当該国のMOD専用変数へ到達する公開promoteを確認する。editorだけの一時storeは不可。
3. 値の型・文字コード・長さ制限・空入力の扱いを確認する。名前や`ToString`相当の表示だけで判定しない。
4. 同じMOD専用slotへ設定・読出しでき、他国や他のslot、baselineを変更しないことを確認する。
5. `日本で家具工場を10レベル建てる`、ASCII、空白・記号、200 Unicode文字付近、空入力をUI再生成・save/load・プロセス完全終了後に同じ値として復元する。
6. debug専用のAPIが候補なら、通常起動でも利用可能かを別に検証する。

接続条件1–4が資料で揃った時点で、最小の文字列保存probeを設計・レビューする。5–6はruntime確認が必要。今回は新しいcallbackやnative fallbackを実装しない。

## 他に流用できるもの

- **Scripted Tests:** `game/tools/scripted_tests/scripted_tests.md`は日次success/fail、success優先、終了日、出力先を説明する。`ip3.txt:13–21`には特定国の`has_journal_entry`を判定する実例がある。将来、Journal登録やslot状態の検証に使える。画面表示・入力操作・再起動後の文字列復元をこれだけでPASSにしない。正常条件と失敗条件が同時に成立するテストは避ける。
- **Script/GUI profiler:** `ScriptProfilerGui.StartCapture/StopCapture`と`GuiDataProfiler.BeginRecording`が実GUIにある。TODOの建物合計・progress/status・画面開閉の比較に使える。probe負荷や32×4への拡大時の費用は未測定。雇用lookup向けのnative hintやアドレスをTODOへ転用しない。
- **Journal cadence:** [performance-controlsの派生記録](https://github.com/pengin0503/Vic3-optimazation/blob/c13bb2730a38a130186e1edb389f9ed8e1f54eef/research/generated/pc-evidence-2026-10-05/performance-controls.json)はactive=4日、inactive=14日を記録する。これらは保存時点の既定値で、他MODによる変更・初期評価の時刻は別問題。現在のprobeの週次bar更新とも区別する。非表示原因の確定証拠にはしないし、global definesを変更しない。

## 制約と次の引継ぎ

保存済みGUIはAPIを呼ぶ使用例であって、runtimeが出力した型一覧ではない。取得済みの元アーカイブ目録・ログ目録にも実際の型一覧は確認できなかった。全exe APIの網羅的な不存在証明ではない。

`installed-game-common.zip`は保存されているが、今回のGitHubテキスト取得経路では内容を読めなかった。この未読資料に対し、common全体のcoverageやscripted-GUI定義の不存在を宣言しない。Webの第三者による別versionの型一覧は現行1.14.5のAPI証拠へ昇格させない。

この環境ではVictoria 3を起動できず、型一覧の出力UI・callback・ゲーム内表示を実行していない。次回は[runtime取得手順](../runtime-api-evidence.md)で取得した型一覧とscript documentationを添付する。Journal非表示については最新probe導入後の`game.log/error.log/gui.log`とbuild/keyboard metadataを別途使う。旧軽量化ログで現在のTODO不具合を断定しない。

## 今回の検証

- `python -m unittest discover -s tests -q`: 59 tests / OK。既存probeのoffline testsであり、新しいengine APIのruntime試験ではない。
- 保存indexに対する5アーカイブのサイズ・SHA256・CRC、8使用例ファイルのSHA256・行数・各API識別子の行位置を独立に再照合した。
- 添付GUIと補助GUIの重複205件はバイト一致。添付ZIPのSHA256は変更していない。
- `git diff --check`、文書の相対リンク・コードフェンス・派生JSONのcandidate/runtime判定を確認した。
- PowerShellの取得例、ゲーム内dump、文字入力、save/load、通常モードでのAPI使用は未実行。製品コード、生成MOD、global defines、Phase 0判定は変更していない。
