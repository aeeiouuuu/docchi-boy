import json
import textwrap
import pathlib

INPUT_FILENAME = "questions_nomal.txt"


# --- チャートのHTMLテンプレート (v8 - ID表示版) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>どっちぼーい</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');

        :root {
            --bg-color: #f8f9fa;
            --node-bg: white;
            --node-border: #dee2e6;
            --text-color: #212529;
            --id-color: #adb5bd;
            --yes-color-strong: #28a745;
            --no-color-strong: #dc3545;
            --yes-color-faint: #a3d9a5; /* 薄い緑 */
            --no-color-faint: #f5c6cb;  /* 薄い赤 */
            --active-glow: #007bff;
            --answered-bg: #e9ecef;
        }

        body {
            font-family: 'Noto Sans JP', sans-serif;
            background-color: var(--bg-color);
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px;
            min-height: 100vh;
            box-sizing: border-box;
        }
        
        .controls {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            gap: 10px;
        }

        .btn {
            font-family: 'Noto Sans JP', sans-serif;
            font-size: 1em;
            font-weight: 700;
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 24px;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
        }
        #reload-btn {
            background: linear-gradient(145deg, #3b82f6, #60a5fa);
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        }
        #reset-route-btn {
            background: linear-gradient(145deg, #6c757d, #adb5bd);
            box-shadow: 0 4px 15px rgba(108, 117, 125, 0.3);
        }
        .btn:hover {
            transform: translateY(-2px);
        }

        .chart-wrapper {
            display: grid;
            grid-template-columns: 150px 1fr;
            grid-template-rows: repeat(6, minmax(120px, auto));
            gap: 0 20px;
            width: 1400px;
            position: relative;
            margin-top: 60px;
        }

        .tier-label {
            grid-column: 1; display: flex; flex-direction: column;
            justify-content: center; align-items: center; padding: 10px;
        }
        .tier-label.tier-3 { grid-row: 3; } .tier-label.tier-4 { grid-row: 4; } .tier-label.tier-5 { grid-row: 5; }
        .tier-name { font-size: 1.1em; font-weight: 700; color: #4b5563; }
        .tier-subname { font-size: 0.8em; color: #9ca3af; }
        .tier-multiplier { font-size: 1.8em; font-weight: 700; color: #2563eb; margin-top: 5px; }

        .level {
            grid-column: 2; display: flex; justify-content: space-around; align-items: center;
        }
        .level#level-0 { grid-row: 1; } .level#level-1 { grid-row: 2; } .level#level-2 { grid-row: 3; }
        .level#level-3 { grid-row: 4; } .level#level-4 { grid-row: 5; } .level#level-5 { grid-row: 6; }

        .node {
            background-color: var(--node-bg); border: 1px solid var(--node-border);
            border-radius: 12px; padding: 10px; width: 180px; height: 70px;
            display: flex; justify-content: center; align-items: center; text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); position: relative;
            z-index: 10; font-size: 0.95em; transition: all 0.2s;
        }
        .node-id {
            position: absolute;
            top: 6px;
            left: 10px;
            font-size: 0.8em;
            font-weight: 700;
            color: var(--id-color);
        }
        .node.clickable { cursor: pointer; }
        .node.active {
            box-shadow: 0 0 15px 5px var(--active-glow);
            border-color: var(--active-glow);
            transform: scale(1.05);
        }
        .node.answered { background-color: var(--answered-bg); color: #6c757d; }
        .node.answered .node-id { color: #9ca3af; }

        .goal-node {
            width: 90px; height: 80px; flex-direction: column; background-color: #fffbeb;
            border-color: #fde68a;
        }
        .goal-node .multiplier { font-size: 1.6em; font-weight: 700; color: #d97706; }
        .goal-node .label { font-size: 0.8em; color: #b45309; margin-top: 4px; }
        .goal-node.final-goal {
            box-shadow: 0 0 20px 8px #ffc107;
            border-color: #ffc107;
            transform: scale(1.1);
        }

        .chart-svg {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            z-index: 1; pointer-events: none;
        }
        .line {
            stroke-width: 2;
            fill: none;
            transition: all 0.3s ease-in-out;
        }
        .line-yes { stroke: var(--yes-color-faint); }
        .line-no { stroke: var(--no-color-faint); }

        .line.highlight-yes {
            stroke: var(--yes-color-strong);
            stroke-width: 5;
        }
        .line.highlight-no {
            stroke: var(--no-color-strong);
            stroke-width: 5;
        }
        
        /* Modal */
        #modal-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.6); z-index: 2000;
            display: none; justify-content: center; align-items: center;
        }
        #modal-content {
            background: white; padding: 30px 40px; border-radius: 15px;
            display: flex; gap: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .modal-btn {
            font-size: 1.5em; padding: 15px 40px; border-radius: 10px;
        }
        #modal-yes { background-color: var(--yes-color-strong); }
        #modal-no { background-color: var(--no-color-strong); }
    </style>
</head>
<body>
    <div class="controls">
        <button id="reload-btn" class="btn">新しいチャート</button>
        <button id="reset-route-btn" class="btn">ルートをリセット</button>
    </div>

    <div id="modal-overlay">
        <div id="modal-content">
            <button id="modal-no" class="btn modal-btn">いいえ</button>
            <button id="modal-yes" class="btn modal-btn">はい</button>
        </div>
    </div>

    <div class="chart-wrapper">
        <!-- Tier Labels -->
        <div class="tier-label tier-3"><div class="tier-name">知人の段</div><div class="tier-subname">ACQUAINTANCE</div><div class="tier-multiplier">x2</div></div>
        <div class="tier-label tier-4"><div class="tier-name">友達の段</div><div class="tier-subname">FRIEND</div><div class="tier-multiplier">x3</div></div>
        <div class="tier-label tier-5"><div class="tier-name">親友の段</div><div class="tier-subname">BEST FRIEND</div><div class="tier-multiplier">x4</div></div>

        <!-- SVG Lines with IDs and default color classes -->
        <svg class="chart-svg" viewbox="0 0 1400 780" preserveAspectRatio="xMidYMid meet">
            <g>
                <path id="line-0-0-no" class="line line-no" d="M 775 55 L 575 165"/><path id="line-0-0-yes" class="line line-yes" d="M 775 55 L 975 165"/>
                <path id="line-1-0-no" class="line line-no" d="M 575 225 L 425 305"/><path id="line-1-0-yes" class="line line-yes" d="M 575 225 L 775 305"/>
                <path id="line-1-1-no" class="line line-no" d="M 975 225 L 775 305"/><path id="line-1-1-yes" class="line line-yes" d="M 975 225 L 1125 305"/>
                <path id="line-2-0-no" class="line line-no" d="M 425 365 L 325 425"/><path id="line-2-0-yes" class="line line-yes" d="M 425 365 L 625 425"/>
                <path id="line-2-1-no" class="line line-no" d="M 775 365 L 625 425"/><path id="line-2-1-yes" class="line line-yes" d="M 775 365 L 925 425"/>
                <path id="line-2-2-no" class="line line-no" d="M 1125 365 L 925 425"/><path id="line-2-2-yes" class="line line-yes" d="M 1125 365 L 1225 425"/>
                <path id="line-3-0-no" class="line line-no" d="M 325 485 L 275 545"/><path id="line-3-0-yes" class="line line-yes" d="M 325 485 L 475 545"/>
                <path id="line-3-1-no" class="line line-no" d="M 625 485 L 475 545"/><path id="line-3-1-yes" class="line line-yes" d="M 625 485 L 725 545"/>
                <path id="line-3-2-no" class="line line-no" d="M 925 485 L 825 545"/><path id="line-3-2-yes" class="line line-yes" d="M 925 485 L 1075 545"/>
                <path id="line-3-3-no" class="line line-no" d="M 1225 485 L 1075 545"/><path id="line-3-3-yes" class="line line-yes" d="M 1225 485 L 1275 545"/>
                <path id="line-4-0-no" class="line line-no" d="M 275 605 L 235 685"/><path id="line-4-0-yes" class="line line-yes" d="M 275 605 L 345 685"/>
                <path id="line-4-1-no" class="line line-no" d="M 475 605 L 455 685"/><path id="line-4-1-yes" class="line line-yes" d="M 475 605 L 565 685"/>
                <path id="line-4-2-no" class="line line-no" d="M 725 605 L 675 685"/><path id="line-4-2-yes" class="line line-yes" d="M 725 605 L 785 685"/>
                <path id="line-4-3-no" class="line line-no" d="M 825 605 L 765 685"/><path id="line-4-3-yes" class="line line-yes" d="M 825 605 L 875 685"/>
                <path id="line-4-4-no" class="line line-no" d="M 1075 605 L 985 685"/><path id="line-4-4-yes" class="line line-yes" d="M 1075 605 L 1095 685"/>
                <path id="line-4-5-no" class="line line-no" d="M 1275 605 L 1205 685"/><path id="line-4-5-yes" class="line line-yes" d="M 1275 605 L 1315 685"/>
            </g>
        </svg>

        <!-- Question nodes with IDs -->
        <div class="level" id="level-0"><div id="node-0-0" class="node"></div></div>
        <div class="level" id="level-1"><div id="node-1-0" class="node"></div><div id="node-1-1" class="node"></div></div>
        <div class="level" id="level-2"><div id="node-2-0" class="node"></div><div id="node-2-1" class="node"></div><div id="node-2-2" class="node"></div></div>
        <div class="level" id="level-3"><div id="node-3-0" class="node"></div><div id="node-3-1" class="node"></div><div id="node-3-2" class="node"></div><div id="node-3-3" class="node"></div></div>
        <div class="level" id="level-4"><div id="node-4-0" class="node"></div><div id="node-4-1" class="node"></div><div id="node-4-2" class="node"></div><div id="node-4-3" class="node"></div><div id="node-4-4" class="node"></div></div>

        <!-- Goal Level with IDs -->
        <div class="level" id="level-5">
            <div id="goal-0" class="node goal-node"><span class="multiplier">x16</span><span class="label">SOULMATE</span></div>
            <div id="goal-1" class="node goal-node"><span class="multiplier">x16</span><span class="label">SOULMATE</span></div>
            <div id="goal-2" class="node goal-node"><span class="multiplier">x12</span><span class="label">SOULMATE</span></div>
            <div id="goal-3" class="node goal-node"><span class="multiplier">x12</span><span class="label">SOULMATE</span></div>
            <div id="goal-4" class="node goal-node"><span class="multiplier">x8</span><span class="label">SOULMATE</span></div>
            <div id="goal-5" class="node goal-node"><span class="multiplier">x8</span><span class="label">SOULMATE</span></div>
            <div id="goal-6" class="node goal-node"><span class="multiplier">x12</span><span class="label">SOULMATE</span></div>
            <div id="goal-7" class="node goal-node"><span class="multiplier">x12</span><span class="label">SOULMATE</span></div>
            <div id="goal-8" class="node goal-node"><span class="multiplier">x16</span><span class="label">SOULMATE</span></div>
            <div id="goal-9" class="node goal-node"><span class="multiplier">x16</span><span class="label">SOULMATE</span></div>
        </div>
    </div>

    <script>
        const allQuestions = __QUESTIONS_JSON__;
        const nodes = document.querySelectorAll('.chart-wrapper .node');
        const questionNodes = document.querySelectorAll('.chart-wrapper .level:not(#level-5) .node');
        const lines = document.querySelectorAll('.chart-svg .line');
        
        const reloadBtn = document.getElementById('reload-btn');
        const resetRouteBtn = document.getElementById('reset-route-btn');
        
        const modalOverlay = document.getElementById('modal-overlay');
        const modalYesBtn = document.getElementById('modal-yes');
        const modalNoBtn = document.getElementById('modal-no');

        let currentNodeId = null;
        let gameActive = false;

        const chartMap = {
            'node-0-0': { no: 'node-1-0', yes: 'node-1-1' }, 'node-1-0': { no: 'node-2-0', yes: 'node-2-1' },
            'node-1-1': { no: 'node-2-1', yes: 'node-2-2' }, 'node-2-0': { no: 'node-3-0', yes: 'node-3-1' },
            'node-2-1': { no: 'node-3-1', yes: 'node-3-2' }, 'node-2-2': { no: 'node-3-2', yes: 'node-3-3' },
            'node-3-0': { no: 'node-4-0', yes: 'node-4-1' }, 'node-3-1': { no: 'node-4-1', yes: 'node-4-2' },
            'node-3-2': { no: 'node-4-2', yes: 'node-4-3' }, 'node-3-3': { no: 'node-4-3', yes: 'node-4-4' },
            'node-4-0': { no: 'goal-0', yes: 'goal-1' }, 'node-4-1': { no: 'goal-2', yes: 'goal-3' },
            'node-4-2': { no: 'goal-4', yes: 'goal-5' }, 'node-4-3': { no: 'goal-6', yes: 'goal-7' },
            'node-4-4': { no: 'goal-8', yes: 'goal-9' },
        };
        
        const nodeIdentifiers = [
            'A-1', 'B-1', 'B-2', 'C-1', 'C-2', 'C-3', 'D-1', 'D-2', 'D-3', 'D-4',
            'E-1', 'E-2', 'E-3', 'E-4', 'E-5'
        ];

        function generateChart() {
            let shuffled = [...allQuestions];
            for (let i = shuffled.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
            }
            const selectedQuestions = shuffled.slice(0, 15);
            questionNodes.forEach((node, index) => {
                if (selectedQuestions[index]) {
                    const text = selectedQuestions[index];
                    const wrappedText = text.replace(/(.{10})/g, "$1<br>");
                    const identifier = nodeIdentifiers[index];
                    node.innerHTML = `<span class="node-id">${identifier}</span>${wrappedText}`;
                }
            });
            resetRoute();
        }

        function resetRoute() {
            nodes.forEach(n => n.classList.remove('active', 'answered', 'clickable', 'final-goal'));
            lines.forEach(l => l.classList.remove('highlight-yes', 'highlight-no'));
            
            const startNode = document.getElementById('node-0-0');
            startNode.classList.add('active', 'clickable');
            gameActive = true;
        }

        function handleNodeClick(e) {
            if (!gameActive || !e.currentTarget.classList.contains('clickable')) return;
            currentNodeId = e.currentTarget.id;
            modalOverlay.style.display = 'flex';
        }

        function handleChoice(choice) {
            modalOverlay.style.display = 'none';
            if (!currentNodeId) return;

            const currentNode = document.getElementById(currentNodeId);
            const nextNodeId = chartMap[currentNodeId][choice];
            const lineId = `line-${currentNodeId.split('-')[1]}-${currentNodeId.split('-')[2]}-${choice}`;
            const line = document.getElementById(lineId);

            currentNode.classList.remove('active', 'clickable');
            currentNode.classList.add('answered');
            if (line) line.classList.add(choice === 'yes' ? 'highlight-yes' : 'highlight-no');

            const nextNode = document.getElementById(nextNodeId);
            if (nextNode) {
                if (nextNodeId.startsWith('goal')) {
                    nextNode.classList.add('final-goal');
                    gameActive = false;
                } else {
                    nextNode.classList.add('active', 'clickable');
                }
            }
            currentNodeId = null;
        }

        reloadBtn.addEventListener('click', generateChart);
        resetRouteBtn.addEventListener('click', resetRoute);
        questionNodes.forEach(node => node.addEventListener('click', handleNodeClick));
        modalYesBtn.addEventListener('click', () => handleChoice('yes'));
        modalNoBtn.addEventListener('click', () => handleChoice('no'));
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) modalOverlay.style.display = 'none';
        });
        
        document.addEventListener('DOMContentLoaded', generateChart);
    </script>
</body>
</html>
"""

def create_interactive_chart(input_filename): # 引数をシンプルに変更
    """
    Generates a self-contained, interactive HTML file from a given question file.
    """
    input_path = pathlib.Path(input_filename)

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            all_questions = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"エラー: '{input_filename}' が見つかりません。")
        return
    except Exception as e:
        print(f"エラー: ファイル読み込み中に問題が発生しました: {e}")
        return

    if len(all_questions) < 15:
        print(f"エラー: 質問が15個以上必要です。(現在: {len(all_questions)}個)")
        return

    questions_json = json.dumps(all_questions, ensure_ascii=False)
    output_html = HTML_TEMPLATE.replace('__QUESTIONS_JSON__', questions_json)

    # 出力ファイル名を自動生成
    # 例: "questions_love.txt" -> "docchi-boy_questions_love.html"
    output_stem = input_path.stem
    final_output_filename = f"docchi-boy_{output_stem}.html"

    with open(final_output_filename, 'w', encoding='utf-8') as f:
        f.write(output_html)

    print(f"成功！ '{final_output_filename}' が生成されました。")
    print("インタラクティブなゲーム盤をお楽しみください！")

if __name__ == '__main__':
    # スクリプト冒頭で設定した INPUT_FILENAME を使って関数を実行
    create_interactive_chart(INPUT_FILENAME)