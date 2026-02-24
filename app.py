import os
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, abort, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///limbo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Model Database ---
class Paste(db.Model):
    id = db.Column(db.String(8), primary_key=True) # IDpendek contoh: abc123
    content = db.Column(db.Text, nullable=False)
    syntax = db.Column(db.String(50), default='plaintext')
    created_at = db.Column(db.DateTime, default=datetime.now)
    views_left = db.Column(db.Integer, default=-1) # -1 = unlimited

# --- Buat Database ---
with app.app_context():
    db.create_all()

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form.get('content')
        syntax = request.form.get('syntax')
        burn = request.form.get('burn') #Checkbox
        
        # Generate IDpendek (6 karakter)
        paste_id = str(uuid.uuid4())[:6]
        
        # Logika Burn After Reading
        views_left = -1
        if burn:
            views_left = 1
            
        new_paste = Paste(id=paste_id, content=content, syntax=syntax, views_left=views_left)
        db.session.add(new_paste)
        db.session.commit()
        
        return redirect(url_for('view_paste', paste_id=paste_id))
        
    return render_template('index.html')

@app.route('/p/<paste_id>')
def view_paste(paste_id):
    paste = Paste.query.get_or_404(paste_id)
    
    # Cek jika paste sudah expired atau batas view tercapai
    if paste.views_left == 0:
        return "Link ini sudah hangus (Burned).", 410
        
    # Kurangi view jika menggunakan fitur Burn
    if paste.views_left > 0:
        paste.views_left -= 1
        if paste.views_left == 0:
            db.session.delete(paste) # Hapus dari database
        db.session.commit()
        
    return render_template('view.html', paste=paste)

@app.route('/raw/<paste_id>')
def raw_paste(paste_id):
    paste = Paste.query.get_or_404(paste_id)
    if paste.views_left == 0:
        return "Gone", 410
    response = make_response(paste.content)
    response.headers['Content-Type'] = 'text/plain'
    return response

if __name__ == '__main__':
    app.run(debug=True)
