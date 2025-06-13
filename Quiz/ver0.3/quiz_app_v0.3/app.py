from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import os
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

QUIZZES = []

def load_quizzes():
    quizzes = []
    csv_file_path = os.path.join(os.path.dirname(__file__), 'quizzes.csv')
    try:
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            required_fields = ['category', 'difficulty', 'question', 'option1', 'option2', 'option3', 'option4', 'answer']
            for row_num, row in enumerate(reader, start=1):
                if not any(row.values()):
                    continue
                if not all(field in row for field in required_fields):
                    flash(f'行{row_num}: 必須フィールドが欠けています。スキップします。', 'warning')
                    continue
                if not all(row[field].strip() for field in required_fields):
                    flash(f'行{row_num}: 空の値が含まれています。スキップします。', 'warning')
                    continue
                options = [row['option1'], row['option2'], row['option3'], row['option4']]
                if len(set(options)) != len(options):
                    flash(f'行{row_num}: 選択肢に重複があります。スキップします。', 'warning')
                    continue
                if row['answer'] not in options:
                    flash(f'行{row_num}: 正解が選択肢に含まれていません。スキップします。', 'warning')
                    continue
                quiz = {
                    'category': row['category'].strip(),
                    'difficulty': row['difficulty'].strip(),
                    'question': row['question'].strip(),
                    'options': [row['option1'].strip(), row['option2'].strip(), row['option3'].strip(), row['option4'].strip()],
                    'answer': row['answer'].strip()
                }
                quizzes.append(quiz)
    except FileNotFoundError:
        flash('quizzes.csvが見つかりません。', 'error')
        return []
    except csv.Error:
        flash('CSVファイルの形式が不正です。', 'error')
        return []
    except Exception as e:
        flash(f'CSV読み込みエラー: {e}', 'error')
        return []
    if not quizzes:
        flash('有効なクイズデータがありません。', 'error')
    return quizzes

QUIZZES = load_quizzes()

