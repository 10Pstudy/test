from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッション管理のための秘密鍵

# CSVファイルからクイズデータを読み込む
def load_quizzes():
    quizzes = []
    csv_file_path = os.path.join(os.path.dirname(__file__), 'quizzes.csv')
    try:
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                quiz = {
                    'category': row['category'],
                    'question': row['question'],
                    'options': [row['option1'], row['option2'], row['option3'], row['option4']],
                    'answer': row['answer']
                }
                quizzes.append(quiz)
    except FileNotFoundError:
        print("Error: quizzes.csv file not found.")
        return []
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []
    return quizzes

# 利用可能なカテゴリを取得
def get_categories(quizzes):
    return sorted(set(quiz['category'] for quiz in quizzes))

@app.route('/')
def index():
    session.clear()  # セッションをリセット
    return render_template('index.html')

@app.route('/select_category', methods=['GET', 'POST'])
def select_category():
    quizzes = load_quizzes()
    if not quizzes:
        return "クイズデータがありません。quizzes.csvを確認してください。", 500
    
    categories = get_categories(quizzes)
    
    if request.method == 'POST':
        selected_categories = request.form.getlist('categories')
        if not selected_categories:
            return "少なくとも1つのカテゴリを選択してください。", 400
        if all(cat in categories for cat in selected_categories):
            session['selected_categories'] = selected_categories
            # 選択したカテゴリのクイズをフィルタ
            filtered_quizzes = [q for q in quizzes if q['category'] in selected_categories]
            if not filtered_quizzes:
                return "選択したカテゴリにクイズがありません。", 400
            # クイズのインデックスをシャッフル
            quiz_indices = list(range(len(filtered_quizzes)))
            random.shuffle(quiz_indices)
            session['quiz_indices'] = quiz_indices
            session['filtered_quizzes'] = filtered_quizzes
            session['score'] = 0
            session['current_quiz'] = 0
            session['remaining_time_ms'] = 60 * 1000  # 初期時間：60秒（ミリ秒）
            session['start_time'] = datetime.now().isoformat()  # 開始時間
            return redirect(url_for('quiz'))
        else:
            return "無効なカテゴリが選択されました。", 400
    
    return render_template('select_category.html', categories=categories)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'selected_categories' not in session or 'quiz_indices' not in session or 'filtered_quizzes' not in session or 'remaining_time_ms' not in session:
        return redirect(url_for('select_category'))

    quizzes = session['filtered_quizzes']
    if not quizzes:
        return "クイズデータがありません。", 500

    # 時間切れチェック
    if session['remaining_time_ms'] <= 0:
        return redirect(url_for('result'))

    current_quiz = session['current_quiz']
    quiz_indices = session['quiz_indices']
    
    if current_quiz >= len(quizzes):
        return redirect(url_for('result'))

    # 現在のクイズ
    current_quiz_index = quiz_indices[current_quiz]
    current_quiz_data = quizzes[current_quiz_index].copy()
    
    # 選択肢をランダムにシャッフル
    options = current_quiz_data['options'].copy()
    random.shuffle(options)
    current_quiz_data['options'] = options
    
    if request.method == 'POST':
        user_answer = request.form.get('answer')
        correct_answer = quizzes[current_quiz_index]['answer']
        
        # 正誤判定と時間調整
        if user_answer == correct_answer:
            session['score'] += 1
            session['remaining_time_ms'] += 10 * 1000  # 正解：+10秒
        else:
            session['remaining_time_ms'] = max(0, session['remaining_time_ms'] - 20 * 1000)  # 不正解：-20秒
        
        # 次のクイズへ
        session['current_quiz'] += 1
        
        if session['current_quiz'] >= len(quizzes) or session['remaining_time_ms'] <= 0:
            return redirect(url_for('result'))
        return redirect(url_for('quiz'))
    
    return render_template('quiz.html', 
                         quiz=current_quiz_data, 
                         quiz_number=current_quiz + 1,
                         total_quizzes=len(quizzes),
                         remaining_time_ms=session['remaining_time_ms'])

@app.route('/result')
def result():
    score = session.get('score', 0)
    total = len(session.get('filtered_quizzes', []))
    categories = ', '.join(session.get('selected_categories', ['不明']))
    return render_template('result.html', score=score, total=total, categories=categories)

if __name__ == '__main__':
    app.run(debug=True)