from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import os
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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
                    'difficulty': row['difficulty'],
                    'question': row['question'],
                    'options': [row['option1'], row['option2'], row['option3'], row['option4']],
                    'answer': row['answer']
                }
                quizzes.append(quiz)
    except FileNotFoundError:
        flash('quizzes.csvが見つかりません。', 'error')
        return []
    except Exception as e:
        flash(f'CSV読み込みエラー: {e}', 'error')
        return []
    return quizzes

# カテゴリと難易度を取得
def get_categories_and_difficulties(quizzes):
    categories = sorted(set(quiz['category'] for quiz in quizzes))
    difficulties = sorted(set(quiz['difficulty'] for quiz in quizzes))
    return categories, difficulties

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/select_category', methods=['GET', 'POST'])
def select_category():
    quizzes = load_quizzes()
    if not quizzes:
        return redirect(url_for('index'))
    
    categories, difficulties = get_categories_and_difficulties(quizzes)
    
    if request.method == 'POST':
        selected_categories = request.form.getlist('categories')
        selected_difficulties = request.form.getlist('difficulties')
        if not selected_categories or not selected_difficulties:
            flash('カテゴリと難易度をそれぞれ1つ以上選択してください。', 'error')
            return redirect(url_for('select_category'))
        if all(cat in categories for cat in selected_categories) and all(diff in difficulties for diff in selected_difficulties):
            session['selected_categories'] = selected_categories
            session['selected_difficulties'] = selected_difficulties
            filtered_quizzes = [
                q for q in quizzes 
                if q['category'] in selected_categories and q['difficulty'] in selected_difficulties
            ]
            if not filtered_quizzes:
                flash('選択したカテゴリと難易度にクイズがありません。', 'error')
                return redirect(url_for('select_category'))
            quiz_indices = list(range(len(filtered_quizzes)))
            random.shuffle(quiz_indices)
            session['quiz_indices'] = quiz_indices
            session['filtered_quizzes'] = filtered_quizzes
            session['score'] = 0
            session['current_quiz'] = 0
            session['remaining_time_ms'] = 60 * 1000
            session['start_time'] = datetime.now().isoformat()
            return redirect(url_for('quiz'))
        else:
            flash('無効なカテゴリまたは難易度が選択されました。', 'error')
    
    return render_template('select_category.html', categories=categories, difficulties=difficulties)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'selected_categories' not in session or 'quiz_indices' not in session or 'filtered_quizzes' not in session or 'remaining_time_ms' not in session:
        return redirect(url_for('select_category'))

    quizzes = session['filtered_quizzes']
    if not quizzes:
        flash('クイズデータがありません。', 'error')
        return redirect(url_for('index'))

    if session['remaining_time_ms'] <= 0:
        return redirect(url_for('result'))

    current_quiz = session['current_quiz']
    quiz_indices = session['quiz_indices']
    
    if current_quiz >= len(quizzes):
        return redirect(url_for('result'))

    current_quiz_index = quiz_indices[current_quiz]
    current_quiz_data = quizzes[current_quiz_index].copy()
    
    options = current_quiz_data['options'].copy()
    random.shuffle(options)
    current_quiz_data['options'] = options
    
    if request.method == 'POST':
        user_answer = request.form.get('answer')
        correct_answer = quizzes[current_quiz_index]['answer']
        
        if user_answer == correct_answer:
            session['score'] += 1
            session['remaining_time_ms'] += 10 * 1000
            flash('正解！+10秒追加', 'success')
        else:
            session['remaining_time_ms'] = max(0, session['remaining_time_ms'] - 20 * 1000)
            flash('不正解。-20秒', 'error')
        
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
    difficulties = ', '.join(session.get('selected_difficulties', ['不明']))
    return render_template('result.html', score=score, total=total, categories=categories, difficulties=difficulties)

if __name__ == '__main__':
    app.run(debug=True)