def get_categories_and_difficulties(quizzes):
    categories = sorted(set(quiz['category'] for quiz in quizzes))
    difficulties = sorted(set(quiz['difficulty'] for quiz in quizzes))
    quiz_counts = {}
    category_counts = {}
    difficulty_counts = {}
    for cat in categories:
        quiz_counts[cat] = {}
        category_counts[cat] = 0
        for diff in difficulties:
            count = len([q for q in quizzes if q['category'] == cat and q['difficulty'] == diff])
            quiz_counts[cat][diff] = count
            category_counts[cat] += count
    for diff in difficulties:
        difficulty_counts[diff] = sum(quiz_counts[cat][diff] for cat in categories)
    return categories, difficulties, quiz_counts, category_counts, difficulty_counts

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/select_category', methods=['GET', 'POST'])
def select_category():
    if not QUIZZES:
        return redirect(url_for('index'))
    
    categories, difficulties, quiz_counts, category_counts, difficulty_counts = get_categories_and_difficulties(QUIZZES)
    
    if request.method == 'POST':
        selected_categories = request.form.getlist('categories')
        selected_difficulties = request.form.getlist('difficulties')
        if not selected_categories or not selected_difficulties:
            flash('カテゴリと難易度をそれぞれ1つ以上選択してください。', 'error')
            return redirect(url_for('select_category'))
        if not all(cat in categories for cat in selected_categories) or not all(diff in difficulties for diff in selected_difficulties):
            flash(f'無効な選択です。カテゴリ: {selected_categories}, 難易度: {selected_difficulties}', 'error')
            return redirect(url_for('select_category'))
        filtered_quizzes = [
            q for q in QUIZZES 
            if q['category'] in selected_categories and q['difficulty'] in selected_difficulties
        ]
        if not filtered_quizzes:
            flash('選択したカテゴリと難易度にクイズがありません。', 'error')
            return redirect(url_for('select_category'))
        quiz_indices = list(range(len(filtered_quizzes)))
        random.shuffle(quiz_indices)
        session['quiz_indices'] = quiz_indices
        session['selected_categories'] = selected_categories
        session['selected_difficulties'] = selected_difficulties
        session['score'] = 0
        session['current_quiz'] = 0
        session['remaining_time_ms'] = 60 * 1000
        session['start_time'] = datetime.now().isoformat()
        session['used_quiz_indices'] = []
        return redirect(url_for('quiz'))
    
    return render_template('select_category.html', 
                         categories=categories, 
                         difficulties=difficulties, 
                         category_counts=category_counts, 
                         difficulty_counts=difficulty_counts)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'selected_categories' not in session or 'quiz_indices' not in session or 'remaining_time_ms' not in session:
        return redirect(url_for('select_category'))

    selected_categories = session['selected_categories']
    selected_difficulties = session['selected_difficulties']
    filtered_quizzes = [
        q for q in QUIZZES 
        if q['category'] in selected_categories and q['difficulty'] in selected_difficulties
    ]
    if not filtered_quizzes:
        flash('クイズデータがありません。', 'error')
        return redirect(url_for('index'))

    if session['remaining_time_ms'] <= 0:
        return redirect(url_for('result'))

    current_quiz = session['current_quiz']
    quiz_indices = session['quiz_indices']
    used_quiz_indices = session.get('used_quiz_indices', [])
    
    if current_quiz >= len(filtered_quizzes) or len(used_quiz_indices) >= len(filtered_quizzes):
        return redirect(url_for('result'))

    available_indices = [i for i in quiz_indices if i not in used_quiz_indices]
    if not available_indices:
        return redirect(url_for('result'))
    
    current_quiz_index = available_indices[0]
    current_quiz_data = filtered_quizzes[current_quiz_index].copy()
    
    options = current_quiz_data['options'].copy()
    random.shuffle(options)
    current_quiz_data['options'] = options
    
    if request.method == 'POST':
        if 'skip' in request.form:
            session['remaining_time_ms'] = max(0, session['remaining_time_ms'] - 10 * 1000)
            flash('クイズをスキップしました。-10秒', 'warning')
            session['used_quiz_indices'].append(current_quiz_index)
            session['current_quiz'] += 1
            if session['current_quiz'] >= len(filtered_quizzes) or session['remaining_time_ms'] <= 0:
                return redirect(url_for('result'))
            return redirect(url_for('quiz'))
        
        user_answer = request.form.get('answer')
        correct_answer = filtered_quizzes[current_quiz_index]['answer']
        
        if user_answer == correct_answer:
            session['score'] += 1
            session['remaining_time_ms'] += 10 * 1000
            flash('正解！+10秒追加', 'success')
        else:
            session['remaining_time_ms'] = max(0, session['remaining_time_ms'] - 20 * 1000)
            flash('不正解。-20秒', 'error')
        
        session['used_quiz_indices'].append(current_quiz_index)
        session['current_quiz'] += 1
        
        if session['current_quiz'] >= len(filtered_quizzes) or session['remaining_time_ms'] <= 0:
            return redirect(url_for('result'))
        return redirect(url_for('quiz'))
    
    return render_template('quiz.html', 
                         quiz=current_quiz_data, 
                         quiz_number=current_quiz + 1,
                         total_quizzes=len(filtered_quizzes),
                         remaining_time_ms=session['remaining_time_ms'])

@app.route('/result')
def result():
    score = session.get('score', 0)
    total = len([
        q for q in QUIZZES 
        if q['category'] in session.get('selected_categories', []) 
        and q['difficulty'] in session.get('selected_difficulties', [])
    ])
    categories = ', '.join(session.get('selected_categories', ['不明']))
    difficulties = ', '.join(session.get('selected_difficulties', ['不明']))
    return render_template('result.html', score=score, total=total, categories=categories, difficulties=difficulties)

if __name__ == '__main__':
    app.run(debug=True)