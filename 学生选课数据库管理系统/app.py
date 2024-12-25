from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from db_config import db_config

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db_connection():
    return mysql.connector.connect(**db_config)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # 检查用户是否存在并匹配密码
            cursor.execute("SELECT * FROM User WHERE username=%s AND password=%s AND is_admin=%s",
                           (username, password, True if role == 'admin' else False))
            user = cursor.fetchone()
            cursor.close()
            connection.close()

            if user:
                session['username'] = username
                session['role'] = role
                flash('登录成功', 'success')
                return redirect(url_for('main_menu')) if role == 'admin' else redirect(url_for('student_main_menu'))
            else:
                flash('用户名或密码错误', 'danger')
        except mysql.connector.Error as err:
            flash(f'错误: {err}', 'danger')

    return render_template('login.html')


@app.route('/main_menu')
def main_menu():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('main_menu.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('已退出登录', 'info')
    return redirect(url_for('login'))

@app.route('/student_menu')
def student_menu():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('student_menu.html', username=session['username'])

@app.route('/course_menu')
def course_menu():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('course_menu.html', username=session['username'])

@app.route('/enrollment_menu')
def enrollment_menu():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('enrollment_menu.html', username=session['username'])

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        sno = request.form['sno']
        sname = request.form['sname']
        ssex = request.form['ssex']
        sbirthdate = request.form['sbirthdate']
        smajor = request.form['smajor']
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO Student (Sno, Sname, Ssex, Sbirthdate, Smajor) VALUES (%s, %s, %s, %s, %s)",
                           (sno, sname, ssex, sbirthdate, smajor))
            connection.commit()
            flash('学生添加成功', 'success')
        except mysql.connector.Error as err:
            flash(f'添加学生失败: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Student")
    results = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('add_student.html', username=session['username'], results=results)


@app.route('/delete_student', methods=['GET', 'POST'])
def delete_student():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        sno = request.form.get('sno')
        sname = request.form.get('sname')
        ssex = request.form.get('ssex')
        sbirthdate = request.form.get('sbirthdate')
        smajor = request.form.get('smajor')

        conditions = []
        values = []

        if sno:
            conditions.append("Sno = %s")
            values.append(sno)
        if sname:
            conditions.append("Sname = %s")
            values.append(sname)
        if ssex:
            conditions.append("Ssex = %s")
            values.append(ssex)
        if sbirthdate:
            conditions.append("Sbirthdate = %s")
            values.append(sbirthdate)
        if smajor:
            conditions.append("Smajor = %s")
            values.append(smajor)

        if not conditions:
            flash('请至少提供一个字段用于删除学生', 'warning')
            return render_template('delete_student.html', username=session['username'])

        select_query = "SELECT Sno FROM Student WHERE " + " AND ".join(conditions)

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            # 查找符合条件的学生的 Sno
            cursor.execute(select_query, tuple(values))
            snos = cursor.fetchall()

            if not snos:
                flash('没有找到符合条件的学生', 'warning')
                return render_template('delete_student.html', username=session['username'])

            # 删除SC表中对应的记录
            for sno in snos:
                delete_query_sc = "DELETE FROM SC WHERE Sno = %s"
                cursor.execute(delete_query_sc, (sno[0],))

            # 删除Student表中的记录
            delete_query_student = "DELETE FROM Student WHERE " + " AND ".join(conditions)
            cursor.execute(delete_query_student, tuple(values))

            connection.commit()
            flash('学生及相关选课信息删除成功', 'success')

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            flash(f'删除学生失败: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Student")
    results = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('delete_student.html', username=session['username'], results=results)


@app.route('/update_student', methods=['GET', 'POST'])
def update_student():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # 获取查询条件
        sno = request.form.get('sno')
        sname = request.form.get('sname')
        ssex = request.form.get('ssex')
        sbirthdate = request.form.get('sbirthdate')
        smajor = request.form.get('smajor')

        # 获取新值
        new_sno = request.form.get('new_sno')
        new_sname = request.form.get('new_sname')
        new_ssex = request.form.get('new_ssex')
        new_sbirthdate = request.form.get('new_sbirthdate')
        new_smajor = request.form.get('new_smajor')

        conditions = []
        condition_values = []
        updates = []
        update_values = []

        # 添加查询条件
        if sno:
            conditions.append("Sno = %s")
            condition_values.append(sno)
        if sname:
            conditions.append("Sname = %s")
            condition_values.append(sname)
        if ssex:
            conditions.append("Ssex = %s")
            condition_values.append(ssex)
        if sbirthdate:
            conditions.append("Sbirthdate = %s")
            condition_values.append(sbirthdate)
        if smajor:
            conditions.append("Smajor = %s")
            condition_values.append(smajor)

        if not conditions:
            flash('请提供至少一个查询字段用于更新学生信息', 'warning')
            return render_template('update_student.html', username=session['username'])

        # 添加更新值
        if new_sno:
            updates.append("Sno = %s")
            update_values.append(new_sno)
        if new_sname:
            updates.append("Sname = %s")
            update_values.append(new_sname)
        if new_ssex:
            updates.append("Ssex = %s")
            update_values.append(new_ssex)
        if new_sbirthdate:
            updates.append("Sbirthdate = %s")
            update_values.append(new_sbirthdate)
        if new_smajor:
            updates.append("Smajor = %s")
            update_values.append(new_smajor)

        if not updates:
            flash('请提供至少一个新值字段用于更新学生信息', 'warning')
            return render_template('update_student.html', username=session['username'])

        update_query = "UPDATE Student SET " + ", ".join(updates) + " WHERE " + " AND ".join(conditions)

        # 调试信息
        print(f"Update Query: {update_query}")
        print(f"Values: {update_values + condition_values}")

        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(update_query, tuple(update_values + condition_values))
            if cursor.rowcount == 0:
                flash('没有找到符合条件的学生或未进行任何更改', 'warning')
            else:
                connection.commit()
                flash('学生信息更新成功', 'success')
        except mysql.connector.Error as err:
            flash(f'更新学生信息失败: {err}', 'danger')
        cursor.close()
        connection.close()

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Student")
    results = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('update_student.html', username=session['username'], results=results)


@app.route('/query_students', methods=['GET', 'POST'])
def query_students():
    if 'username' not in session:
        return redirect(url_for('login'))
    results = []
    if request.method == 'POST':
        sno = request.form['sno']
        sname = request.form['sname']
        ssex = request.form['ssex']
        sbirthdate = request.form['sbirthdate']
        smajor = request.form['smajor']

        query = "SELECT * FROM Student WHERE 1=1"
        params = []

        if sno:
            query += " AND Sno = %s"
            params.append(sno)
        if sname:
            query += " AND Sname = %s"
            params.append(sname)
        if ssex:
            query += " AND Ssex = %s"
            params.append(ssex)
        if sbirthdate:
            query += " AND Sbirthdate = %s"
            params.append(sbirthdate)
        if smajor:
            query += " AND Smajor = %s"
            params.append(smajor)

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        connection.close()
    return render_template('query_students.html', results=results, username=session['username'])

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if 'username' not in session:
        return redirect(url_for('login'))
    results = []
    if request.method == 'POST':
        cno = request.form['cno']
        cname = request.form['cname']
        credit = request.form['credit']
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO Course (Cno, Cname, Credit) VALUES (%s, %s, %s)",
                           (cno, cname, credit))
            connection.commit()
            flash('课程添加成功', 'success')
        except mysql.connector.Error as err:
            flash(f'添加课程失败: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Course")
    results = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('add_course.html', username=session['username'], results=results)

@app.route('/delete_course', methods=['GET', 'POST'])
def delete_course():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        cno = request.form.get('cno')
        cname = request.form.get('cname')
        credit = request.form.get('credit')
        cpno = request.form.get('cpno')

        conditions = []
        values = []

        if cno:
            conditions.append("Cno = %s")
            values.append(cno)
        if cname:
            conditions.append("Cname = %s")
            values.append(cname)
        if credit:
            conditions.append("Credit = %s")
            values.append(credit)
        if cpno:
            conditions.append("Cpno = %s")
            values.append(cpno)

        if not conditions:
            flash('请至少提供一个字段用于删除课程', 'warning')
            return render_template('delete_course.html', username=session['username'])

        select_query = "SELECT Cno FROM Course WHERE " + " AND ".join(conditions)

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            # 查找符合条件的课程的 Cno
            cursor.execute(select_query, tuple(values))
            cnos = cursor.fetchall()

            if not cnos:
                flash('没有找到符合条件的课程', 'warning')
                return render_template('delete_course.html', username=session['username'])

            # 删除SC表中对应的记录
            for cno in cnos:
                delete_query_sc = "DELETE FROM SC WHERE Cno = %s"
                cursor.execute(delete_query_sc, (cno[0],))

            # 删除Course表中的记录
            delete_query_course = "DELETE FROM Course WHERE " + " AND ".join(conditions)
            cursor.execute(delete_query_course, tuple(values))

            connection.commit()
            flash('课程及相关选课信息删除成功', 'success')

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            flash(f'删除课程失败: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Course")
    results = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('delete_course.html', username=session['username'], results=results)

@app.route('/update_course', methods=['GET', 'POST'])
def update_course():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        cno = request.form.get('cno')
        cname = request.form.get('cname')
        credit = request.form.get('ccredit')
        cpno = request.form.get('cpno')

        new_cno = request.form.get('new_cno')
        new_cname = request.form.get('new_cname')
        new_credit = request.form.get('new_ccredit')
        new_cpno = request.form.get('new_cpno')

        conditions = []
        condition_values = []
        updates = []
        update_values = []

        if cno:
            conditions.append("Cno = %s")
            condition_values.append(cno)
        if cname:
            conditions.append("Cname = %s")
            condition_values.append(cname)
        if credit:
            conditions.append("Ccredit = %s")
            condition_values.append(credit)
        if cpno:
            conditions.append("Cpno = %s")
            condition_values.append(cpno)

        if not conditions:
            flash('请提供至少一个查询字段用于更新课程信息', 'warning')
            return render_template('update_course.html', username=session['username'])

        if new_cno:
            updates.append("Cno = %s")
            update_values.append(new_cno)
        if new_cname:
            updates.append("Cname = %s")
            update_values.append(new_cname)
        if new_credit:
            updates.append("Ccredit = %s")
            update_values.append(new_credit)
        if new_cpno:
            updates.append("Cpno = %s")
            update_values.append(new_cpno)

        if not updates:
            flash('请提供至少一个新值字段用于更新课程信息', 'warning')
            return render_template('update_course.html', username=session['username'])

        update_query = "UPDATE Course SET " + ", ".join(updates) + " WHERE " + " AND ".join(conditions)

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(update_query, tuple(update_values + condition_values))
            if cursor.rowcount == 0:
                flash('没有找到符合条件的课程或未进行任何更改', 'warning')
            else:
                connection.commit()
                flash('课程信息更新成功', 'success')
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            flash(f'更新课程信息失败: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Course")
    results = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('update_course.html', username=session['username'], results=results)

@app.route('/query_courses', methods=['GET', 'POST'])
def query_courses():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    results = []
    if request.method == 'POST':
        cno = request.form['cno']
        cname = request.form['cname']
        credit = request.form['credit']
        cpno = request.form['cpno']

        query = "SELECT * FROM Course WHERE 1=1"
        params = []

        if cno:
            query += " AND Cno = %s"
            params.append(cno)
        if cname:
            query += " AND Cname = %s"
            params.append(cname)
        if credit:
            query += " AND Ccredit = %s"
            params.append(credit)
        if cpno:
            query += " AND Cpno = %s"
            params.append(cpno)

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        connection.close()

    return render_template('query_courses.html', results=results, username=session['username'])
@app.route('/add_enrollment', methods=['GET', 'POST'])
def add_enrollment():
    if 'username' not in session:
        return redirect(url_for('login'))
    results = []
    if request.method == 'POST':
        sno = request.form['sno']
        cno = request.form['cno']
        grade = request.form['grade']
        semester = request.form['semester']
        teachingclass = request.form['teachingclass']
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO SC (Sno, Cno, Grade, Semester, Teachingclass) VALUES (%s, %s, %s, %s, %s)",
                           (sno, cno, grade, semester, teachingclass))
            connection.commit()
            flash('选课添加成功', 'success')
        except mysql.connector.Error as err:
            flash(f'添加选课失败: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM SC")
    results = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('add_enrollment.html', username=session['username'], results=results)

@app.route('/delete_enrollment', methods=['GET', 'POST'])
def delete_enrollment():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        sno = request.form['sno']
        cno = request.form['cno']
        grade = request.form['grade']
        semester = request.form['semester']
        teachingclass = request.form['teachingclass']

        conditions = []
        values = []
        if sno:
            conditions.append("Sno = %s")
            values.append(sno)
        if cno:
            conditions.append("Cno = %s")
            values.append(cno)
        if grade:
            conditions.append("Grade = %s")
            values.append(grade)
        if semester:
            conditions.append("Semester = %s")
            values.append(semester)
        if teachingclass:
            conditions.append("Teachingclass = %s")
            values.append(teachingclass)

        if not conditions:
            flash('请至少提供一个字段用于删除选课信息', 'warning')
            return render_template('delete_enrollment.html', username=session['username'])

        query = "DELETE FROM SC WHERE " + " AND ".join(conditions)
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(query, tuple(values))
            if cursor.rowcount == 0:
                flash('未找到选课信息或已删除', 'warning')
            else:
                connection.commit()
                flash(f'成功删除{cursor.rowcount}条选课信息', 'success')
        except mysql.connector.Error as err:
            flash(f'删除选课信息失败: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM SC")
    results = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('delete_enrollment.html', username=session['username'], results=results)

@app.route('/update_enrollment', methods=['GET', 'POST'])
def update_enrollment():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        sno = request.form['sno']
        cno = request.form['cno']
        grade = request.form['grade']
        semester = request.form['semester']
        teachingclass = request.form['teachingclass']

        new_sno = request.form['new_sno']
        new_cno = request.form['new_cno']
        new_grade = request.form['new_grade']
        new_semester = request.form['new_semester']
        new_teachingclass = request.form['new_teachingclass']

        conditions = []
        updates = []
        values = []
        if sno:
            conditions.append("Sno = %s")
            values.append(sno)
        if cno:
            conditions.append("Cno = %s")
            values.append(cno)
        if grade:
            conditions.append("Grade = %s")
            values.append(grade)
        if semester:
            conditions.append("Semester = %s")
            values.append(semester)
        if teachingclass:
            conditions.append("Teachingclass = %s")
            values.append(teachingclass)

        if not conditions:
            flash('请提供至少一个查询字段用于更新选课信息', 'warning')
            return render_template('update_enrollment.html', username=session['username'])

        if new_sno:
            updates.append("Sno = %s")
            values.append(new_sno)
        if new_cno:
            updates.append("Cno = %s")
            values.append(new_cno)
        if new_grade:
            updates.append("Grade = %s")
            values.append(new_grade)
        if new_semester:
            updates.append("Semester = %s")
            values.append(new_semester)
        if new_teachingclass:
            updates.append("Teachingclass = %s")
            values.append(new_teachingclass)

        if not updates:
            flash('请提供至少一个新值字段用于更新选课信息', 'warning')
            return render_template('update_enrollment.html', username=session['username'])

        update_query = "UPDATE SC SET " + ", ".join(updates) + " WHERE " + " AND ".join(conditions)
        values += values[:len(conditions)]

        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(update_query, tuple(values))
            if cursor.rowcount == 0:
                flash('没有找到符合条件的选课信息或未进行任何更改', 'warning')
            else:
                connection.commit()
                flash('选课信息更新成功', 'success')
        except mysql.connector.Error as err:
            flash(f'更新选课信息失败: {err}', 'danger')
        cursor.close()
        connection.close()

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM SC")
    results = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('update_enrollment.html', username=session['username'], results=results)

@app.route('/query_enrollments', methods=['GET', 'POST'])
def query_enrollments():
    if 'username' not in session:
        return redirect(url_for('login'))
    results = []
    if request.method == 'POST':
        sno = request.form['sno']
        cno = request.form['cno']
        grade = request.form['grade']
        semester = request.form['semester']
        teachingclass = request.form['teachingclass']

        query = "SELECT * FROM SC WHERE 1=1"
        params = []

        if sno:
            query += " AND Sno = %s"
            params.append(sno)
        if cno:
            query += " AND Cno = %s"
            params.append(cno)
        if grade:
            query += " AND Grade = %s"
            params.append(grade)
        if semester:
            query += " AND Semester = %s"
            params.append(semester)
        if teachingclass:
            query += " AND Teachingclass = %s"
            params.append(teachingclass)

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        connection.close()
    return render_template('query_enrollments.html', results=results, username=session['username'])


@app.route('/student_main_menu')
def student_main_menu():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    return render_template('student_main_menu.html', username=session['username'])


@app.route('/student_profile')
def student_profile():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Student WHERE Sno=%s", (session['username'],))
    student_info = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('student_profile.html', student_info=student_info)


@app.route('/update_student_info', methods=['GET', 'POST'])
def update_student_info():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        sname = request.form['sname']
        ssex = request.form['ssex']
        sbirthdate = request.form['sbirthdate']
        smajor = request.form['smajor']

        update_query = "UPDATE Student SET Sname=%s, Ssex=%s, Sbirthdate=%s, Smajor=%s WHERE Sno=%s"
        cursor.execute(update_query, (sname, ssex, sbirthdate, smajor, session['username']))
        connection.commit()
        flash('个人信息更新成功', 'success')

    cursor.execute("SELECT * FROM Student WHERE Sno=%s", (session['username'],))
    student_info = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('update_student_info.html', student_info=student_info)


@app.route('/student_courses')
def student_courses():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT SC.Cno, Course.Cname, Course.Ccredit, SC.Semester, SC.Teachingclass
    FROM SC
    JOIN Course ON SC.Cno = Course.Cno
    WHERE SC.Sno = %s
    """
    cursor.execute(query, (session['username'],))
    enrollments = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('student_courses.html', enrollments=enrollments)


@app.route('/student/query_courses', methods=['GET', 'POST'])
def query_k():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    results = []
    if request.method == 'POST':
        cno = request.form['cno']
        cname = request.form['cname']
        credit = request.form['credit']
        cpno = request.form['cpno']

        query = "SELECT * FROM Course WHERE 1=1"
        params = []

        if cno:
            query += " AND Cno = %s"
            params.append(cno)
        if cname:
            query += " AND Cname = %s"
            params.append(cname)
        if credit:
            query += " AND Ccredit = %s"
            params.append(credit)
        if cpno:
            query += " AND Cpno = %s"
            params.append(cpno)

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        connection.close()

    return render_template('query_k.html', results=results, username=session['username'])


@app.route('/student/apply_course', methods=['GET', 'POST'])
def apply_course():
    if 'username' not in session or session['role'] != 'student':
        return redirect(url_for('login'))

    if request.method == 'POST':
        sno = session['username']
        cno = request.form['cno']
        semester = request.form['semester']
        teachingclass = request.form['teachingclass']
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO SQSC (Sno, Cno, Grade, Semester, Teachingclass) VALUES (%s, %s, NULL, %s, %s)",
                           (sno, cno, semester, teachingclass))
            connection.commit()
            flash('选课申请已提交', 'success')
        except mysql.connector.Error as err:
            flash(f'提交选课申请失败: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for('apply_course'))

    # 查询已提交的选课信息
    sno = session['username']
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM SQSC WHERE Sno = %s", (sno,))
    applications = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('apply_course.html', applications=applications, username=session['username'])


@app.route('/process_applications', methods=['GET', 'POST'])
def process_applications():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        selected_applications = request.form.getlist('applications')

        if selected_applications:
            for application in selected_applications:
                sno, cno = application.split(',')
                cursor.execute("SELECT * FROM SQSC WHERE Sno = %s AND Cno = %s", (sno, cno))
                application = cursor.fetchone()
                if application:
                    grade = application['Grade']
                    semester = application['Semester']
                    teachingclass = application['Teachingclass']
                    # 检查是否已经存在相同的记录
                    cursor.execute("SELECT * FROM SC WHERE Sno = %s AND Cno = %s", (sno, cno))
                    if cursor.fetchone() is None:
                        cursor.execute(
                            "INSERT INTO SC (Sno, Cno, Grade, Semester, Teachingclass) VALUES (%s, %s, %s, %s, %s)",
                            (sno, cno, grade, semester, teachingclass)
                        )
                    cursor.execute("DELETE FROM SQSC WHERE Sno = %s AND Cno = %s", (sno, cno))
            connection.commit()
            flash('选课申请处理成功', 'success')
        else:
            flash('请勾选需要处理的申请', 'warning')

    cursor.execute("SELECT * FROM SQSC")
    applications = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('process_applications.html', applications=applications, username=session['username'])

@app.route('/query_course_students', methods=['GET', 'POST'])
def query_course_students():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    results = []
    if request.method == 'POST':
        cno = request.form['cno']
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT Student.Sno, Student.Sname, Student.Ssex, Student.Sbirthdate, Student.Smajor
            FROM SC
            JOIN Student ON SC.Sno = Student.Sno
            WHERE SC.Cno = %s
        """, (cno,))
        results = cursor.fetchall()
        cursor.close()
        connection.close()
    return render_template('query_course_students.html', results=results, username=session['username'])

@app.route('/query_pass_fail_students', methods=['GET', 'POST'])
def query_pass_fail_students():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    pass_results = []
    fail_results = []
    if request.method == 'POST':
        cno = request.form['cno']
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT SC.Sno, Student.Sname, SC.Cno, SC.Grade
            FROM SC
            JOIN Student ON SC.Sno = Student.Sno
            WHERE SC.Cno = %s AND SC.Grade IS NOT NULL
        """, (cno,))
        results = cursor.fetchall()
        for result in results:
            if result['Grade'] >= 60:
                pass_results.append(result)
            else:
                fail_results.append(result)
        cursor.close()
        connection.close()
    return render_template('query_pass_fail_students.html', pass_results=pass_results, fail_results=fail_results, username=session['username'])

@app.route('/query_missing_prerequisites')
def query_missing_prerequisites():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    results = []
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT SC.Sno, Student.Sname, SC.Cno, SC.Semester, SC.Teachingclass
        FROM SC
        JOIN Student ON SC.Sno = Student.Sno
        JOIN Course ON SC.Cno = Course.Cno
        WHERE Course.Cpno IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM SC AS SC2
              WHERE SC2.Sno = SC.Sno AND SC2.Cno = Course.Cpno
          )
    """)
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('query_missing_prerequisites.html', results=results, username=session['username'])

@app.route('/query_course_range', methods=['GET', 'POST'])
def query_course_range():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    results = []
    if request.method == 'POST':
        n = request.form['n']
        m = request.form['m']
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT Student.Sno, Student.Sname, COUNT(SC.Cno) AS CourseCount
            FROM SC
            JOIN Student ON SC.Sno = Student.Sno
            GROUP BY SC.Sno, Student.Sname
            HAVING COUNT(SC.Cno) BETWEEN %s AND %s
        """, (n, m))
        results = cursor.fetchall()
        cursor.close()
        connection.close()
    return render_template('query_course_range.html', results=results, username=session['username'])

@app.route('/query_major_courses', methods=['GET', 'POST'])
def query_major_courses():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    results = []
    if request.method == 'POST':
        major = request.form['major']
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT SC.Sno, Student.Sname, SC.Cno, SC.Grade, SC.Semester, SC.Teachingclass
            FROM SC
            JOIN Student ON SC.Sno = Student.Sno
            WHERE Student.Smajor = %s
        """, (major,))
        results = cursor.fetchall()
        print(results)
        cursor.close()
        connection.close()
    return render_template('query_major_courses.html', results=results, username=session['username'])

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        username = request.form['username']
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM User WHERE username=%s AND password=%s", (username, old_password))
            user = cursor.fetchone()

            if user:
                cursor.execute("UPDATE User SET password=%s WHERE username=%s", (new_password, username))
                connection.commit()
                flash('密码修改成功', 'success')
                return redirect(url_for('login'))
            else:
                flash('用户名或旧密码错误', 'danger')
        except mysql.connector.Error as err:
            flash(f'错误: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()

    return render_template('change_password.html')


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        username = request.form['username']
        try:
            cursor.execute("UPDATE User SET password = %s WHERE username = %s", (username, username))
            connection.commit()
            flash('密码重置成功', 'success')
        except mysql.connector.Error as err:
            flash(f'错误: {err}', 'danger')

    cursor.execute("SELECT * FROM User")
    user_records = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('reset_password.html', user_records=user_records, username=session['username'])


if __name__ == '__main__':
    app.run(debug=True)
