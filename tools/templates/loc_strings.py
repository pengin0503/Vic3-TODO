# Hand-written localization for Vic3 TODO: key -> (Japanese, English).
# tools/generate_mod.py writes both language files from this table, so the
# two can never drift apart. Strings may use the game's data functions; in
# window rows the datacontext is the journal's (or tracker's) ScriptContainer.

SV = "ScriptContainer.MakeScope.ScriptValue('%s')"
PSV = "GetPlayer.MakeScope.ScriptValue('%s')"


def sv(name, fmt="0"):
    return "[" + SV % name + "|" + fmt + "]"


def psv(name, fmt="0"):
    return "[" + PSV % name + "|" + fmt + "]"


def onoff(tag):
    return "[SelectLocalization( ScriptContainer.HasTag('%s'), 'vic3_todo_on', 'vic3_todo_off' )]" % tag


LINE = "[ScriptContainer.MakeScope.Var('vic3_todo_line%d').GetFlagName]"
CARRIER = "[GetPlayer.MakeScope.Var('vic3_todo_in_carrier').GetCompany.GetNameNoFormatting]"
DATE_JA = sv("vic3_todo_dl_year") + "年" + sv("vic3_todo_dl_month") + "月" + sv("vic3_todo_dl_day") + "日"
DATE_EN = sv("vic3_todo_dl_day") + "/" + sv("vic3_todo_dl_month") + "/" + sv("vic3_todo_dl_year")
RULE = "[SelectLocalization( ScriptContainer.HasTag('vic3_todo_any'), 'vic3_todo_rule_any', 'vic3_todo_rule_all' )]"
CUR, GOAL = "vic3_todo_tr_disp_cur", "vic3_todo_tr_disp_goal"

