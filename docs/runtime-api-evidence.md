# 現行ゲームの型・関数一覧を取得する

目的: TODOの「入力→MOD専用変数→save→復元」に必要なAPIを確認する。新しいDLL、native hook、ゲームファイルの書き換えは不要。**この手順は未実測で、資料にないconsole名や出力先を確定情報として扱わない。**

背景と根拠は[調査記録](feasibility/2026-10-07-optimization-api-reuse.md)。調査段階ではfree-text保存は`candidate`であり、入力probeに保存callbackは追加していない。

## 1. 準備

1. Victoria 3を終了する。通常のキャンペーンやIronmanではなく、検証用playsetと新規ゲームを使う。他のGUI MODは無効にする。
2. 実際のゲームversionを記録する。今回の資料は1.14.5だが、画面のversionと以下のexeハッシュを別々に残す。
3. 起動引数に`-debug_mode`を付ける。デバッグ起動は[公式Modding Dev Diary](https://www.paradoxinteractive.com/games/victoria-3/news/victoria-3-dev-diary-60-modding)で説明されている。型一覧の出力がこのビルドで利用できるかは、実画面で確認する。

PowerShellで、起動前に実行:

```powershell
$GameDir = 'D:\SteamLibrary\steamapps\common\Victoria 3'
$UserDataDir = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Paradox Interactive\Victoria 3'
$DumpStartedAtUtc = [DateTime]::UtcNow

Get-FileHash -LiteralPath (Join-Path $GameDir 'binaries\victoria3.exe') -Algorithm SHA256
foreach ($Name in @('caligula_branch.txt', 'caligula_rev.txt', 'clausewitz_branch.txt', 'clausewitz_rev.txt')) {
    $BuildFile = Join-Path $GameDir $Name
    if (Test-Path -LiteralPath $BuildFile -PathType Leaf) {
        Write-Output $Name
        Get-Content -LiteralPath $BuildFile
    }
}
```

ゲームフォルダーが違う場合は`$GameDir`だけを変更する。表示結果を保存または添付する。資料側のexeハッシュは`9b6f133a5dc235de9135d7b57e86ceda8282d1ba6c0e185f3ee19c22f8917f54`だが、違う場合に書き換えたり一致扱いにしたりしない。

## 2. 出力機能の入口を確認する

デバッグ起動したゲームでコンソールの補完・ヘルプ一覧、または公開されている開発用ツールの一覧から、型・関数をdumpする機能を探す。

- 確認済みのGUIは`clausewitz/gui/applicationutils/datatypes_explorer.gui`。`Dump datatypes`というボタンが`DatatypesExplorer.DumpDataTypes`を呼ぶ。
- **`DatatypesExplorer.DumpDataTypes`はGUI callback名であり、そのままconsole commandとは限らない。** この資料だけではconsole aliasを確定できない。
- 型一覧画面を実際に開けた場合は`Dump datatypes`を押す。コンソールに出力コマンドが表示される場合は、表示された正確な名前を確認してから実行する。
- script documentationについても、実際の補完・ヘルプで`script_docs`等の機能を確認してから実行する。既存資料の名称だけで現在のビルドで成功すると仮定しない。
- 入口が見つからない／unknown commandになる場合は、そこで止めてコンソールまたはツール一覧のスクリーンショットを添付する。未知のaliasを繰り返し試す必要はない。

出力時の通知・console結果を記録する。型／関数の表示フィルターが出力対象を絞るかは未確認なので、可能なら絞り込みを解除した一覧を取得する。絞り込みを解除できない場合は設定を記録する。

## 3. 出力ファイルを見つける

以下は**出力先の候補を調べる読み取り専用操作**。この調査では、出力先やファイル名をまだ確認できていない。起動前と同じPowerShellで実行:

```powershell
$DumpRoots = @(
    (Join-Path $UserDataDir 'docs'),
    (Join-Path $UserDataDir 'logs'),
    (Join-Path $UserDataDir 'data_types')
)

$DumpFiles = foreach ($CandidateRoot in $DumpRoots) {
    if (Test-Path -LiteralPath $CandidateRoot -PathType Container) {
        Get-ChildItem -LiteralPath $CandidateRoot -File -Recurse |
            Where-Object {
                $_.FullName -match '(?i)data.?types|datatype|script.?doc|effects\.log|triggers\.log|scopes\.log'
            }
    }
}

$DumpFiles | Sort-Object FullName -Unique |
    Select-Object FullName, Length, LastWriteTimeUtc,
        @{Name='UpdatedThisAttempt'; Expression={ $_.LastWriteTimeUtc -ge $DumpStartedAtUtc }} |
    Format-List

$DumpFiles | Sort-Object FullName -Unique | ForEach-Object {
    Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
}
```

新旧ファイルを混ぜず、更新時刻と実行時の通知を照合する。同じ内容が再出力されて更新時刻が変わらない可能性もあるため、`UpdatedThisAttempt`だけで現行ビルド由来だと断定しない。通知が別の出力先を示した場合は、その指定先を確認する。何も見つからなければ通知と一覧結果を添付する。

この結果は既存の`collect_phase0_results.ps1`とは別に添付する。現collectorは型一覧を収集せず、そのPASS/FAIL回答をAPI証拠に転用しない。

## 4. 添付するもの

- 型・関数一覧の出力ファイル。複数ファイルなら、生成された一覧のフォルダーをZIPにする。重要なpromoteが別ファイルにある可能性があるので、検索結果の数行だけではなく一覧全体が望ましい。
- script documentationのeffects/triggers/scopes等、実際に生成されたファイル。
- ゲームversion、exe SHA256、出力時のconsole通知／スクリーンショット、候補ファイル一覧・時刻・ハッシュ。
- 出力に失敗した場合は、そのエラーとツール／補完一覧。失敗はAPI不存在の証明にしない。

ゲームexe、save、launcherのアカウント情報、全Documents、全ゲームフォルダーを送る必要はない。

## 5. 取得後に調べる対象

型名は調査語であり、そのすべてが現行一覧に存在すると仮定しない。

| 調査語 | 確認したい契約 |
|---|---|
| `Country`, `Scope`, `Playable` | プレイヤー国の永続変数storeを得るpromote |
| `VariableStore`, `VariableEntry` | 特定のMOD専用slotの取得・作成・更新・読出し |
| `ScopeObjectEditor`, `ScopeObjectType` | 値の型、編集setterのsignature、通常GUIで取得できるcontext |
| `CString`, string, flag | 任意Unicode値の扱い。表示変換と格納・serializationを区別 |
| editbox callback, `ScriptedGui`, `TopScope` | GUI入力を保存先へ渡す正確な引数とscope |

一覧が揃ってもsave/loadの成功とは別。接続候補を最小probeで検証し、UI再生成→save/load→プロセス完全終了／再起動の結果を記録してからPhase 0を判定する。通常のTODO製品実装やnative fallbackへの承認は、この資料取得に含まれない。
