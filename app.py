from flask import Flask,render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///todo.db'
db=SQLAlchemy(app)

class Todo(db.Model):
    sno=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(200),nullable=False)
    description=db.Column(db.String(500),nullable=False)
    date_created =db.Column(db.DateTime, default=datetime.utcnow) 
    def __repr__(self):
        return f'{self.sno} - {self.title}'


@app.route('/',methods=['GET','POST'])
def hello(): 
    if request.method=='POST':
        title=request.form['title']
        description=request.form['description']
        todo=Todo(title=title,description=description)
        # print(f'Todo Created')
        db.session.add(todo)
        db.session.commit()
        # print(f'Todo Added to database')
    allTodo=Todo.query.all()
    return render_template('index.html',allTodos=allTodo)

@app.route('/edit/<int:sno>',methods=['POST','GET'])
def edit(sno):
    if request.method=='POST':
        title=request.form['title']
        description=request.form['description']
        edit_todo=Todo.query.filter_by(sno=sno).first()
        edit_todo.title=title
        edit_todo.description=description
        db.session.commit()
        return redirect('/')
    else:
        edit_todo=Todo.query.filter_by(sno=sno).first()
        return render_template('edit.html',todo=edit_todo)

  
    
@app.route('/delete/<int:sno>')
def delete(sno):
    del_todo=Todo.query.filter_by(sno=sno).first()
    db.session.delete(del_todo)
    db.session.commit()
    return redirect('/')




if __name__=='__main__':
    app.run(debug=False,host='0.0.0.0',port=5000)