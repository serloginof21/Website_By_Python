from datetime import datetime
from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///TestPythonWebSite.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Отключаем предупреждения
db = SQLAlchemy(app)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    intro = db.Column(db.String(300), nullable=True)
    text = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Integer, nullable=True)
    views = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Article %r>' % self.id


@app.route('/')
@app.route('/home')
def index():
    # Получаем популярные статьи (топ-3 по просмотрам)
    popular_articles = Article.query.order_by(Article.views.desc()).limit(3).all()
    # Получаем последние статьи
    recent_articles = Article.query.order_by(Article.date.desc()).limit(3).all()

    return render_template("index.html", popular_articles=popular_articles, recent_articles=recent_articles)


@app.route('/posts')
def posts():
    # Получаем параметры из URL
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'date')  # date, score, views

    # Базовый запрос
    if search_query:
        # Поиск по названию или введению
        articles = Article.query.filter(
            (Article.title.contains(search_query)) |
            (Article.intro.contains(search_query))
        )
    else:
        articles = Article.query

    # Применяем сортировку
    if sort_by == 'score':
        # Сортируем по оценке (сначала высокие) и по дате
        articles = articles.order_by(Article.score.desc().nullslast(), Article.date.desc())
    elif sort_by == 'views':
        # Сортируем по просмотрам (сначала популярные) и по дате
        articles = articles.order_by(Article.views.desc().nullslast(), Article.date.desc())
    else:
        # Сортируем по дате (новые сверху)
        articles = articles.order_by(Article.date.desc())

    # Получаем все статьи
    articles = articles.all()

    return render_template("posts.html", articles=articles, search_query=search_query, sort_by=sort_by)


@app.route('/posts/<int:id>')
def posts_detail(id):
    article = Article.query.get(id)

    if article:
        article.views = (article.views or 0) + 1
        db.session.commit()

    # Получаем популярные статьи для боковой панели
    popular_articles = Article.query.order_by(Article.views.desc()).limit(5).all()

    return render_template("post_detail.html", article=article, popular_articles=popular_articles)

@app.route('/posts/<int:id>/delete')
def posts_delete(id):
    article = Article.query.get_or_404(id)

    try:
        db.session.delete(article)
        db.session.commit()
        return redirect('/posts')
    except:
        return "При удалении статьи произошла ошибка"


@app.route('/posts/<int:id>/update', methods=['POST', 'GET'])
def posts_update(id):
    article = Article.query.get(id)
    if request.method == 'POST':
        article.title = request.form['title']
        article.intro = request.form['intro']
        article.text = request.form['text']
        article.score = request.form.get('score', type=int)  # Обновляем оценку

        try:
            db.session.commit()
            return redirect('/posts')
        except:
            return "При редактировании статьи произошла ошибка!"
    else:
        return render_template("post_update.html", article=article)


@app.route('/create-article', methods=['POST', 'GET'])
def create_article():
    if request.method == 'POST':
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['text']
        score = request.form.get('score', type=int)  # Получаем оценку

        article = Article(title=title, intro=intro, text=text, score=score)

        try:
            db.session.add(article)
            db.session.commit()
            return redirect('/posts')
        except:
            return "При добавлении статьи произошла ошибка!"
    else:
        return render_template("create-article.html")


if __name__ == "__main__":
    app.run(debug=True)