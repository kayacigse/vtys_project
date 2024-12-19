from flask import Flask, render_template, request, redirect, url_for, flash
from db import get_db_connection
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Anasayfa
@app.route('/')
def index():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Projects")
    projects = cursor.fetchall()
    db.close()
    return render_template('index.html', projects=projects)

# Proje Yönetimi
@app.route('/projects', methods=['GET', 'POST'])
def projects():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        try:
            name = request.form['name']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            cursor.execute(
                "INSERT INTO Projects (name, start_date, end_date) VALUES (%s, %s, %s)",
                (name, start_date, end_date)
            )
            db.commit()
            flash("Project added successfully!", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")
    cursor.execute("SELECT * FROM Projects")
    projects = cursor.fetchall()
    db.close()
    return render_template('projects.html', projects=projects)

@app.route('/projects/<int:project_id>')
def project_detail(project_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()
    
    cursor.execute("SELECT * FROM Tasks WHERE project_id = %s", (project_id,))
    tasks = cursor.fetchall()
    
    # Gecikme kontrolü ve bitiş tarihi güncellemesi
    for task in tasks:
        if task['status'] == 'In Progress' or task['status'] == 'Completed':
            due_date = datetime.strptime(task['start_date'], '%Y-%m-%d') + timedelta(days=task['duration'])
            if datetime.now() > due_date and task['status'] != 'Completed':
                delay_days = (datetime.now() - due_date).days
                project['end_date'] = (datetime.now() + timedelta(days=delay_days)).strftime('%Y-%m-%d')
                cursor.execute(
                    "UPDATE Projects SET end_date = %s WHERE id = %s",
                    (project['end_date'], project_id)
                )
                db.commit()
    db.close()
    return render_template('project_detail.html', project=project, tasks=tasks)

@app.route('/projects/delete/<int:project_id>')
def delete_project(project_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM Tasks WHERE project_id = %s", (project_id,))
        cursor.execute("DELETE FROM Projects WHERE id = %s", (project_id,))
        db.commit()
        flash("Project and its tasks deleted successfully!", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    db.close()
    return redirect(url_for('projects'))

# Görev Yönetimi
@app.route('/tasks/add/<int:project_id>', methods=['GET', 'POST'])
def add_task(project_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        try:
            name = request.form['name']
            assigned_to = request.form['assigned_to']
            start_date = request.form['start_date']
            duration = request.form['duration']
            status = request.form['status']  # Burada formdan gelen status değerini alıyoruz

            # Status değerinin geçerli olduğundan emin olun
            valid_statuses = ['Tamamlanacak', 'Devam Ediyor', 'Tamamlandı']
            if status not in valid_statuses:
                flash("Invalid status value.", "danger")
                return redirect(url_for('add_task', project_id=project_id))

            cursor.execute(
                "INSERT INTO Tasks (project_id, assigned_to, name, start_date, duration, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (project_id, assigned_to, name, start_date, duration, status)
            )
            db.commit()
            flash("Task added successfully!", "success")
            return redirect(url_for('project_detail', project_id=project_id))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    db.close()
    return render_template('add_task.html', project_id=project_id, users=users)


@app.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        try:
            name = request.form['name']
            assigned_to = request.form['assigned_to']
            start_date = request.form['start_date']
            duration = request.form['duration']
            status = request.form['status']
            cursor.execute(
                "UPDATE Tasks SET name=%s, assigned_to=%s, start_date=%s, duration=%s, status=%s WHERE id=%s",
                (name, assigned_to, start_date, duration, status, task_id)
            )
            db.commit()
            flash("Task updated successfully!", "success")
            return redirect(url_for('project_detail', project_id=request.form['project_id']))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    cursor.execute("SELECT * FROM Tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    db.close()
    return render_template('edit_task.html', task=task, users=users)

@app.route('/tasks/delete/<int:task_id>')
def delete_task(task_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT project_id FROM Tasks WHERE id = %s", (task_id,))
        project_id = cursor.fetchone()['project_id']
        cursor.execute("DELETE FROM Tasks WHERE id = %s", (task_id,))
        db.commit()
        flash("Task deleted successfully!", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    db.close()
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/logs', methods=['GET', 'POST'])
def logs():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            task_id = request.form['task_id']
            project_id = request.form['project_id']
            delay_days = request.form['delay_days']
            log_date = request.form['log_date']
            
            cursor.execute(
                "INSERT INTO TaskLogs (task_id, project_id, delay_days, log_date) VALUES (%s, %s, %s, %s)",
                (task_id, project_id, delay_days, log_date)
            )
            db.commit()
            flash("Log added successfully!", "success")
        except Exception as e:
            db.rollback()
            flash(f"Error: {e}", "danger")
    
    try:
        cursor.execute("SELECT * FROM TaskLogs ORDER BY log_date DESC")
        logs = cursor.fetchall()
    except Exception as e:
        logs = []
        flash(f"Error: {e}", "danger")
    db.close()
    return render_template('logs.html', logs=logs)


@app.route('/projects/edit/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            name = request.form['name']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            cursor.execute(
                "UPDATE Projects SET name = %s, start_date = %s, end_date = %s WHERE id = %s",
                (name, start_date, end_date, project_id)
            )
            db.commit()
            flash("Project updated successfully!", "success")
            return redirect(url_for('project_detail', project_id=project_id))
        except Exception as e:
            flash(f"Error: {e}", "danger")

    cursor.execute("SELECT * FROM Projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()
    db.close()
    return render_template('edit_project.html', project=project)



# Çalışan Yönetimi
@app.route('/users', methods=['GET', 'POST'])
def users():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Handle the POST request (adding new user)
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        phone = request.form['phone']
        
        try:
            cursor.execute(
                "INSERT INTO Users (name, surname, email, phone) VALUES (%s, %s, %s, %s)",
                (name, surname, email, phone)
            )
            db.commit()
            flash("User added successfully!", "success")
        except Exception as e:
            db.rollback()
            flash(f"Error: {e}", "danger")
    
    # Handle the GET request (displaying all users)
    try:
        cursor.execute("SELECT * FROM Users ORDER BY name ASC")
        users = cursor.fetchall()
    except Exception as e:
        users = []
        flash(f"Error: {e}", "danger")
    
    db.close()
    return render_template('users.html', users=users)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        try:
            username = request.form['username']
            print(f"Received username: {username}")  # Check if data is being received
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "INSERT INTO Users (username) VALUES (%s)",
                (username,)
            )
            db.commit()
            flash("User added successfully!", "success")
            db.close()
            return redirect(url_for('users'))  # Redirect to the users list
        except Exception as e:
            flash(f"Error: {e}", "danger")
            print(f"Error: {e}")  # Log the error to console for debugging
    return render_template('add_user.html')

@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch the existing user data
    cursor.execute("SELECT * FROM Users WHERE id = %s", (id,))
    user = cursor.fetchone()
    
    if user is None:
        flash("User not found.", "danger")
        return redirect(url_for('users'))

    if request.method == 'POST':
        # Get updated data from the form
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        phone = request.form['phone']

        try:
            cursor.execute("""
                UPDATE Users
                SET name = %s, surname = %s, email = %s, phone = %s
                WHERE id = %s
            """, (name, surname, email, phone, id))
            db.commit()
            flash("User updated successfully!", "success")
            return redirect(url_for('users'))
        except Exception as e:
            db.rollback()
            flash(f"Error: {e}", "danger")
    
    db.close()
    
    # Render the edit user form with the current user data
    return render_template('edit_user.html', user=user)





@app.route('/users/<int:user_id>')
def user_detail(user_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Kullanıcı bilgileri
    cursor.execute("SELECT * FROM Users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    # Kullanıcının görevleri
    cursor.execute("SELECT * FROM Tasks WHERE assigned_to = %s", (user_id,))
    tasks = cursor.fetchall()
    
    completed_on_time = 0
    completed_late = 0
    ongoing = 0
    upcoming = 0
    
    # Görev durumu hesaplamaları
    for task in tasks:
        due_date = datetime.strptime(task['start_date'], '%Y-%m-%d') + timedelta(days=task['duration'])
        if task['status'] == 'Completed':
            if datetime.strptime(task['end_date'], '%Y-%m-%d') <= due_date:
                completed_on_time += 1
            else:
                completed_late += 1
        elif task['status'] == 'In Progress':
            ongoing += 1
        elif task['status'] == 'Not Started':
            upcoming += 1
    
    db.close()
    return render_template(
        'user_detail.html',
        user=user,
        tasks=tasks,
        completed_on_time=completed_on_time,
        completed_late=completed_late,
        ongoing=ongoing,
        upcoming=upcoming
    )

if __name__ == '__main__':
    app.run(debug=True)