STRINGS = {
    # window and launcher
    "vic3_todo_window_title": ("カスタムジャーナル", "Custom Journals"),
    "vic3_todo_launcher_tt": ("#b カスタムジャーナル#!\n自分で書いた目標・TODOをジャーナルとして管理します。",
                              "#b Custom Journals#!\nWrite your own goals and TODOs as Journal Entries."),
    "vic3_todo_new": ("＋ 新しいジャーナル", "+ New journal"),
    "vic3_todo_new_tt": ("ゲームの「名前の変更」入力欄が開きます。タイトルを入力して確定すると、ジャーナルが作られます。",
                         "Opens the game's rename box. Type a title and confirm it to create the journal."),
    "vic3_todo_counts": ("進行中 " + psv("vic3_todo_n_active") + " ・ 完了/失敗 " + psv("vic3_todo_n_finished") +
                         " ・ 空き " + psv("vic3_todo_n_free"),
                         "Active " + psv("vic3_todo_n_active") + " · Finished " + psv("vic3_todo_n_finished") +
                         " · Free slots " + psv("vic3_todo_n_free")),
    "vic3_todo_tab_active": ("進行中", "Active"),
    "vic3_todo_tab_finished": ("完了・失敗", "Finished"),
    "vic3_todo_empty": ("まだジャーナルがありません。「＋ 新しいジャーナル」から作成できます。\n作成したジャーナルはゲームのジャーナル画面にも表示され、ピン留めや完了通知もバニラと同じように動きます。",
                        "No journals yet. Use \"+ New journal\" to write one.\nYour journals also appear in the game's Journal, with pinning and completion notices like any other entry."),
    "vic3_todo_clear_finished": ("完了・失敗したものをすべて削除", "Delete all finished journals"),
    "vic3_todo_clear_confirm": ("本当にすべて削除しますか？", "Delete them all?"),
    "vic3_todo_yes_delete": ("削除する", "Delete"),
    "vic3_todo_no": ("やめる", "Cancel"),
    "vic3_todo_on": ("オン", "On"),
    "vic3_todo_off": ("オフ", "Off"),

    # text input
    "vic3_todo_input_help": ("#b 文字を入力中#!\nゲームの「名前の変更」欄に入力して確定してください（1行50文字まで）。確定すると自動で取り込まれます。入力の間だけ、入力用の一時的な会社が表示されることがあります（確定・キャンセルで消えます）。",
                             "#b Typing#!\nType into the game's rename box and confirm (up to 50 characters a line). The text is picked up automatically. While you type, a temporary input company may show; it goes away when you confirm or cancel."),
    "vic3_todo_input_current": ("現在の入力: #v " + CARRIER + "#!", "Current text: #v " + CARRIER + "#!"),
    "vic3_todo_input_open": ("入力欄を開く", "Open the box"),
    "vic3_todo_input_use": ("この文字で確定", "Use this text"),
    "vic3_todo_input_use_tt": ("自動で取り込まれなかった場合に押してください。", "Press this if the text was not picked up automatically."),
    "vic3_todo_input_cancel": ("キャンセル", "Cancel"),
    "vic3_todo_tt_no_input": ("ほかの入力が進行中でない", "No other text input is open"),
    "vic3_todo_tt_has_room": ("ジャーナルの空きがある（最大32件）", "There is room for another journal (32 at most)"),

    # rows
    "vic3_todo_line1": (LINE % 1, LINE % 1),
    "vic3_todo_line2": (LINE % 2, LINE % 2),
    "vic3_todo_line3": (LINE % 3, LINE % 3),
    "vic3_todo_line4": (LINE % 4, LINE % 4),
    "vic3_todo_status_line": ("状態: #v [ScriptContainer.GetCustom('vic3_todo_status')]#!",
                              "Status: #v [ScriptContainer.GetCustom('vic3_todo_status')]#!"),
    "vic3_todo_deadline_line": ("期限: " + DATE_JA + "（残り " + sv("vic3_todo_days_left") + " 日）",
                                "Deadline: " + DATE_EN + " (" + sv("vic3_todo_days_left") + " days left)"),
    "vic3_todo_deadline_date": (DATE_JA, DATE_EN),
    "vic3_todo_conditions_line": ("条件 " + sv("vic3_todo_tr_done_count") + " / " + sv("vic3_todo_tr_count") + " 達成（" + RULE + "）",
                                  "Conditions met " + sv("vic3_todo_tr_done_count") + " / " + sv("vic3_todo_tr_count") + " (" + RULE + ")"),
    "vic3_todo_rule_all": ("すべて満たすと達成", "all must be met"),
    "vic3_todo_rule_any": ("どれか1つで達成", "any one is enough"),
    "vic3_todo_complete_tt": ("完了にする", "Mark as completed"),
    "vic3_todo_reopen_tt": ("未完了に戻す", "Reopen"),
    "vic3_todo_edit_tt": ("編集する / 閉じる", "Edit / close"),
    "vic3_todo_pin_tt": ("アウトライナーにピン留めする", "Pin to the outliner"),
    "vic3_todo_unpin_tt": ("ピン留めを外す", "Unpin from the outliner"),
    "vic3_todo_complete": ("完了にする", "Complete"),
    "vic3_todo_open_in_window": ("編集画面で開く", "Edit in window"),

    # statuses (custom loc)
    "vic3_todo_status_done": ("#G 完了#!", "#G Completed#!"),
    "vic3_todo_status_failed": ("#R 失敗#!", "#R Failed#!"),
    "vic3_todo_status_overdue": ("#R 期限切れ#!", "#R Overdue#!"),
    "vic3_todo_status_met": ("#G 条件達成#!（自動完了がオフなら手動で完了にしてください）", "#G Conditions met#! (complete it by hand if auto-complete is off)"),
    "vic3_todo_status_progress": ("進行中", "In progress"),
    "vic3_todo_status_plain": ("メモ", "Note"),
    "vic3_todo_kind_unknown": ("不明な条件", "Unknown condition"),
    "vic3_todo_target_none": ("（未選択）", "(not chosen)"),

    # editor
    "vic3_todo_h_text": ("本文", "Text"),
    "vic3_todo_rewrite_1": ("タイトルを書き換え", "Rewrite title"),
    "vic3_todo_rewrite_2": ("2行目を書き換え", "Rewrite line 2"),
    "vic3_todo_rewrite_3": ("3行目を書き換え", "Rewrite line 3"),
    "vic3_todo_rewrite_4": ("4行目を書き換え", "Rewrite line 4"),
    "vic3_todo_add_line": ("行を追加", "Add a line"),
    "vic3_todo_add_line_tt": ("説明を1行追加します（最大4行、合計200文字）。", "Adds a line of description (4 lines, 200 characters at most)."),
    "vic3_todo_remove_line": ("最後の行を削除", "Remove last line"),
    "vic3_todo_h_features": ("ジャーナルの機能", "Journal features"),
    "vic3_todo_opt_auto": ("自動完了: " + onoff("vic3_todo_auto"), "Auto-complete: " + onoff("vic3_todo_auto")),
    "vic3_todo_opt_auto_tt": ("オンにすると、条件を満たした時点で自動的に完了します（週1回と画面を開いたときに判定）。",
                              "When on, the journal completes by itself once its conditions are met (checked weekly and when the window opens)."),
    "vic3_todo_opt_rule": ("達成ルール: " + RULE, "Rule: " + RULE),
    "vic3_todo_opt_rule_tt": ("条件をすべて満たす必要があるか、どれか1つでよいかを切り替えます。", "Switch between all conditions and any one condition."),
    "vic3_todo_opt_deadline": ("期限: " + onoff("vic3_todo_deadline_on"), "Deadline: " + onoff("vic3_todo_deadline_on")),
    "vic3_todo_opt_deadline_tt": ("期限を設定します。期限を過ぎても削除はされず「期限切れ」と表示されます。", "Sets a deadline. A missed deadline marks the journal overdue; it is not deleted."),
    "vic3_todo_opt_fail": ("期限切れで失敗: " + onoff("vic3_todo_fail_on_deadline"), "Fail when overdue: " + onoff("vic3_todo_fail_on_deadline")),
    "vic3_todo_opt_fail_tt": ("オンにすると、期限までに完了しなかったとき、バニラのジャーナルと同じように「失敗」になります。",
                              "When on, a journal not completed by its deadline fails, like a vanilla Journal Entry."),
    "vic3_todo_dl_minus_year": ("-1年", "-1y"),
    "vic3_todo_dl_minus_month": ("-30日", "-30d"),
    "vic3_todo_dl_plus_month": ("+30日", "+30d"),
    "vic3_todo_dl_plus_year": ("+1年", "+1y"),
    "vic3_todo_h_conditions": ("進捗の条件", "Progress conditions"),
    "vic3_todo_no_conditions": ("条件はありません。このままでも手動で完了できるメモとして使えます。条件を追加すると、ゲームの実際の状態から進捗が自動で計算されます。",
                                "No conditions. It works as a note you complete by hand. Add conditions to track progress from the live game state."),
    "vic3_todo_add_condition": ("＋ 条件を追加（最大4つ）", "+ Add a condition (4 at most)"),
    "vic3_todo_add_condition_tt": ("建物・経済・社会・技術・法律・外交・軍事・時間など、33種類から選べます。", "Choose from 33 kinds: buildings, economy, society, technology, laws, diplomacy, military and time."),
    "vic3_todo_delete": ("このジャーナルを削除", "Delete this journal"),
    "vic3_todo_delete_confirm": ("削除しますか？", "Delete it?"),
    "vic3_todo_close_editor": ("編集を閉じる", "Close editor"),

    # trackers
    "vic3_todo_tr_title": ("#b [ScriptContainer.GetCustom('vic3_todo_kind_name')]#!", "#b [ScriptContainer.GetCustom('vic3_todo_kind_name')]#!"),
    "vic3_todo_tr_target_building": ("[ScriptContainer.GetCustom('vic3_todo_tn_building')]", "[ScriptContainer.GetCustom('vic3_todo_tn_building')]"),
    "vic3_todo_tr_target_technology": ("[ScriptContainer.GetCustom('vic3_todo_tn_technology')]", "[ScriptContainer.GetCustom('vic3_todo_tn_technology')]"),
    "vic3_todo_tr_target_law": ("[ScriptContainer.GetCustom('vic3_todo_tn_law')]", "[ScriptContainer.GetCustom('vic3_todo_tn_law')]"),
    "vic3_todo_tr_target_goods": ("[ScriptContainer.GetCustom('vic3_todo_tn_goods')]", "[ScriptContainer.GetCustom('vic3_todo_tn_goods')]"),
    "vic3_todo_tr_target_interest_group": ("[ScriptContainer.GetCustom('vic3_todo_tn_interest_group')]", "[ScriptContainer.GetCustom('vic3_todo_tn_interest_group')]"),
    "vic3_todo_tr_target_country": ("[ScriptContainer.MakeScope.Var('vic3_todo_target_cap').GetState.GetCountry.GetName]",
                                    "[ScriptContainer.MakeScope.Var('vic3_todo_target_cap').GetState.GetCountry.GetName]"),
    "vic3_todo_tr_target_rank": ("目標: [ScriptContainer.GetCustom('vic3_todo_tn_rank')]", "Goal: [ScriptContainer.GetCustom('vic3_todo_tn_rank')]"),
    "vic3_todo_tr_invalid": ("#R 対象が未選択か無効です#!", "#R No valid target#!"),
    "vic3_todo_tr_nums_int": (sv(CUR) + " / " + sv(GOAL), sv(CUR) + " / " + sv(GOAL)),
    "vic3_todo_tr_nums_large": (sv(CUR, "K") + " / " + sv(GOAL, "K"), sv(CUR, "K") + " / " + sv(GOAL, "K")),
    "vic3_todo_tr_nums_dec": (sv(CUR, "1") + " / " + sv(GOAL, "1"), sv(CUR, "1") + " / " + sv(GOAL, "1")),
    "vic3_todo_tr_nums_days": (sv(CUR) + " / " + sv(GOAL) + " 日", sv(CUR) + " / " + sv(GOAL) + " days"),
    "vic3_todo_tr_nums_rank": ("現在: [ScriptContainer.GetCustom('vic3_todo_rank_current')]", "Now: [ScriptContainer.GetCustom('vic3_todo_rank_current')]"),
    "vic3_todo_tr_bool_yes": ("#G 達成#!", "#G Done#!"),
    "vic3_todo_tr_bool_no": ("未達成", "Not yet"),
    "vic3_todo_tr_percent": (sv("vic3_todo_tr_percent") + "%", sv("vic3_todo_tr_percent") + "%"),
    "vic3_todo_tr_detail_delta": ("[ScriptContainer.GetCustom('vic3_todo_mode_name')] ・ 現在 " + sv("vic3_todo_tr_disp_raw", "K") +
                                  " ・ 作成時 " + sv("vic3_todo_tr_disp_base", "K") + " ・ 完了値 " + sv("vic3_todo_tr_disp_finish", "K"),
                                  "[ScriptContainer.GetCustom('vic3_todo_mode_name')] · now " + sv("vic3_todo_tr_disp_raw", "K") +
                                  " · at creation " + sv("vic3_todo_tr_disp_base", "K") + " · completes at " + sv("vic3_todo_tr_disp_finish", "K")),
    "vic3_todo_tr_detail_absolute": ("[ScriptContainer.GetCustom('vic3_todo_mode_name')] ・ 作成時 " + sv("vic3_todo_tr_disp_base", "K"),
                                     "[ScriptContainer.GetCustom('vic3_todo_mode_name')] · at creation " + sv("vic3_todo_tr_disp_base", "K")),
    "vic3_todo_tr_settings_tt": ("条件の設定を開く / 閉じる", "Open / close the condition's settings"),
    "vic3_todo_tr_remove_tt": ("この条件を削除", "Remove this condition"),
    "vic3_todo_mode_1": ("作成時から増加", "Increase"),
    "vic3_todo_mode_2": ("目標値以上", "Reach at least"),
    "vic3_todo_mode_3": ("作成時から減少", "Decrease"),
    "vic3_todo_mode_4": ("目標値以下", "Reach at most"),
    "vic3_todo_mode_1_tt": ("作成時の値から、目標の量だけ増やす。作成前からある分は数えません。", "Increase by the goal from the value at creation. What existed before does not count."),
    "vic3_todo_mode_2_tt": ("値が目標値以上になったら達成。", "Met when the value reaches the goal or more."),
    "vic3_todo_mode_3_tt": ("作成時の値から、目標の量だけ減らす。", "Decrease by the goal from the value at creation."),
    "vic3_todo_mode_4_tt": ("値が目標値以下になったら達成。", "Met when the value is at or below the goal."),
    "vic3_todo_goal_minus_l": ("−大", "−L"),
    "vic3_todo_goal_minus_m": ("−中", "−M"),
    "vic3_todo_goal_minus_s": ("−小", "−S"),
    "vic3_todo_goal_plus_s": ("＋小", "+S"),
    "vic3_todo_goal_plus_m": ("＋中", "+M"),
    "vic3_todo_goal_plus_l": ("＋大", "+L"),
    "vic3_todo_goal_step_tt": ("目標値を変更します。刻み幅は条件の種類ごとに決まっています。目標値の変更では基準値は取り直しません。",
                               "Changes the goal. Step sizes depend on the kind. Changing the goal keeps the baseline."),
    "vic3_todo_pick_target": ("対象を選ぶ", "Choose target"),
    "vic3_todo_recapture": ("基準値を今の値に取り直す", "Reset baseline to now"),
    "vic3_todo_recapture_tt": ("「作成時の値」を現在の値で上書きします。", "Overwrites the value at creation with the current value."),
    "vic3_todo_country_choice": ("[Scope.GetState.GetCountry.GetName]", "[Scope.GetState.GetCountry.GetName]"),

    # Journal Entries
    "je_group_vic3_todo": ("カスタムジャーナル", "Custom Journals"),
    "vic3_todo_je_reason": ("あなたが書いたジャーナルです。編集はサイドバーの「カスタムジャーナル」ボタンから。",
                            "A journal you wrote. Edit it from the Custom Journals button on the sidebar."),
    "je_vic3_todo_complete_tt": ("このジャーナルを完了にする（手動、または条件達成による自動完了）", "This journal is completed (by hand, or automatically when its conditions are met)"),
    "je_vic3_todo_fail_tt": ("期限までに完了しなかった（「期限切れで失敗」がオンのとき）", "Not completed by its deadline (when \"Fail when overdue\" is on)"),
    "je_vic3_todo_status_overdue": ("#R 期限切れ#!", "#R Overdue#!"),
    "je_vic3_todo_status_met": ("#G 条件達成#!", "#G Conditions met#!"),
    "je_vic3_todo_status_tracked": ("進行中", "In progress"),
    "je_vic3_todo_status_plain": ("メモ", "Note"),

    # input carrier objects (seen briefly while typing)
    "company_vic3_todo_carrier": ("ここにジャーナルの文字を入力", "Type your journal text here"),
    "building_vic3_todo_carrier_anchor": ("ジャーナル入力用（建設されません）", "Journal input placeholder (never built)"),
    "pmg_vic3_todo_carrier_anchor": ("ジャーナル入力用", "Journal input placeholder"),
    "pm_vic3_todo_carrier_anchor": ("ジャーナル入力用", "Journal input placeholder"),
    "vic3_todo_carrier_slot": ("ジャーナル入力中", "Typing a journal"),
    "vic3_todo_carrier_slot_desc": ("ジャーナルの文字入力の間だけ、入力用の会社の枠を1つ追加します。", "Adds one company slot for the journal input company while you type."),
}
