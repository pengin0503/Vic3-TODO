# Vic3-TODO

Victoria 3 1.14.x向けTODO MODのPhase 0 feasibility probeです。Task 1–6のoffline成果を用意しました。**ゲーム内実測は未実施、Task 7は未実行です。** Productionの32 TODO × 4 trackerは実装していません。

任意Unicode free-textをsaveへ渡すMOD専用経路はcandidateで、入力probeに保存callbackはありません。日本語の固定表示やsession-only保持を永続化成功として扱いません。pure-mod viabilityの判断はruntime evidence後に行います。

## 実測を始める

`Ctrl+Shift+T`または画面上部の`TODO検証`ボタンで直接検証画面を開ける経路を追加しました（version 0.0.2）。Journalの自動表示を待つ必要はありません。[操作と実装記録](docs/feasibility/2026-10-07-keyboard-probe.md)。旧版導入済みの場合も、下記2コマンドで更新と再導入を行ってください。キー経路のゲーム内表示は再検証待ちです。

Python 3.10以上。最新mainを取得し、Victoria 3を完全終了した状態でリポジトリ直下から実行します。

```powershell
git pull --ff-only origin main
powershell -ExecutionPolicy Bypass -File .\tools\install_probe.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Victoria 3"
```

installerはZIP由来の派生evidenceとinstalled treeを比較し、実際のinstalled treeに基づいてprobeを生成します。ZIPをPC上でも直接監査する場合は `-SourceArchive` を指定してください。country scripted-GUI定義が確認できたときだけselectorのGUI controlsを生成します。ZIPだけではその定義が不足しています。

[実測手順と結果収集](docs/runtime-verification-phase0.md)に従い、最初の起動でUnicode入力・2 slot・家具工場レベル・baseline・設定変更・Technology・Relations・Journal progress/status/pinをまとめて確認してください。full restart/loadのみ完全終了後の再起動が必須です。

確認後：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\collect_phase0_results.ps1
```

## 文字列保存APIの追加調査

軽量化プロジェクトの保存資料を流用し、GUIの型一覧出力、変数編集API、組み込みテストとprofilerを確認しました。[根拠と不足している接続](docs/feasibility/2026-10-07-optimization-api-reuse.md)、[現行ゲームから型・関数一覧を取得する手順](docs/runtime-api-evidence.md)。実際のruntime型一覧は未取得で、free-text保存は引き続きcandidateです。今回の調査だけでは入力callbackを追加せず、Task 7の判定も行いません。

## Offline tooling

```bash
python tools/audit_vanilla.py --source-archive /path/to/Vic3_todo_source.zip --output research/generated/phase0-api-evidence.json
python tools/build_probe.py --source-archive /path/to/Vic3_todo_source.zip --evidence research/generated/phase0-api-evidence.json --output dist/Vic3TODOProbe
python tools/render_capability_matrix.py --evidence research/generated/phase0-api-evidence.json --output docs/feasibility/tracker-capability-matrix.md
python -m unittest discover -s tests -v
python -m py_compile tools/*.py tests/*.py
```

Windowsでpy_compileのglob展開が必要な場合：

```powershell
$PythonFiles = Get-ChildItem .\tools\*.py, .\tests\*.py | ForEach-Object { $_.FullName }
python -m py_compile @PythonFiles
```

[Tracker matrix](docs/feasibility/tracker-capability-matrix.md)はAPIの静的証拠とruntime未検証を分けています。candidateをunsupportedへ変えるにはcoverageの証明が必要です。任意の `phase0-source-coverage.json` は `complete_directories` を明示する利用者側の宣言であり、exeとディレクトリの存在だけから完全性を断定しません。

Vanilla ZIP/展開ファイルはコミットしません。testsのfixtureは独自に作成した小さな合成資料です。probeはnamespaced stateのみを変更し、AI・経済・外交・建設のルールは変更しません。Journal GUIは置換しません。キー経路のため、入力sourceのHUDとshortcutbindingsに子要素を挿入して生成・導入します。同じHUD/shortcutファイルを変更するGUI MODとの併用は避けてください。
