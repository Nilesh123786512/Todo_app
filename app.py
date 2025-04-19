from flask import Flask,render_template,request,redirect,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
# from dotenv import load_dotenv
from groq import Groq
import re

# load_dotenv()

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///todo.db'
app.config['SECRET_KEY'] = 'some_random_secret_key' # Add a secret key for session management
db=SQLAlchemy(app)
api_key = os.getenv("groq")  # Safely access your API key
client = Groq(api_key=api_key)

# Initialize conversation history with a system prompt
conversation = [
    {"role": "system", "content": """You are an AI assistant helping to add To-do tasks. You are given a message and should return multiple suggested to-do items. For each suggested to-do, return it in the format <todo><title>Title here</title><desc>Description here</desc></todo>. Make the titles clear and straightforward so they are easy to remember. Ensure emojis are included to make them look wonderful. Generate at least 3-5 suggestions if possible, based on the user's input."""}
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
            model="deepseek-r1-distill-llama-70b",
            messages=conv,
            temperature=0.7,
            max_tokens=5000,
            stream=False  # Enable streaming
        )
        ai_response = stream.choices[0].message.content
        print(ai_response)
        # Find all todo blocks
        todo_blocks = re.findall(r'<todo>(.*?)</todo>', ai_response, re.DOTALL)
        
        suggested_todos = []
        for block in todo_blocks:
            title_match = re.search(r'<title>(.*?)</title>', block, re.DOTALL)
            desc_match = re.search(r'<desc>(.*?)</desc>', block, re.DOTALL)
            
            title = title_match.group(1).strip() if title_match else "No Title"
            description = desc_match.group(1).strip() if desc_match else "No Description"
            
            suggested_todos.append({'title': title, 'description': description})
            
        # Store suggested todos in session
        session['suggested_todos'] = suggested_todos
        
        # Redirect to a new route to review and confirm todos
        return redirect('/reviewai')


    return render_template('createai.html')

@app.route('/edit_suggested/<int:index>', methods=['GET', 'POST'])
def edit_suggested_todo(index):
    suggested_todos = session.get('suggested_todos', [])
    if index < 0 or index >= len(suggested_todos):
        # Invalid index, redirect back to review page
        return redirect('/reviewai')

    todo_to_edit = suggested_todos[index]

    if request.method == 'POST':
        # Update the todo in the session
        suggested_todos[index]['title'] = request.form['title']
        suggested_todos[index]['description'] = request.form['description']
        session['suggested_todos'] = suggested_todos # Update session
        return redirect('/reviewai')
    else:
        # Render edit form
        return render_template('edit_suggested.html', todo=todo_to_edit, index=index)


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

@app.route('/reviewai', methods=['GET', 'POST'])
def review_ai_todos():
    if request.method == 'POST':
        # Process confirmed todos
        confirmed_todos_data = request.form.getlist('todo_data')
        for todo_data_str in confirmed_todos_data:
            # Assuming todo_data_str is in the format "title|description"
            # Need to handle potential issues with '|' in title/description
            # A better approach would be to use indexed form fields
            parts = todo_data_str.split('|', 1)
            if len(parts) == 2:
                title = parts[0]
                description = parts[1]
                new_todo = Todo(title=title, description=description)
                db.session.add(new_todo)
        db.session.commit()
        session.pop('suggested_todos', None) # Clear suggested todos from session
        return redirect('/') # Redirect to home page after saving

    else: # GET request
        suggested_todos = session.get('suggested_todos', [])
        if not suggested_todos:
            # Redirect if no suggested todos are found in session
            return redirect('/createai')
        return render_template('reviewai.html', suggested_todos=suggested_todos)


@app.route('/edit_existing/<int:sno>',methods=['POST','GET'])
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
