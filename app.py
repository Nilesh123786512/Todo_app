from flask import Flask,render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from groq import Groq
import re



app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///todo.db'
db=SQLAlchemy(app)
api_key = os.getenv("groq_deepseek")  # Safely access your API key
client = Groq(api_key=api_key)

# Initialize conversation history with a system prompt
conversation = [
    {"role": "system", "content": """You are an AI assistant helping to add To-do tasks.You are given a message you should return 
    <title>Title here</title> and <desc>Description here</desc>
    make the title clearer and straight forward so that it gets me reminded easily
    """}
]


class Todo(db.Model):
    sno=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(200),nullable=False)
    description=db.Column(db.String(500),nullable=False)
    date_created =db.Column(db.DateTime, default=datetime.utcnow) 
    def __repr__(self):
        return f'{self.sno} - {self.title}'


@app.route('/createai',methods=['GET','POST'])
def create_with_ai():
    if request.method=="POST":
        user_input=request.form['description']
        conv=conversation.copy()
        conv.append({"role": "user", "content": user_input})
        stream = client.chat.completions.create(
            model="deepseek-r1-distill-qwen-32b",
            messages=conv,
            temperature=0.7,
            max_tokens=5000,
            stream=False  # Enable streaming
        )
        stream = stream.choices[0].message.content
        print(stream)
        cleaned_response = re.sub(r'<think>.*?</think>', '', stream, flags=re.DOTALL)
        title_match = re.search(r'<title>(.*?)</title>', cleaned_response)
        title = title_match.group(1) if title_match else None
        # Extract description
        desc_match = re.search(r'<desc>(.*?)</desc>', cleaned_response)
        desc = desc_match.group(1) if desc_match else None
        # print(f'Title-{title}')
        # print(f'Description-{desc}')
        todo=Todo(title=title,description=desc)
        # print('Deepseek responded successfully ')
        # print(f'Todo Created')
        db.session.add(todo)
        db.session.commit()
        # print(f'Todo formed')
        sno=todo.sno
        return redirect(f'/edit/{sno}')

        
    return render_template('createai.html')

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