from flask import Flask, render_template, request, redirect, url_for, flash
from db import get_db_connection
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "your_secret_key"

#Anasayfa
@app.route('/')
def index():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Projeleri al
    cursor.execute("SELECT * FROM Projects")
    projects = cursor.fetchall()

     # Kullanıcıları al
    cursor.execute("SELECT id, CONCAT(name, ' ', surname) AS username FROM Users")
    users = cursor.fetchall()

    # Görevleri al
    cursor.execute("SELECT * FROM Tasks")
    tasks = cursor.fetchall()

    # Logları al
    cursor.execute("SELECT * FROM TaskLogs")
    logs = cursor.fetchall()

    db.close()
    return render_template('index.html', projects=projects, tasks=tasks, logs=logs, users=users)


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
            # Hata türünü kontrol ederek kullanıcı dostu bir mesaj oluştur
            if "Incorrect date value" in str(e):
                flash("Invalid date format. Please make sure the dates are in the correct format (YYYY-MM-DD).", "danger")
            else:
                flash("There was an error adding the project. Please check your information and try again.", "danger")
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
    db.close()
    return render_template('project_detail.html', project=project, tasks=tasks)

@app.route('/projects/delete/<int:project_id>')
def delete_project(project_id):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM Tasks WHERE project_id = %s", (project_id,))
        cursor.execute("DELETE FROM Projects WHERE id = %s", (project_id,))
        db.commit()
        flash("Project and its tasks deleted successfully!", "success")
    except Exception as e:
        flash(f"An error occurred while deleting the project: {e}", "danger")
    db.close()
    return redirect(url_for('projects'))

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
            flash(f"An error occurred while updating the project: {e}", "danger")
    cursor.execute("SELECT * FROM Projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()
    db.close()
    return render_template('edit_project.html', project=project)

@app.route('/projects/update/<int:project_id>', methods=['POST'])
def update_project_status(project_id):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        status = request.form['status']
        cursor.execute(
            "UPDATE Projects SET status = %s WHERE id = %s",
            (status, project_id)
        )
        db.commit()
        flash("Project status updated successfully!", "success")
    except Exception as e:
        db.rollback()
        flash(f"An error occurred while updating the project status: {e}", "danger")
    db.close()
    return redirect(url_for('projects'))

# Görev Yönetimi
@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        # Formdan gelen verilerle yeni bir görev ekle
        project_id = request.form['project_id']
        assigned_to = request.form.get('assigned_to')  # Boş olabilir
        name = request.form['name']
        start_date = request.form['start_date']
        duration = request.form['duration']

        # Görev ekleme sorgusu
        cursor.execute("""
            INSERT INTO Tasks (project_id, assigned_to, name, start_date, duration, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (project_id, assigned_to, name, start_date, duration, 'Pending'))
        db.commit()

    # Tüm görevleri çek
    cursor.execute("""
        SELECT id, project_id, assigned_to, name, start_date, duration, 
               DATE_ADD(start_date, INTERVAL duration DAY) AS end_date, status
        FROM Tasks
    """)
    tasks = cursor.fetchall()
    db.close()

    return render_template('tasks.html', tasks=tasks)

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
            status = request.form['status']

            # Status değerinin geçerli olduğundan emin olun
            valid_statuses = ['Tamamlanacak', 'Devam Ediyor', 'Tamamlandı']
            if status not in valid_statuses:
                flash("Invalid status value. Please choose a valid status.", "danger")
                return redirect(url_for('add_task', project_id=project_id))

            cursor.execute(
                "INSERT INTO Tasks (project_id, assigned_to, name, start_date, duration, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (project_id, assigned_to, name, start_date, duration, status)
            )
            db.commit()
            flash("Task added successfully!", "success")
            return redirect(url_for('project_detail', project_id=project_id))
        except Exception as e:
            flash(f"An error occurred while adding the task: {e}", "danger")
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
            # Gelen POST verilerini kontrol edin
            print(request.form)  # Gelen verileri terminalde görebilirsiniz

            name = request.form['name']
            start_date = request.form['start_date']
            duration = request.form['duration']
            status = request.form['status']

            # Sadece start_date ve duration'ı güncelleyin, end_date otomatik hesaplanacaktır.
            cursor.execute(
                "UPDATE Tasks SET name=%s, start_date=%s, duration=%s, status=%s WHERE id=%s",
                (name, start_date, duration, status, task_id)
            )
            db.commit()
            flash("Task updated successfully!", "success")
            return redirect(url_for('project_detail', project_id=request.form['project_id']))
        except Exception as e:
            print(e)  # Tam hata mesajını konsola yazdırın
            flash(f"An error occurred while updating the task: {e}", "danger")

    # Task ve Kullanıcıları Veritabanından Çekme
    cursor.execute("SELECT * FROM Tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    db.close()

    return render_template('task_edit.html', task=task)


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
        flash(f"An error occurred while deleting the task: {e}", "danger")
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
            
            cursor.execute(
                "INSERT INTO TaskLogs (task_id, project_id, delay_days) VALUES (%s, %s, %s)",
                (task_id, project_id, delay_days)
            )
            db.commit()
            flash("Log added successfully!", "success")
        except Exception as e:
            db.rollback()
            flash(f"An error occurred while adding the log: {e}", "danger")
    
    try:
        cursor.execute("SELECT * FROM TaskLogs ORDER BY log_date DESC")
        logs = cursor.fetchall()
    except Exception as e:
        logs = []
        flash(f"An error occurred while fetching the logs: {e}", "danger")
    db.close()
    return render_template('logs.html', logs=logs)

@app.route('/logs/delete/<int:log_id>', methods=['GET', 'POST'])
def delete_log(log_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM TaskLogs WHERE id = %s", (log_id,))
        db.commit()
        flash("Log deleted successfully!", "success")
    except Exception as e:
        db.rollback()
        flash(f"An error occurred while deleting the log: {e}", "danger")
    finally:
        db.close()
    return redirect(url_for('logs'))

# Çalışan Yönetimi
@app.route('/users', methods=['GET', 'POST'])
def users():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        
        try:
            cursor.execute(
                "INSERT INTO Users (name, surname, email) VALUES (%s, %s, %s)",
                (name, surname, email)
            )
            db.commit()
            flash("User added successfully!", "success")
        except Exception as e:
            db.rollback()
            flash(f"An error occurred while adding the user: {e}", "danger")
    
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    db.close()
    return render_template('users.html', users=users)

@app.route('/users/delete/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    db = get_db_connection()
    cursor = db.cursor()
    
    # Kullanıcıyı silmek için SQL sorgusu
    cursor.execute("DELETE FROM Users WHERE id = %s", (user_id,))
    db.commit()
    db.close()
    
    return redirect(url_for('users'))

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        # Formdan gelen verileri al
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        phone = request.form['phone']

        try:
            # Kullanıcı bilgilerini güncelle
            cursor.execute("""
                UPDATE Users
                SET name = %s, surname = %s, email = %s, phone = %s
                WHERE id = %s
            """, (name, surname, email, phone, user_id))
            db.commit()
            flash("Kullanıcı bilgileri başarıyla güncellendi.", "success")
        except Exception as e:
            db.rollback()
            flash(f"Hata: Kullanıcı bilgileri güncellenemedi. {e}", "danger")
        finally:
            db.close()

        # Başarılı bir güncellemeden sonra kullanıcı listesine yönlendir
        return redirect(url_for('users'))

    else:
        # Kullanıcı bilgilerini çek
        cursor.execute("SELECT * FROM Users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        db.close()

        if not user:
            flash("Kullanıcı bulunamadı.", "warning")
            return redirect(url_for('users'))

        # Kullanıcı bilgilerini düzenleme sayfasını göster
        return render_template('edit_user.html', user=user)


@app.route('/users/<int:user_id>')
def user_details(user_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Kullanıcı bilgilerini çek
    cursor.execute("SELECT * FROM Users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    # Kullanıcının projelerini çek
    # Kullanıcının projelerini çek
    cursor.execute("""
        SELECT id AS project_id, name AS project_name, status AS project_status
        FROM Projects
        WHERE id = %s
    """, (user_id,))
    projects = cursor.fetchall()

    
    # Kullanıcının görevlerini çek
    cursor.execute("""
        SELECT id AS task_id, name AS task_name, status AS task_status
        FROM Tasks t
        WHERE t.id = %s
    """, (user_id,))
    tasks = cursor.fetchall()
    
    db.close()
    
    return render_template('user_details.html', user=user, projects=projects, tasks=tasks)


    db.close()

    return render_template('edit_user.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)